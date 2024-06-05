from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .database import engine, Base
from .models import User, Product, SubAddress, Address, Order, OrderItem

db = SQLAlchemy(metadata=Base.metadata)  # Використовуємо Base.metadata
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://superuser:password@localhost/product"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()

    return app