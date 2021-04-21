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

def is_active(campaign_id):
    sql = "SELECT visible FROM campaigns WHERE id=:campaign_id"
    result = db.session.execute(sql, {"campaign_id":campaign_id})
    status = result.fetchone()[0]
    print("Campaign status: ", status)
    return status == 1

def get_campaign_info(campaign_id):
    sql = """SELECT c.title title, u.name gm, c.created_at creation_time
             FROM campaigns c, users u
             WHERE c.id=:campaign_id AND u.id=c.creator_id"""
    result = db.session.execute(sql, {"campaign_id":campaign_id})
    campaign = result.fetchone()
    return campaign

def get_campaign_players(campaign_id):
    sql = """SELECT u.name FROM users u, campaign_users c
             WHERE c.campaign_id=:campaign_id
             AND u.id=c.user_id
             AND u.visible=1"""
    result = db.session.execute(sql, {"campaign_id":campaign_id})
    players = result.fetchall()
    return players

def is_duplicate(title, user_id):
    sql = "SELECT title FROM campaigns WHERE creator_id=:user_id"
    result = db.session.execute(sql, {"user_id":user_id}).fetchall()
    titles = [item[0] for item in result]
    return title in titles
