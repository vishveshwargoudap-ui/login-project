from flask import Flask
from app.extensions import db
from flask_mail import Mail
import os


mail = Mail()
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
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT']=587
    app.config['MAIL_USE_TLS']=True
    app.config['MAIL_USE_SSL']=False
    app.config['MAIL_MAX_EMAILS']=1
    app.config['MAIL_USERNAME']=os.environ.get("MAIL_USERNAME")
    app.config['MAIL_PASSWORD']=os.environ.get("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER']=os.environ.get("MAIL_USERNAME")
    mail.init_app(app)

    db.init_app(app)
      # Import models to register them with SQLAlchemy
    from .import models
 #  with app.app_context():
  #  db.create_all()
      # Register blueprints

    from .auth import auth
    app.register_blueprint(auth)

    return app

