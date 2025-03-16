from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    counterparty_order_id = Column(
        Integer, ForeignKey("orders.id"), nullable=False
    )
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    order = relationship(
        "Order", foreign_keys=[order_id], back_populates="trades"
    )
    counterparty_order = relationship("Order", foreign_keys=[counterparty_order_id])
    
    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "counterparty_order_id": self.counterparty_order_id,
            "price": self.price,
            "quantity": self.quantity,
            "executed_at": self.executed_at.isoformat(),
        }
