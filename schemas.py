from pydantic import BaseModel, SecretStr, NonNegativeInt, NonNegativeFloat
from typing import List, Optional


class ProductBase(BaseModel):
    id: int
    name: str
    color: str
    weight: NonNegativeFloat
    price: NonNegativeFloat
    inventory: NonNegativeInt

    class Config:
        orm_mode = True


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True


class ProductUpdate(ProductBase):
    pass


class AddressBase(BaseModel):
    id: int
    country: str
    city: str
    street: str

    class Config:
        orm_mode = True


class AddressCreate(AddressBase):
    pass


class Address(AddressBase):
    id: int

    class Config:
        orm_mode = True


class AddressUpdate(AddressBase):
    pass


class OrderItemBase(BaseModel):
    quantity: int
    product_id: int


class OrderBase(BaseModel):
    id: int
    status: str
    address_id: int
    productitems: List[OrderItemBase]

    class Config:
        orm_mode = True


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: str


class UserBase(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    username: str
    password: str


class User(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str]
    password: Optional[SecretStr]
