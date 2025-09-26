from flask import Flask
from .extensions import db
from .routers import main
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(main)

    return app