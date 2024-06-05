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
from forms import RegistrationForm

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

@app.route("/products/<int:product_id>/", methods=["GET"])
def get_product_by_id(product_id: int):
    with get_db() as db:
        prod = services.get_product_by_id(db, product_id)
        if prod is None:
            return {"error": "Object not found"}, 404
        product_dict = {"id": prod.id, "name": prod.name, "color": prod.color, "weight": prod.weight,
                        "price": prod.price, "inventory": prod.inventory}
        return product_dict


@app.post("/products/")

def create_product():
    with get_db() as db:
        prod_data = request.get_json()

        try:
            product_create = schemas.ProductCreate(**prod_data)
        except ValueError as e:
            return jsonify({"error": "Invalid data format"}), 400

        new_product = services.product_create(db, product_create)

        serialized_product = {
            "id": new_product.id,
            "name": new_product.name,
            "color": new_product.color,
            "weight": new_product.weight,
            "price": new_product.price,
            "inventory": new_product.inventory,
        }

        return jsonify(serialized_product)

@app.put("/products/<int:product_id>/")
@login_required
def update_product(product_id: int):
    with get_db() as db:
        prod = services.get_product_by_id(db, product_id)
        if prod is None:
            return {"error": "Object not found"}, 404

        prod_data = request.get_json()

        try:
            product_update = schemas.ProductUpdate(**prod_data)
        except ValueError as e:
            return jsonify({"error": "Invalid data format"}), 400
        updated_product = services.product_update(db, prod, product_update)
        serialized_product = {
            "id": updated_product.id,
            "name": updated_product.name,
            "color": updated_product.color,
            "weight": updated_product.weight,
            "price": updated_product.price,
            "inventory": updated_product.inventory,
        }

        return jsonify(serialized_product)


@app.delete("/products/<int:product_id>/")
@admin_required
def delete_product_route(product_id: int):
    with get_db() as db:
        product = services.get_product_by_id(db, product_id)
        if product is None:
            return {"error": "Product not found"}, 404

        services.delete_product(db, product)

        return {"message": "Product deleted successfully"}, 204


@app.route("/addresses/", methods=["GET"])
@login_required
def get_addresses():
    with get_db() as db:
        street_filter = request.args.get("street", None)
        city_filter = request.args.get("city", None)
        country_filter = request.args.get("country", None)

        query = db.query(Address)

        if street_filter:
            query = query.filter(Address.street == street_filter)

        if city_filter:
            query = query.filter(Address.city == city_filter)

        if country_filter:
            query = query.filter(Address.country == country_filter)

        addresses = query.all()

        addresses_data = [
            {"id": address.id,
             "country": address.country,
             "city": address.city,
             "street": address.street} for address in addresses
        ]
        return jsonify(addresses_data)


@app.route("/addresses/<int:address_id>/", methods=["GET"])
@login_required
def get_address_by_id(address_id: int):
    with get_db() as db:
        address = services.get_address_by_id(db, address_id)
        if address is None:
            return {"error": "Object not found"}, 404
        address_dict = {"id": address.id, "country": address.country, "city": address.city, "street": address.street}
        return address_dict


@app.post("/addresses/")
@login_required
def create_address():
    with get_db() as db:
        address_data = request.get_json()

        try:
            address_create = schemas.AddressCreate(**address_data)
        except ValueError as e:
            return jsonify({"error": "Invalid data format"}), 400

        new_address = services.address_create(db, address_create)

        serialized_address = {
            "id": new_address.id,
            "country": new_address.country,
            "city": new_address.city,
            "street": new_address.street,
        }

        return jsonify(serialized_address)


@app.put("/addresses/<int:address_id>/")
@login_required
def update_address(address_id: int):
    with get_db() as db:
        address = services.get_address_by_id(db, address_id)
        if address is None:
            return {"error": "Address not found"}, 404

        address_data = request.get_json()

        try:
            address_update = schemas.AddressUpdate(**address_data)
        except ValueError as e:
            return jsonify({"error": "Invalid data format"}), 400

        updated_address = services.address_update(db, address, address_update)

        serialized_address = {
            "id": updated_address.id,
            "country": updated_address.country,
            "city": updated_address.city,
            "street": updated_address.street,
        }

        return jsonify(serialized_address)


@app.delete("/addresses/<int:address_id>/")
@admin_required
def delete_address_route(address_id: int):
    with get_db() as db:
        address = services.get_address_by_id(db, address_id)
        if address is None:
            return {"error": "Address not found"}, 404

        services.delete_address(db, address)

        return {"message": "Address deleted successfully"}, 204


@app.route("/orders/", methods=["GET"])
@login_required
def get_orders():
    db = SessionLocal()
    orders = services.get_orders(db)
    db.close()
    return jsonify([order.to_dict() for order in orders])


@app.route("/orders/<int:order_id>/", methods=["GET"])
@login_required
def get_order_by_id(order_id: int):
    with get_db() as db:
        order = services.get_order_by_id(db, order_id)
        if order is None:
            return {"error": "Object not found"}, 404
        order_dict = {
            "id": order.id,
            "status": order.status,
            "productitems": [
                {
                    "id": item.id,
                    "order_id": item.order_id,
                    "product_id": item.product_id,
                    "quantity": item.quantity
                }
                for item in order.productitems
            ],
            "address": {
                "id": order.address.id,
                "country": order.address.country,
                "city": order.address.city,
                "street": order.address.street
            }
        }
        return order_dict


@app.get("/orders/<int:order_id>/status/")
@login_required
def get_order_status(order_id: int):
    with get_db() as db:
        order = services.get_order_status_by_id(db, order_id)
        return order


@app.route("/orders/", methods=["POST"])
@login_required
def create_order():
    order_data = request.get_json()

    try:
        order_create = schemas.OrderCreate(**order_data)
    except ValueError as e:
        return jsonify({"error": "Invalid data format"}), 400

    with get_db() as db:
        try:
            new_order = services.create_order(db, order_create)
        except Exception as e:
            return jsonify({"error": "Failed to create order"}), 500

        return jsonify(new_order.to_dict()), 201


@app.put("/orders/<int:order_id>/status/")
@admin_required
def update_order_status(order_id: int):
    with get_db() as db:
        order = services.get_order_by_id(db, order_id)
        if order is None:
            return {"error": "Order not found"}, 404

        status_data = request.get_json()
        try:
            order_update = schemas.OrderUpdate(**status_data)
        except ValueError as e:
            return jsonify({"error": "Invalid data format"}), 400

        updated_order = services.update_order_status(db, order, order_update)

        order_update_dict = order_update.to_dict() if hasattr(order_update, 'to_dict') else order_update.__dict__

        track_order_status(order_id, order_update_dict)

        return jsonify(updated_order.to_dict()), 200


@app.delete("/orders/<int:order_id>/")
# @admin_required
def delete_order(order_id: int):
    with get_db() as db:
        order = services.get_order_by_id(db, order_id)
        if order is None:
            return {"error": "Order not found"}, 404

        services.delete_order(db, order)

        return {"message": "Order deleted successfully"}, 204


@app.route("/orders/status/", methods=["GET"])
@login_required
def get_orders_by_status():
    status_query = request.args.get("status")
    if not status_query:
        return {"error": "Missing 'status' query parameter"}, 400

    with get_db() as db:
        orders = services.get_order_by_status(db, status_query)
        orders_data = []
        for order in orders:
            order_dict = {
                "id": order.id,
                "status": order.status,
                "address_id": order.address_id,
                "productitems": [
                    {
                        "id": item.id,
                        "order_id": item.order_id,
                        "product_id": item.product_id,
                        "quantity": item.quantity
                    }
                    for item in order.productitems
                ]
            }
            orders_data.append(order_dict)

        return jsonify(orders_data)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    with get_db() as db:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = services.authenticate(db, username, password)
            if user:
                session['user'] = user.username
                session['is_admin'] = user.is_admin
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error='Invalid username or password')
        return render_template('login.html')


@app.route('/dashboard/')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    return render_template('dashboard.html', user={'username': username})


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user_create = schemas.UserCreate(username=username, password=password)

        if services.create_user(db, user_create):
            return redirect(url_for('login'))
        else:
            return render_template('register.html', form=form, error='Username already exists')
    return render_template('register.html', form=form)


@app.route("/users/<username>/", methods=["GET"])
def get_user_by_username(username):
    with get_db() as db:
        user = services.get_user_by_username(db, username)
        if user:
            return jsonify({"id": user.id, "username": user.username})
        return {"message": "User not found"}, 404


@app.route("/users/<username>/", methods=["PUT"])
def update_user_by_username(username):
    user_data = request.json
    with get_db() as db:
        user = services.get_user_by_username(db, username)
        if user:
            updated_user = services.update_user(db, user, schemas.UserUpdate(**user_data))
            return jsonify({"id": updated_user.id, "username": updated_user.username, "is_admin": updated_user.is_admin})   #noqa
        return {"message": "User not found"}, 404


@app.route("/users/<username>/", methods=["DELETE"])
def delete_user_by_username(username):
    with get_db() as db:
        user = services.get_user_by_username(db, username)
        if user:
            services.delete_user(db, user)
            return {"message": "User deleted successfully"}
        return {"message": "User not found"}, 404


if __name__ == '__main__':
    time.sleep(10)
    app.run(host='0.0.0.0', port=5000, debug=True)