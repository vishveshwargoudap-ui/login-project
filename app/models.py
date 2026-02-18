from .extensions import db
import bcrypt
from datetime import datetime

class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='buyer')
    phone = db.Column(db.String(20))
    city = db.Column(db.String(100))
    address = db.Column(db.String(255))
    pincode = db.Column(db.String(20))

    def __init__(self, name, email, password, role='buyer'):
        self.name = name
        self.email = email
        role_value = (role or 'buyer').lower()
        self.role = role_value if role_value in {'buyer', 'seller', 'admin'} else 'buyer'
        self.password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password.encode('utf-8')
        )


class Product(db.Model):
    __tablename__="products"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(150),nullable=False)
    price=db.Column(db.Float,nullable=False)
    description=db.Column(db.String(300))
    image = db.Column(db.String(200))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    buyer_name = db.Column(db.String(100), nullable=False)
    buyer_phone = db.Column(db.String(20), nullable=False)
    payment_mode = db.Column(db.String(20), nullable=False)
    transaction_id = db.Column(db.String(100))
    total_amount = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan", lazy=True)


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
