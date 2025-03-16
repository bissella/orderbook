from pydantic import BaseModel, Field, validator
from typing import Optional
from models.order import OrderType


class CustomerCreate(BaseModel):
    name: str
    email: str


class CommodityCreate(BaseModel):
    name: str
    symbol: str
    description: Optional[str] = None


class OrderCreate(BaseModel):
    customer_id: int
    commodity_id: int
    order_type: str
    price: float
    quantity: float
    
    @validator('order_type')
    def validate_order_type(cls, v):
        if v not in [t.value for t in OrderType]:
            raise ValueError(f"Invalid order_type: {v}. Must be one of: {[t.value for t in OrderType]}")
        return v
    
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than zero")
        return v


class AuthHeader(BaseModel):
    api_key: str = Field(..., alias="X-API-Key")
