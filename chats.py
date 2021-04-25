from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash

def create_chat(campaign_id, title):
    sql = """INSERT INTO chats (title, campaign_id, created_at, visible)
              VALUES (:title, :campaign_id, NOW(), 1) RETURNING id"""
    chat_id = db.session.execute(
        sql, {"title":title, "campaign_id":campaign_id}).fetchone()[0]
    db.session.commit()
    return chat_id

def add_chatter(chat_id, user_id):
    sql = """INSERT INTO chat_users (user_id, chat_id, visible)
             VALUES (:user_id, :chat_id, 1)"""
    db.session.execute(sql, {"user_id":user_id, "chat_id":chat_id})
    db.session.commit()

def get_chatters(chat_id):
    sql = """SELECT user_id FROM chat_users
             WHERE chat_id=:chat_id AND visible=1"""
    return db.session.execute(sql, {"chat_id":chat_id}).fetchall()

