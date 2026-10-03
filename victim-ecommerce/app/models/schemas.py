from pydantic import BaseModel
from typing import Optional, List


class UserRegister(BaseModel):
    username: str
    email: str = ""
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: int
    username: str
    role: str
    message: str = "Login successful"


class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: Optional[str] = None
    stock: int = 0


class ReviewCreate(BaseModel):
    rating: int
    comment: str


class ReviewOut(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: str
    created_at: str


class CartItem(BaseModel):
    item_id: int
    qty: int = 1


class CheckoutRequest(BaseModel):
    shipping_address: str = "123 Demo Street, Cyber City"


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderOut(BaseModel):
    id: int
    user_id: int
    total: float
    status: str
    shipping_address: Optional[str] = None
    items: List[OrderItemOut] = []
    created_at: str


class PingRequest(BaseModel):
    host: str


class PingResponse(BaseModel):
    host: str
    output: str
    success: bool


class ProfileOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    created_at: str


class MessageResponse(BaseModel):
    message: str
    success: bool = True
