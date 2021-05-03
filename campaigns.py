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
             WHERE creator_id=:user_id AND visible=1
             ORDER BY created_at"""
    return db.session.execute(sql, {"user_id":user_id}).fetchall()

def is_active(campaign_id):
    sql = "SELECT visible FROM campaigns WHERE id=:campaign_id"
    result = db.session.execute(sql, {"campaign_id":campaign_id})
    status = result.fetchone()[0]
    return status == 1

def get_campaign_info(campaign_id):
    sql = """SELECT
                 c.id id,
                 c.title title,
                 u.name gm,
                 c.created_at creation_time
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
    result = db.session.execute(sql, {"campaign_id":campaign_id}).fetchall()
    players = [item[0] for item in result]
    return players

def get_campaign_title(campaign_id):
    sql = "SELECT title FROM campaigns WHERE id=:campaign_id"
    result = db.session.execute(sql, {"campaign_id":campaign_id}).fetchone()
    return result[0]

def is_duplicate(title, user_id):
    sql = "SELECT title FROM campaigns WHERE creator_id=:user_id"
    result = db.session.execute(sql, {"user_id":user_id}).fetchall()
    titles = [item[0] for item in result]
    return title in titles

def deactivate_created_campaigns(user_id):
    campaign_list = get_created_campaigns(user_id)
    for campaign in campaign_list:
        deactivate_campaign(campaign.id)

def deactivate_campaign(campaign_id):
    user_id = session.get("user_id")
    sql = "SELECT creator_id, visible FROM campaigns WHERE id=:campaign_id"
    result = db.session.execute(sql, {"campaign_id":campaign_id}).fetchone()
    creator_id = result[0]
    status = result[1]
    if not creator_id or user_id != creator_id or status == 0:
        return False
    sql = "UPDATE campaigns SET visible=0 WHERE id=:campaign_id"
    db.session.execute(sql, {"campaign_id":campaign_id})
    db.session.commit()
    return True

def check_password(campaign_id, password):
    sql = "SELECT password FROM campaigns WHERE id=:campaign_id"
    result = db.session.execute(sql, {"campaign_id":campaign_id}).fetchone()
    password_hash = result[0]
    return check_password_hash(password_hash, password)

def is_creator(campaign_id, user_id):
    sql = "SELECT creator_id FROM campaigns WHERE id=:campaign_id"
    result = db.session.execute(sql, {"campaign_id":campaign_id}).fetchone()
    creator = result[0]
    return user_id == creator

def has_access(campaign_id, user_id):
    if is_creator(campaign_id, user_id):
        return True
    sql = """SELECT 1 FROM campaign_users
             WHERE user_id=:user_id AND campaign_id=:campaign_id"""
    result = db.session.execute(
        sql, {"user_id":user_id, "campaign_id":campaign_id})
    return result.fetchone() != None

def get_all():
    sql = "SELECT id FROM campaigns WHERE visible=1 ORDER BY created_at"
    result = db.session.execute(sql).fetchall()
    campaign_list = []
    for item in result:
        id = item[0]
        campaign = get_campaign_info(id)
        campaign_list.append(campaign)
    return  campaign_list

def add_player(campaign_id, user_id):
    if not is_active(campaign_id):
        return False
    try:
        sql = """INSERT INTO campaign_users (user_id, campaign_id, visible)
                VALUES (:user_id, :campaign_id, 1)"""
        db.session.execute(sql, {"user_id":user_id, "campaign_id":campaign_id})
        db.session.commit()
    except:
        return False
    return True

def get_joined_campaigns(user_id):
    sql = """SELECT c.id FROM campaigns c, campaign_users u
            WHERE c.visible=1 AND u.visible=1
            AND c.id=u.campaign_id AND u.user_id=:user_id
            ORDER BY created_at"""
    result = db.session.execute(sql, {"user_id":user_id}).fetchall()
    campaign_list = []
    for item in result:
        id = item[0]
        campaign = get_campaign_info(id)
        campaign_list.append(campaign)
    return  campaign_list

def remove_user_from_campaign(campaign_id, user_id):
    try:
        sql = """DELETE FROM campaign_users
                WHERE user_id=:user_id AND campaign_id=:campaign_id"""
        db.session.execute(sql, {"user_id":user_id, "campaign_id":campaign_id})
        db.session.commit()
        return True
    except:
        return False

def search_by_title(title):
    sql = """SELECT id FROM campaigns
             WHERE visible=1 AND lower(title) LIKE lower(:title)
             ORDER BY created_at"""
    result = db.session.execute(sql, {"title":"%"+title+"%"}).fetchall()
    campaign_list = []
    for item in result:
        id = item[0]
        campaign = get_campaign_info(id)
        campaign_list.append(campaign)
    return  campaign_list

def get_by_gm_ids(gm_id_list):
    sql = """SELECT id FROM campaigns
             WHERE visible=1 AND creator_id = ANY (:gm_id_list)
             ORDER BY created_at"""
    result = db.session.execute(sql, {"gm_id_list":gm_id_list}).fetchall()
    campaign_list = []
    for item in result:
        id = item[0]
        campaign = get_campaign_info(id)
        campaign_list.append(campaign)
    return  campaign_list

def remove_from_all_campaigns(user_id):
    sql = "DELETE FROM campaign_users WHERE user_id=:user_id"
    db.session.execute(sql, {"user_id":user_id})
    db.session.commit()
