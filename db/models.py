from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from .database import Base

db = SQLAlchemy()

class User(Base):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    color = Column(String(255), nullable=False)
    weight = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    inventory = Column(Integer, nullable=False)
    productitems = relationship("OrderItem", back_populates="product")


class SubAddress(Base):
    __tablename__ = "sub_address"
    id = Column(Integer, primary_key=True, index=True)
    sub_address_details = Column(String(255), nullable=False)
    main_address_id = Column(Integer, ForeignKey("address.id"))
    main_address = relationship("Address", back_populates="sub_addresses")


class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True, index=True)
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    street = Column(String(255), nullable=False)
    orders = relationship("Order", back_populates="address")
    sub_addresses = relationship("SubAddress", back_populates="main_address")


class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(length=50), nullable=False, default=OrderStatus.PENDING.value)
    address_id = Column(Integer, ForeignKey("address.id"))
    address = relationship("Address", back_populates="orders")
    productitems = relationship("OrderItem", back_populates="order", lazy='joined')

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "address_id": self.address_id,
            "productitems": [item.to_dict() for item in self.productitems],
        }


class OrderItem(Base):
    __tablename__ = "orderitem"
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False)
    order_id = Column(Integer, ForeignKey("order.id"))
    order = relationship("Order", back_populates="productitems")
    product_id = Column(Integer, ForeignKey("product.id"))
    product = relationship("Product", back_populates="productitems")

    def to_dict(self):
        return {
            "id": self.id,
            "quantity": self.quantity,
            "product_id": self.product_id,
            "order_id": self.order_id,
        }