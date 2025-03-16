from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database.db import Base


class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    OPEN = "open"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    status = Column(
        SQLEnum(OrderStatus), default=OrderStatus.OPEN, nullable=False
    )
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    filled_quantity = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    commodity = relationship("Commodity", back_populates="orders")
    trades = relationship(
        "Trade", foreign_keys="Trade.order_id", back_populates="order"
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "commodity_id": self.commodity_id,
            "order_type": self.order_type.value,
            "status": self.status.value,
            "price": self.price,
            "quantity": self.quantity,
            "filled_quantity": self.filled_quantity,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
