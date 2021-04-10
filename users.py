from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
import os

def log_out():
    del session["username"]
    del session["role"]
    del session["user_id"]

