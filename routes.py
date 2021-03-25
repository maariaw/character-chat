from app import app
from app import db
from flask import redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT password FROM users WHERE name=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user == None:
        return render_template("index.html", error="Username not registered")
    else:
        hash_value = user[0]
        if check_password_hash(hash_value, password):
            session["username"] = username
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
    if len(username) > 20:
        return render_template("index.html", error="Username is too long")
    if len(password) < 8:
        return render_template("index.html", error="Password is too short")
    if len(password) > 32:
        return render_template("index.html", error="Password is too long")
    hash_value = generate_password_hash(password)
    sql = "INSERT INTO users (name, password) VALUES (:username, :password)"
    db.session.execute(sql, {"username":username, "password":hash_value})
    db.session.commit()
    session["username"] = username
    return redirect("/")
