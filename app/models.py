from .extensions import db
import bcrypt
#define user and product models
class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
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