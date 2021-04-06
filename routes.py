from app import app
from app import db
from flask import redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import campaigns

@app.route("/")
def index():
    if session.get("role", 0) == 2:
        campaign_list = campaigns.get_created_campaigns(session.get("user_id", 0))
    else:
        campaign_list = []
    return render_template("index.html", campaigns=campaign_list)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT password, id, role FROM users WHERE name=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user == None:
        return render_template("index.html", error="Username not registered")
    else:
        hash_value = user[0]
        if check_password_hash(hash_value, password):
            session["username"] = username
            session["user_id"] = user[1]
            role = user[2]
            session["role"] = role
            return redirect("/")
        else:
            return render_template("index.html", error="Incorrect password")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    account_type = request.form["account"]
    if len(username) > 20:
        return render_template("index.html", error="Username is too long")
    if len(password) < 8:
        return render_template("index.html", error="Password is too short")
    if len(password) > 32:
        return render_template("index.html", error="Password is too long")
    hash_value = generate_password_hash(password)
    sql = "INSERT INTO users (name, password, role) VALUES (:username, :password, :account)"
    db.session.execute(sql, {"username":username, "password":hash_value, "account":account_type})
    db.session.commit()
    session["username"] = username
    session["role"] = account_type
    return redirect("/")

@app.route("/newcampaign")
def new_campaign():
    return render_template("newcampaign.html")

@app.route("/createcampaign", methods=["POST"])
def create_campaign():
    title = request.form["title"]
    password = request.form["password"]
    if len(title) > 100:
        return render_template("newcampaign.html", error="Title is too long")
    if len(password) < 8:
        return render_template("newcampaign.html", error="Password is too short")
    if len(password) > 32:
        return render_template("newcampaign.html", error="Password is too long")
    hash_value = generate_password_hash(password)
    creator_id = session.get("user_id", 0)
    sql = """INSERT INTO campaigns (title, creator_id, created_at, password)
             VALUES (:title, :creator_id, NOW(), :password)"""
    db.session.execute(sql, {"title":title, "creator_id":creator_id, "password":hash_value})
    db.session.commit()
    return redirect("/")