from typing import Optional, List
from pydantic import BaseModel, EmailStr

# Auth Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_admin: bool = False

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_admin: bool = False

# Product Schemas
class ProductCreate(BaseModel):
    title: str
    price: float
    image_url: Optional[str] = None
    description: Optional[str] = None
    stock: Optional[int] = 10

class ProductResponse(BaseModel):
    id: int
    title: str
    price: float
    image_url: Optional[str] = None
    description: Optional[str] = None
    stock: int = 10

    class Config:
        from_attributes = True

# Cart Schemas
class AddToCartRequest(BaseModel):
    product_id: int
    quantity: Optional[int] = 1

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    title: str
    price: float
    image_url: Optional[str] = None
    quantity: int
    subtotal: float

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total: float

# Agent Schemas
class AgentAskRequest(BaseModel):
    question: str

class AgentAskResponse(BaseModel):
    answer: str

