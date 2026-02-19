from flask import Flask
from .extensions import db
from sqlalchemy import text


def ensure_user_role_column():
    columns = db.session.execute(text("PRAGMA table_info(users)")).fetchall()
    column_names = {column[1] for column in columns}
    if "role" not in column_names:
        db.session.execute(
            text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'buyer'")
        )
        db.session.commit()

def ensure_user_profile_columns():
    columns = db.session.execute(text("PRAGMA table_info(users)")).fetchall()
    column_names = {column[1] for column in columns}

    if "phone" not in column_names:
        db.session.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
    if "city" not in column_names:
        db.session.execute(text("ALTER TABLE users ADD COLUMN city VARCHAR(100)"))
    if "address" not in column_names:
        db.session.execute(text("ALTER TABLE users ADD COLUMN address VARCHAR(255)"))
    if "pincode" not in column_names:
        db.session.execute(text("ALTER TABLE users ADD COLUMN pincode VARCHAR(20)"))

    db.session.commit()

def ensure_product_seller_column():
    columns = db.session.execute(text("PRAGMA table_info(products)")).fetchall()
    column_names = {column[1] for column in columns}
    if "seller_id" not in column_names:
        db.session.execute(
            text("ALTER TABLE products ADD COLUMN seller_id INTEGER")
        )
        db.session.commit()


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.database.db'
    app.config['SECRET_KEY'] = 'secret_key'

    db.init_app(app)
    
     
    from .auth import auth
    app.register_blueprint(auth)

    with app.app_context():
        db.create_all()
        ensure_user_role_column()
        ensure_user_profile_columns()
        ensure_product_seller_column()

    return app
