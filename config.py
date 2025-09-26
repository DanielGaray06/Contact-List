from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'mydatabase.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MY_HOST = 'localhost'
    MY_USER = 'user'
    MY_PASSWORD = 'password'
    MY_DB = 'flaskcontacts'