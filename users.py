from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
import os

def log_out():
    del session["username"]
    del session["role"]
    del session["user_id"]
    del session["csrf_token"]

def log_in(username, password):
    error = "no error"
    sql = "SELECT password, id, role, visible FROM users WHERE name=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if not user:
        error = "Username not registered"
    elif user[3] == 0:
        error = "Account has been deactivated"
    else:
        hash_value = user[0]
        if check_password_hash(hash_value, password):
            session["username"] = username
            session["user_id"] = user[1]
            session["role"] = user[2]
            session["csrf_token"] = os.urandom(16).hex()
        else:
            error = "Incorrect password"
    return error

def register(username, password, role):
    hash_value = generate_password_hash(password)
    try:
        sql = """INSERT INTO users (name, password, role, visible)
                VALUES (:username, :password, :role, 1)"""
        db.session.execute(
            sql,
            {"username":username, "password":hash_value, "role":role}
            )
        db.session.commit()
    except:
        return "Could not register account"
    return log_in(username, password)

def user_exists(username):
    sql = "SELECT 1 FROM users WHERE name=:username"
    result = db.session.execute(sql, {"username":username})
    return result.fetchone() != None

def deactivate_account(username, password):
    if check_password(username, password) and account_active(username):
        sql = "UPDATE users SET visible=0 WHERE name=:username"
        db.session.execute(sql, {"username":username})
        db.session.commit()
        log_out()
        return True
    else:
        return False

def reactivate_account(username, password):
    if check_password(username, password) and not account_active(username):
        sql = "UPDATE users SET visible=1 WHERE name=:username"
        db.session.execute(sql, {"username":username})
        db.session.commit()
        return True
    else:
        return False

def account_active(username):
    sql = "SELECT visible FROM users WHERE name=:username"
    result = db.session.execute(sql, {"username":username})
    visibility = result.fetchone()[0]
    return visibility == 1

def check_password(username, password):
    sql = "SELECT password FROM users WHERE name=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if not user:
        return False
    return check_password_hash(user[0], password)
