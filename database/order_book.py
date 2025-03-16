from sqlalchemy.orm import Session
from models import Order, OrderType, OrderStatus, Trade
from typing import List, Dict, Tuple


class OrderBook:
    """OrderBook implementation for handling order matching and execution."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_order(self, order: Order) -> Tuple[Order, List[Trade]]:
        """Add a new order to the order book and try to match it with existing orders."""
        # Save the order to DB first
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        # Try to match the order
        trades = self.match_order(order)
        
        # Update order status based on matches
        if trades:
            if order.filled_quantity >= order.quantity:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIAL
        
        self.db.commit()
        self.db.refresh(order)
        
        return order, trades
    
    def match_order(self, order: Order) -> List[Trade]:
        """Match an order with existing orders in the book."""
        trades = []
        
        # Determine which orders to match against based on order type
        opposite_type = OrderType.SELL if order.order_type == OrderType.BUY else OrderType.BUY
        
        # Query for matching orders
        # For buy orders, we want to match with sell orders with price <= buy price (sorted by lowest price first)
        # For sell orders, we want to match with buy orders with price >= sell price (sorted by highest price first)
        if order.order_type == OrderType.BUY:
            matching_orders = (
                self.db.query(Order)
                .filter(
                    Order.commodity_id == order.commodity_id,
                    Order.order_type == opposite_type,
                    Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIAL]),
                    Order.price <= order.price
                )
                .order_by(Order.price, Order.created_at)
                .all()
            )
        else:  # SELL order
            matching_orders = (
                self.db.query(Order)
                .filter(
                    Order.commodity_id == order.commodity_id,
                    Order.order_type == opposite_type,
                    Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIAL]),
                    Order.price >= order.price
                )
                .order_by(Order.price.desc(), Order.created_at)
                .all()
            )
        
        # Match with orders until our order is filled or no more matches
        remaining_quantity = order.quantity
        
        for matching_order in matching_orders:
            if remaining_quantity <= 0:
                break
                
            # Calculate the matched quantity
            match_quantity = min(
                remaining_quantity,
                matching_order.quantity - matching_order.filled_quantity
            )
            
            if match_quantity <= 0:
                continue
                
            # Create a trade
            # Use the price of the existing order in the book (price-time priority)
            trade = Trade(
                order_id=order.id,
                counterparty_order_id=matching_order.id,
                price=matching_order.price,
                quantity=match_quantity
            )
            
            # Update the filled quantities
            order.filled_quantity += match_quantity
            matching_order.filled_quantity += match_quantity
            
            # Update the matching order status
            if matching_order.filled_quantity >= matching_order.quantity:
                matching_order.status = OrderStatus.FILLED
            else:
                matching_order.status = OrderStatus.PARTIAL
            
            # Save the trade
            self.db.add(trade)
            trades.append(trade)
            
            # Update remaining quantity
            remaining_quantity -= match_quantity
        
        # Commit all changes
        self.db.commit()
        
        return trades
    
    def cancel_order(self, order_id: int) -> Order:
        """Cancel an order if it's still open or partially filled."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise ValueError(f"Order with ID {order_id} not found")
            
        if order.status in [OrderStatus.OPEN, OrderStatus.PARTIAL]:
            order.status = OrderStatus.CANCELLED
            self.db.commit()
            self.db.refresh(order)
            
        return order
    
    def get_order_book_snapshot(self, commodity_id: int) -> Dict:
        """Get a snapshot of the current order book for a specific commodity."""
        # Get all open buy orders
        buy_orders = (
            self.db.query(Order)
            .filter(
                Order.commodity_id == commodity_id,
                Order.order_type == OrderType.BUY,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIAL])
            )
            .order_by(Order.price.desc())
            .all()
        )
        
        # Get all open sell orders
        sell_orders = (
            self.db.query(Order)
            .filter(
                Order.commodity_id == commodity_id,
                Order.order_type == OrderType.SELL,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIAL])
            )
            .order_by(Order.price)
            .all()
        )
        
        # Aggregate orders by price level
        bids = {}  # Buy side
        for order in buy_orders:
            price = order.price
            quantity = order.quantity - order.filled_quantity
            if price in bids:
                bids[price] += quantity
            else:
                bids[price] = quantity
                
        asks = {}  # Sell side
        for order in sell_orders:
            price = order.price
            quantity = order.quantity - order.filled_quantity
            if price in asks:
                asks[price] += quantity
            else:
                asks[price] = quantity
        
        # Format as sorted lists
        bids_list = [{"price": price, "quantity": quantity} for price, quantity in 
                     sorted(bids.items(), key=lambda x: x[0], reverse=True)]
        asks_list = [{"price": price, "quantity": quantity} for price, quantity in 
                     sorted(asks.items(), key=lambda x: x[0])]
        
        return {
            "commodity_id": commodity_id,
            "bids": bids_list,
            "asks": asks_list
        }
