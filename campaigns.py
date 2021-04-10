from db import db

def get_created_campaigns(user_id):
    sql = """SELECT id, title, created_at FROM campaigns
             WHERE creator_id=:user_id ORDER BY created_at"""
    return db.session.execute(sql, {"user_id":user_id}).fetchall()