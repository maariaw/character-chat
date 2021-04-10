from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
import os

def log_out():
    del session["username"]
    del session["role"]
    del session["user_id"]

def log_in(username, password):
    error = "no error"
    sql = "SELECT password, id, role FROM users WHERE name=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if not user:
        error = "Username not registered"
    else:
        hash_value = user[0]
        if check_password_hash(hash_value, password):
            session["username"] = username
            session["user_id"] = user[1]
            session["role"] = user[2]
        else:
            error = "Incorrect password"
    return error
