from sqlalchemy.orm import Session
from typing import Any

import models
import schemas


def get_all_products(db: Session) -> models.Product:
    return db.query(models.Product).order_by(models.Product.id).all()


def get_product_by_id(db: Session, product_id: int) -> models.Product:
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def product_create(db: Session, prod: schemas.ProductCreate) -> models.Product:
    db_product = models.Product(
        name=prod.name,
        color=prod.color,
        weight=prod.weight,
        price=prod.price,
        inventory=prod.inventory
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def product_update(
        db: Session,
        product: models.Product,
        product_update: schemas.ProductUpdate) -> models.Product:
    for field, value in product_update.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: models.Product):
    db.delete(product)
    db.commit()


def get_addresses(db: Session) -> models.Address:
    return db.query(models.Address).order_by(models.Address.id).all()


def get_address_by_id(db: Session, address_id: int) -> models.Address:
    return db.query(models.Address).filter(models.Address.id == address_id).first()


def address_create(db: Session, address: schemas.AddressCreate) -> models.Address:
    db_address = models.Address(
        country=address.country,
        city=address.city,
        street=address.street,
    )
    db.add(db_address)
    db.commit()
    db.refresh(db_address)
    return db_address


def address_update(
        db: Session, address: models.Address,
        address_update: schemas.AddressUpdate) -> models.Address:
    for field, value in address_update.model_dump(exclude_unset=True).items():
        setattr(address, field, value)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, address: models.Address):
    db.delete(address)
    db.commit()


def get_orders(db: Session) -> models.Order:
    return db.query(models.Order).all()


def get_order_by_id(db: Session, order_id: int) -> models.Order:
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_order_status_by_id(db: Session, order_id: int) -> dict[str: Any]:
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if order is None:
        return {"error": "Order not found"}, 404
    return {"status": order.status}


def create_order(db: Session, order: schemas.OrderCreate) -> models.Order:

    order_data = order.model_dump()
    product_items_data = order_data.pop("productitems")

    order_db = models.Order(**order_data)
    db.add(order_db)

    for item in product_items_data:
        product_id = item.get("product_id")
        quantity = item.get("quantity")
        product = db.query(models.Product).get(product_id)

        if product is None:
            db.rollback()
            return None

        if product.inventory < quantity:
            db.rollback()
            return None
        product.inventory -= quantity
        order_item_db = models.OrderItem(**item, order_id=order_db.id)
        db.add(order_item_db)

    db.commit()
    db.refresh(order_db)

    return order_db


def update_order_status(
        db: Session,
        order: models.Order,
        order_update: schemas.OrderUpdate) -> dict:
    if isinstance(order_update, dict):
        order_update = schemas.OrderUpdate(**order_update)

    order_data = order_update.dict(exclude={"productitems"})
    for key, value in order_data.items():
        setattr(order, key, value)

    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order: models.Order):
    db.delete(order)
    db.commit()


def get_order_by_status(db: Session, status: str) -> models.Order:
    return db.query(models.Order).filter(models.Order.status == status).all()


def get_user_by_username(db: Session, username: str) -> models.User:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.Order:
    new_user = models.User(
        username=user.username,
        password=user.password,
    )
    db.session.add(new_user)
    db.session.commit()
    db.session.refresh(new_user)
    return new_user


def update_user(db: Session, user: models.User, user_update: schemas.UserUpdate) -> models.User:
    update_data = user_update.dict(exclude_unset=True)

    if 'password' in update_data:
        user.set_password(update_data.pop('password').get_secret_value())

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

def authenticate(db: Session, username, password):
    db_user = db.query(models.User).filter_by(username=username).first()
    if db_user and db_user.check_password(password):
        return db_user
    return None


def delete_user(db: Session, user: models.User):
    db.delete(user)
    db.commit()



