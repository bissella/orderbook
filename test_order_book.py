#!/usr/bin/env python
"""
Test script for the Order Book matching system
This script initializes the database with test data and performs some basic order matching tests
"""

import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session

# Set up environment and imports
from database.db import engine, Base, SessionLocal, init_db
from models import Customer, Commodity, Order, OrderType, OrderStatus, Trade
from database.order_book import OrderBook

def clean_database():
    """Drop all tables and recreate them for a fresh start."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset completed.")

def create_test_data(db: Session):
    """Initialize the database with test data."""
    # Create customers
    customers = [
        Customer(
            name="Alice Trading Co.",
            email="alice@example.com",
            api_key="alice-api-key-12345"
        ),
        Customer(
            name="Bob Investment LLC",
            email="bob@example.com",
            api_key="bob-api-key-67890"
        ),
        Customer(
            name="Charlie Commodities",
            email="charlie@example.com",
            api_key="charlie-api-key-abcde"
        )
    ]
    
    db.add_all(customers)
    db.commit()
    for c in customers:
        db.refresh(c)
    print(f"Created {len(customers)} test customers")
    
    # Create commodities
    commodities = [
        Commodity(
            name="Gold",
            symbol="XAU",
            description="Gold bullion (troy ounce)"
        ),
        Commodity(
            name="Silver",
            symbol="XAG",
            description="Silver bullion (troy ounce)"
        ),
        Commodity(
            name="Crude Oil",
            symbol="OIL",
            description="Crude oil (barrel)"
        ),
        Commodity(
            name="Natural Gas",
            symbol="GAS",
            description="Natural gas (cubic meter)"
        )
    ]
    
    db.add_all(commodities)
    db.commit()
    for c in commodities:
        db.refresh(c)
    print(f"Created {len(commodities)} test commodities")
    
    return customers, commodities

def test_basic_order_matching(db: Session, customers: list, commodities: list):
    """Test the basic order matching functionality."""
    # Create an order book
    order_book = OrderBook(db)
    
    gold = commodities[0]
    alice = customers[0]
    bob = customers[1]
    
    print(f"\n----- Testing Basic Order Matching for {gold.name} -----")
    
    # Alice places a BUY order for 10 oz of gold at $1900/oz
    alice_buy_order = Order(
        customer_id=alice.id,
        commodity_id=gold.id,
        order_type=OrderType.BUY,
        price=1900.0,
        quantity=10.0,
        filled_quantity=0.0,
        status=OrderStatus.OPEN
    )
    
    print(f"Alice places a BUY order: {alice_buy_order.quantity} oz of {gold.name} at ${alice_buy_order.price}/oz")
    
    alice_order, trades = order_book.add_order(alice_buy_order)
    print(f"Order added with ID: {alice_order.id}")
    print(f"Trades executed: {len(trades)}")
    
    # Bob places a SELL order for 5 oz of gold at $1890/oz (should match with Alice's order)
    bob_sell_order = Order(
        customer_id=bob.id,
        commodity_id=gold.id,
        order_type=OrderType.SELL,
        price=1890.0,
        quantity=5.0,
        filled_quantity=0.0,
        status=OrderStatus.OPEN
    )
    
    print(f"\nBob places a SELL order: {bob_sell_order.quantity} oz of {gold.name} at ${bob_sell_order.price}/oz")
    
    bob_order, trades = order_book.add_order(bob_sell_order)
    print(f"Order added with ID: {bob_order.id}")
    print(f"Trades executed: {len(trades)}")
    
    if trades:
        print("\nTrade details:")
        for trade in trades:
            print(f"  - Trade ID: {trade.id}")
            print(f"    Price: ${trade.price}")
            print(f"    Quantity: {trade.quantity} oz")
            print(f"    Buyer: Order #{trade.counterparty_order_id}")
            print(f"    Seller: Order #{trade.order_id}")
    
    # Get order book snapshot to see the current state
    book_snapshot = order_book.get_order_book_snapshot(gold.id)
    print("\nOrder Book Snapshot:")
    print("  Bids:")
    for bid in book_snapshot["bids"]:
        print(f"    - Price: ${bid['price']}, Quantity: {bid['quantity']} oz")
    print("  Asks:")
    for ask in book_snapshot["asks"]:
        print(f"    - Price: ${ask['price']}, Quantity: {ask['quantity']} oz")
    
    # Verify the order status and filled quantities
    alice_order_check = db.query(Order).filter(Order.id == alice_order.id).first()
    bob_order_check = db.query(Order).filter(Order.id == bob_order.id).first()
    
    print("\nVerifying order status:")
    print(f"  Alice's order:")
    print(f"    - Status: {alice_order_check.status.value}")
    print(f"    - Filled: {alice_order_check.filled_quantity}/{alice_order_check.quantity} oz")
    print(f"  Bob's order:")
    print(f"    - Status: {bob_order_check.status.value}")
    print(f"    - Filled: {bob_order_check.filled_quantity}/{bob_order_check.quantity} oz")

def test_partial_matching(db: Session, customers: list, commodities: list):
    """Test partial order matching functionality."""
    # Create an order book
    order_book = OrderBook(db)
    
    silver = commodities[1]
    alice = customers[0]
    bob = customers[1]
    charlie = customers[2]
    
    print(f"\n----- Testing Partial Order Matching for {silver.name} -----")
    
    # Alice places a BUY order for 20 oz of silver at $25/oz
    alice_buy_order = Order(
        customer_id=alice.id,
        commodity_id=silver.id,
        order_type=OrderType.BUY,
        price=25.0,
        quantity=20.0,
        filled_quantity=0.0,
        status=OrderStatus.OPEN
    )
    
    print(f"Alice places a BUY order: {alice_buy_order.quantity} oz of {silver.name} at ${alice_buy_order.price}/oz")
    alice_order, trades = order_book.add_order(alice_buy_order)
    print(f"Order added with ID: {alice_order.id}")
    
    # Bob places a SELL order for 10 oz of silver at $24.5/oz (should partially match with Alice's order)
    bob_sell_order = Order(
        customer_id=bob.id,
        commodity_id=silver.id,
        order_type=OrderType.SELL,
        price=24.5,
        quantity=10.0,
        filled_quantity=0.0,
        status=OrderStatus.OPEN
    )
    
    print(f"\nBob places a SELL order: {bob_sell_order.quantity} oz of {silver.name} at ${bob_sell_order.price}/oz")
    bob_order, trades = order_book.add_order(bob_sell_order)
    print(f"Order added with ID: {bob_order.id}")
    print(f"Trades executed: {len(trades)}")
    
    if trades:
        print("\nTrade details:")
        for trade in trades:
            print(f"  - Trade ID: {trade.id}")
            print(f"    Price: ${trade.price}")
            print(f"    Quantity: {trade.quantity} oz")
    
    # Charlie places a SELL order for 15 oz of silver at $24.8/oz (should match with the remainder of Alice's order)
    charlie_sell_order = Order(
        customer_id=charlie.id,
        commodity_id=silver.id,
        order_type=OrderType.SELL,
        price=24.8,
        quantity=15.0,
        filled_quantity=0.0,
        status=OrderStatus.OPEN
    )
    
    print(f"\nCharlie places a SELL order: {charlie_sell_order.quantity} oz of {silver.name} at ${charlie_sell_order.price}/oz")
    charlie_order, trades = order_book.add_order(charlie_sell_order)
    print(f"Order added with ID: {charlie_order.id}")
    print(f"Trades executed: {len(trades)}")
    
    if trades:
        print("\nTrade details:")
        for trade in trades:
            print(f"  - Trade ID: {trade.id}")
            print(f"    Price: ${trade.price}")
            print(f"    Quantity: {trade.quantity} oz")
    
    # Verify the final state of all orders
    alice_order_check = db.query(Order).filter(Order.id == alice_order.id).first()
    bob_order_check = db.query(Order).filter(Order.id == bob_order.id).first()
    charlie_order_check = db.query(Order).filter(Order.id == charlie_order.id).first()
    
    print("\nVerifying final order status:")
    print(f"  Alice's order:")
    print(f"    - Status: {alice_order_check.status.value}")
    print(f"    - Filled: {alice_order_check.filled_quantity}/{alice_order_check.quantity} oz")
    print(f"  Bob's order:")
    print(f"    - Status: {bob_order_check.status.value}")
    print(f"    - Filled: {bob_order_check.filled_quantity}/{bob_order_check.quantity} oz")
    print(f"  Charlie's order:")
    print(f"    - Status: {charlie_order_check.status.value}")
    print(f"    - Filled: {charlie_order_check.filled_quantity}/{charlie_order_check.quantity} oz")
    
    # Get order book snapshot to see the current state
    book_snapshot = order_book.get_order_book_snapshot(silver.id)
    print("\nFinal Order Book Snapshot:")
    print("  Bids:")
    for bid in book_snapshot["bids"]:
        print(f"    - Price: ${bid['price']}, Quantity: {bid['quantity']} oz")
    print("  Asks:")
    for ask in book_snapshot["asks"]:
        print(f"    - Price: ${ask['price']}, Quantity: {ask['quantity']} oz")

def main():
    """Main function to run the tests."""
    print("======= Order Book System Test =======")
    
    # Clean and initialize the database
    clean_database()
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Create test data
        customers, commodities = create_test_data(db)
        
        # Run tests
        test_basic_order_matching(db, customers, commodities)
        test_partial_matching(db, customers, commodities)
        
        print("\n======= All Tests Completed =======")
    finally:
        db.close()

if __name__ == "__main__":
    main()
