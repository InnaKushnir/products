from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from database import Base

db = SQLAlchemy(metadata=Base.metadata)
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://user1:password1@localhost/product1"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()

    return app