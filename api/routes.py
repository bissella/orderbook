from flask import Blueprint, request, jsonify, g
from flask_restful import Api, Resource
from database import SessionLocal
from database.order_book import OrderBook
from models import Customer, Commodity, Order, OrderType, OrderStatus, Trade
from api.validators import CommodityCreate, OrderCreate
import uuid
import functools
import logging

# Create Blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)


# Authentication middleware
def authenticate(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            return {"error": "API Key required"}, 401
            
        db = SessionLocal()
        customer = db.query(Customer).filter(Customer.api_key == api_key).first()
        
        if not customer:
            db.close()
            return {"error": "Invalid API Key"}, 401
            
        g.customer = customer
        g.db = db
        
        try:
            return f(*args, **kwargs)
        finally:
            db.close()
            
    return decorated


# Login resource
class LoginResource(Resource):
    def post(self):
        """Login with username and password."""
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return {"error": "Email and password required"}, 400
            
        db = SessionLocal()
        try:
            customer = db.query(Customer).filter(Customer.email == email).first()
            
            if not customer or not customer.check_password(password):
                return {"error": "Invalid email or password"}, 401
                
            return {
                "customer": customer.to_dict(),
                "api_key": customer.api_key
            }, 200
        finally:
            db.close()


# Customer resources
class CustomerResource(Resource):
    def post(self):
        """Create a new customer."""
        data = request.get_json()
        
        # Check if password is provided
        if 'password' not in data:
            return {"error": "Password required"}, 400
            
        # Generate API key
        api_key = str(uuid.uuid4())
        
        # Create customer
        db = SessionLocal()
        try:
            customer = Customer(
                name=data.get('name'),
                email=data.get('email'),
                api_key=api_key
            )
            customer.set_password(data.get('password'))
            db.add(customer)
            db.commit()
            db.refresh(customer)
            
            result = customer.to_dict()
            result["api_key"] = api_key  # Include API key in response
            
            return result, 201
        except Exception as e:
            db.rollback()
            logging.error("Registration error: %s", str(e))
            return {"error": f"Registration failed: {str(e)}"}, 400
        finally:
            db.close()
    
    @authenticate
    def get(self):
        """Get current customer information."""
        return g.customer.to_dict(), 200


# Commodity resources
class CommodityListResource(Resource):
    @authenticate
    def get(self):
        """Get all commodities."""
        commodities = g.db.query(Commodity).all()
        return [c.to_dict() for c in commodities], 200
    
    @authenticate
    def post(self):
        """Create a new commodity."""
        data = request.get_json()
        commodity_data = CommodityCreate(**data)
        
        # Create commodity
        commodity = Commodity(
            name=commodity_data.name,
            symbol=commodity_data.symbol,
            description=commodity_data.description
        )
        g.db.add(commodity)
        g.db.commit()
        g.db.refresh(commodity)
        
        return commodity.to_dict(), 201


class CommodityResource(Resource):
    @authenticate
    def get(self, commodity_id):
        """Get a specific commodity."""
        commodity = g.db.query(Commodity).filter(Commodity.id == commodity_id).first()
        
        if not commodity:
            return {"error": f"Commodity with ID {commodity_id} not found"}, 404
            
        return commodity.to_dict(), 200


# Order Book resources
class OrderBookResource(Resource):
    @authenticate
    def get(self, commodity_id):
        """Get order book for a specific commodity."""
        order_book = OrderBook(g.db)
        book_snapshot = order_book.get_order_book_snapshot(commodity_id)
        return book_snapshot, 200


# Order resources
class OrderListResource(Resource):
    @authenticate
    def get(self):
        """Get all orders for the current customer."""
        orders = g.db.query(Order).filter(Order.customer_id == g.customer.id).all()
        return [o.to_dict() for o in orders], 200
    
    @authenticate
    def post(self):
        """Create a new order."""
        data = request.get_json()
        # Override customer_id with authenticated customer
        data["customer_id"] = g.customer.id
        order_data = OrderCreate(**data)
        
        # Create order
        order = Order(
            customer_id=order_data.customer_id,
            commodity_id=order_data.commodity_id,
            order_type=OrderType(order_data.order_type),
            price=order_data.price,
            quantity=order_data.quantity,
            filled_quantity=0.0,
            status=OrderStatus.OPEN
        )
        
        # Add to order book
        order_book = OrderBook(g.db)
        order, trades = order_book.add_order(order)
        
        # Return response with order and any executed trades
        result = {
            "order": order.to_dict(),
            "trades": [t.to_dict() for t in trades]
        }
        
        return result, 201


class OrderResource(Resource):
    @authenticate
    def get(self, order_id):
        """Get a specific order."""
        order = g.db.query(Order).filter(
            Order.id == order_id,
            Order.customer_id == g.customer.id
        ).first()
        
        if not order:
            return {"error": f"Order with ID {order_id} not found"}, 404
            
        return order.to_dict(), 200
    
    @authenticate
    def delete(self, order_id):
        """Cancel an order."""
        order = g.db.query(Order).filter(
            Order.id == order_id,
            Order.customer_id == g.customer.id
        ).first()
        
        if not order:
            return {"error": f"Order with ID {order_id} not found"}, 404
            
        # Cancel order
        order_book = OrderBook(g.db)
        try:
            order = order_book.cancel_order(order_id)
            return order.to_dict(), 200
        except ValueError as e:
            logging.error("Order cancellation error: %s", str(e))
            return {"error": str(e)}, 400


# Trade resources
class TradeListResource(Resource):
    @authenticate
    def get(self):
        """Get all trades for the current customer."""
        # Get all orders for this customer
        customer_orders = g.db.query(Order.id).filter(Order.customer_id == g.customer.id).all()
        customer_order_ids = [o[0] for o in customer_orders]
        
        # Get all trades involving these orders
        trades = g.db.query(Trade).filter(
            (Trade.order_id.in_(customer_order_ids)) | 
            (Trade.counterparty_order_id.in_(customer_order_ids))
        ).all()
        
        return [t.to_dict() for t in trades], 200


# Add resources to API
api.add_resource(LoginResource, "/login")
api.add_resource(CustomerResource, "/customers")
api.add_resource(CommodityListResource, "/commodities")
api.add_resource(CommodityResource, "/commodities/<int:commodity_id>")
api.add_resource(OrderBookResource, "/orderbook/<int:commodity_id>")
api.add_resource(OrderListResource, "/orders")
api.add_resource(OrderResource, "/orders/<int:order_id>")
api.add_resource(TradeListResource, "/trades")
