from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=4, max_length=255)

    @field_validator("username", "email", "password")
    @classmethod
    def strip_nonempty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=255)


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
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=2000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("comment must not be empty")
        return cleaned


class ReviewOut(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: str
    created_at: str


class CartItem(BaseModel):
    item_id: int = Field(ge=1)
    qty: int = Field(ge=1, le=99)


class CheckoutRequest(BaseModel):
    shipping_address: str = Field(min_length=5, max_length=500)

    @field_validator("shipping_address")
    @classmethod
    def strip_address(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 5:
            raise ValueError("shipping address is too short")
        return cleaned


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    price: float
    name: Optional[str] = None


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
