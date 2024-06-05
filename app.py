import os
import secrets
import time
from functools import wraps

from flask import Flask, g, request, jsonify, redirect, render_template, url_for, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jsonrpc import JSONRPC
import redis

import services, schemas
from db.database import SessionLocal
# from forms import RegistrationForm
from db.models import db, Address
# from tasks import track_order_status


try:
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    r.ping()
except redis.ConnectionError:
    print("Failed to connect to Redis.")

secret_key = secrets.token_hex(32)

app = Flask(__name__, template_folder='templates')
jsonrpc = JSONRPC(app, '/json-rpc')
app.config['SECRET_KEY'] = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.environ.get('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}" # noqa
db = SQLAlchemy(app)
migrate = Migrate(app, db)



def get_db():
    if 'db' not in g:
        g.db = SessionLocal()

    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or not session['is_admin']:
            return jsonify({"error": "Access denied. Admin permission required."}), 403
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route("/products/", methods=["GET"])
def get_products():
    with get_db() as db:
        products = services.get_all_products(db)
        products_dicts = [
            {"id": prod.id,
             "name": prod.name,
             "color": prod.color,
             "weight": prod.weight,
             "price": prod.price,
             "inventory": prod.inventory} for prod
            in products]
        return products_dicts


if __name__ == '__main__':
    time.sleep(10)
    app.run(host='0.0.0.0', port=5000, debug=True)