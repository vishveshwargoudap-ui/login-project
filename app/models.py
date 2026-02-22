from app.extensions import db
import bcrypt
#define user and product models
class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role=db.Column(db.String(50), nullable=False, default='buyer')   

    def __init__(self, name, email, password,role='buyer'):
        self.name = name
        self.email = email
        self.role=role
        self.password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password.encode('utf-8')
        )
    # Define a method to check if the user is a seller
class Product(db.Model):
    __tablename__="products"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(150),nullable=False)
    price=db.Column(db.Float,nullable=False)
    description=db.Column(db.String(300))
    image = db.Column(db.Text, nullable=True)
    seller_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product", backref="order_items")