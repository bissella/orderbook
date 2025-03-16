# Commodity Order Book

A complete trading system for commodity markets with a matching engine, order book, and user interface.

## Features

- RESTful API for querying prices and order book data
- API endpoints for placing, viewing and canceling trades
- Database for tracking trades by customer
- Web-based UI for viewing and interacting with the order book
- Matching engine that processes trades according to price-time priority

## Requirements

- Python 3.8+
- UV package manager

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd windsurf-project
```

2. Install dependencies using UV:

```bash
pip install uv
uv pip install -e .
```

## Usage

1. Start the application:

```bash
python app.py
```

2. Open a web browser and navigate to `http://localhost:5000`

3. Register a new account to get an API key

4. Use the UI to create commodities, place orders, and view the order book

## API Documentation

### Authentication

All API endpoints require authentication using the `X-API-Key` header.

### Customers

- `GET /api/customers` - Get current customer information
- `POST /api/customers` - Create a new customer

### Commodities

- `GET /api/commodities` - Get all commodities
- `POST /api/commodities` - Create a new commodity
- `GET /api/commodities/<id>` - Get a specific commodity

### Order Book

- `GET /api/orderbook/<commodity_id>` - Get order book for a specific commodity

### Orders

- `GET /api/orders` - Get all orders for the current customer
- `POST /api/orders` - Create a new order
- `GET /api/orders/<id>` - Get a specific order
- `DELETE /api/orders/<id>` - Cancel an order

### Trades

- `GET /api/trades` - Get all trades for the current customer

## Database Schema

- `customers` - Store customer information and API keys
- `commodities` - Store commodity information
- `orders` - Store order information
- `trades` - Store execution information

## Architecture

The application follows a layered architecture:

1. **Database Layer**: SQLAlchemy models and database connection
2. **Business Logic Layer**: Order book implementation with matching algorithm
3. **API Layer**: RESTful API endpoints for client interaction
4. **UI Layer**: Web interface for human interaction

## License

MIT
