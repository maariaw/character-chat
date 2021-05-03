from db import db
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
import users, campaigns

def create_chat(campaign_id, title, private):
    sql = """INSERT INTO chats (
             title, campaign_id, created_at, privated, closed, visible)
             VALUES (
             :title, :campaign_id, NOW(), :private, 0, 1)
             RETURNING id"""
    chat_id = db.session.execute(
        sql,
        {"title":title, "campaign_id":campaign_id, "private":private}
        ).fetchone()[0]
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
    result = db.session.execute(sql, {"chat_id":chat_id}).fetchall()
    chatters = [item[0] for item in result]
    return chatters

def get_campaign_chats(campaign_id):
    chat_list = []
    sql = """SELECT id FROM chats
             WHERE campaign_id=:campaign_id AND visible=1"""
    result = db.session.execute(sql, {"campaign_id":campaign_id}).fetchall()
    for row in result:
        chat_list.append(get_chat(row[0]))
    return chat_list

def get_chat(chat_id):
    chat = {}
    sql = """SELECT title, created_at, privated, closed, campaign_id FROM chats
             WHERE id=:chat_id"""
    result = db.session.execute(sql, {"chat_id":chat_id}).fetchone()
    chat["id"] = chat_id
    chat["title"] = result[0]
    chat["time"] = result[1]
    chat["private"] = result[2]
    chat["closed"] = result[3]
    chat["campaign_id"] = result[4]
    participants = get_chatters(chat_id)
    chatters = [users.get_username(chatter_id) for chatter_id in participants]
    chat["chatters"] = chatters
    chat["messages"] = get_messages(chat_id)
    return chat

def get_messages(chat_id):
    sql = """SELECT u.name, m.message, m.sent_at FROM users u, messages m
             WHERE chat_id=:chat_id AND u.id=m.user_id
             ORDER BY m.sent_at"""
    result = db.session.execute(sql, {"chat_id":chat_id}).fetchall()
    messages = []
    for row in result:
        message = {
            "username":row[0],
            "text":row[1],
            "time":row[2]
        }
        messages.append(message)
    return messages

def add_message(chat_id, text):
    user_id = session.get("user_id", 0)
    sql = """INSERT INTO messages (message, user_id, chat_id, sent_at, visible)
             VALUES (:text, :user_id, :chat_id, NOW(), 1)"""
    db.session.execute(
        sql, {"text":text, "user_id":user_id, "chat_id":chat_id})
    db.session.commit()

def close(chat_id):
    sql = "UPDATE chats SET closed=1 WHERE id=:chat_id"
    db.session.execute(sql, {"chat_id":chat_id})
    db.session.commit()

def remove_from_all_chats(user_id):
    sql = "DELETE FROM chat_users WHERE user_id=:user_id"
    db.session.execute(sql, {"user_id":user_id})
    db.session.commit()
