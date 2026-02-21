from flask import Flask
from .models import db
import os
  # Initialize the Flask application and configure it
def create_app():
    app = Flask(__name__)

    database_url = os.environ.get("DATABASE_URL")

    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "default_secret_key")
    app.config["SESSION_COOKIE_SECURE"]=True
    app.config["SESSION_COOKIE_SAMESITE"]="Lax"

    db.init_app(app)

    from .auth import auth
    app.register_blueprint(auth)

    with app.app_context():
        db.create_all()

    return app

