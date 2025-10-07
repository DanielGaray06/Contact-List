from flask import Flask
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.secret_key = os.getenv("SECRET_KEY", "fallback-key")
    app.config["DATABASE"] = os.path.join("instance", "mydatabase.db")

    from contacts.routes import contacts_bp
    app.register_blueprint(contacts_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)