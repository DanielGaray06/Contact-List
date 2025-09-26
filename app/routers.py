from flask import Blueprint

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return "Hello World desde blueprint"

@main.route("/add")
def add():
    return "add contact"
