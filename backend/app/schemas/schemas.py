from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class Register(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)
    phone: str | None = None
    department: str | None = None


class Login(BaseModel):
    email: EmailStr
    password: str


class FoodCreate(BaseModel):
    category_id: int
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    price: float = Field(ge=0)
    available: bool = True
    stock_quantity: int = Field(ge=0, default=20)
    minimum_stock: int = Field(ge=0, default=5)


class FoodUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    available: bool | None = None
    active: bool | None = None


class CartLine(BaseModel):
    food_id: int
    quantity: int = Field(gt=0, le=20)


class OrderCreate(BaseModel):
    items: list[CartLine] = Field(min_length=1)
    pickup_slot: str
    payment_mode: Literal['MOCK_ONLINE', 'PAY_AT_PICKUP']


class StatusUpdate(BaseModel):
    status: Literal['PLACED', 'PREPARING', 'READY', 'COMPLETED', 'CANCELLED']


class InventoryUpdate(BaseModel):
    stock_quantity: int = Field(ge=0)
    minimum_stock: int | None = Field(default=None, ge=0)


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class SupplierCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    contact: str | None = None
    email: EmailStr | None = None
    address: str | None = None


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    contact: str | None = None
    email: EmailStr | None = None
    address: str | None = None


class SupplierItemCreate(BaseModel):
    food_id: int
    supply_price: float = Field(ge=0)
    quantity_supplied: int = Field(gt=0)


class UserRoleUpdate(BaseModel):
    role: Literal['STUDENT', 'STAFF', 'ADMIN']


class UserStatusUpdate(BaseModel):
    active: bool
