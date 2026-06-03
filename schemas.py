from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Product Schemas
class ProductBase(BaseModel):
    sku: str
    name: str
    price: float
    stock: int

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True

# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    email: EmailStr

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int

    class Config:
        from_attributes = True

# Order Schemas
class OrderBase(BaseModel):
    product_id: int
    customer_id: int
    quantity: int

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    status: str = "pending"
    order_date: Optional[datetime] = None

    class Config:
        from_attributes = True
