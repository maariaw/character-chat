from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash

def create_campaign(title, password):
    hash_value = generate_password_hash(password)
    creator_id = session.get("user_id", 0)
    sql = """INSERT INTO campaigns (title, creator_id, created_at,
             password, visible)
             VALUES (:title, :creator_id, NOW(), :password, 1)"""
    db.session.execute(
        sql,
        {"title":title, "creator_id":creator_id, "password":hash_value}
        )
    db.session.commit()

def get_created_campaigns(user_id):
    sql = """SELECT id, title, created_at FROM campaigns
             WHERE creator_id=:user_id ORDER BY created_at"""
    return db.session.execute(sql, {"user_id":user_id}).fetchall()