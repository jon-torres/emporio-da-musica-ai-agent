from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Category(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None


class Product(BaseModel):
    product_id: int
    name: str
    price_brl: float
    category_id: int
    category_name: Optional[str] = None
    description: str
    stock_quantity: int
    status: str
    specs: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    active_discount_percent: Optional[int] = None
    promotional_price: Optional[float] = None


class Customer(BaseModel):
    customer_id: int
    name: str
    phone: str
    email: str
    city: str


class OrderItem(BaseModel):
    order_id: int
    product_id: int
    quantity: int
    product_name: Optional[str] = None
    unit_price: Optional[float] = None


class Order(BaseModel):
    order_id: int
    customer_id: int
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    order_date: str
    status: str
    total_brl: float
    payment_method: str
    tracking_code: Optional[str] = None
    estimated_delivery: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItem] = Field(default_factory=list)


class Promotion(BaseModel):
    promotion_id: int
    product_id: int
    product_name: Optional[str] = None
    discount_percent: int
    description: str
    is_active: bool
