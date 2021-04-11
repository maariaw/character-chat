from app import app
from db import db
from flask import redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import users, campaigns

@app.route("/")
def index():
    if session.get("role", 0) == 2:
        campaign_list = campaigns.get_created_campaigns(
            session.get("user_id", 0))
    else:
        campaign_list = []
    return render_template("index.html", campaigns=campaign_list)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    error_message = users.log_in(username, password)
    if error_message == "no error":
        return redirect("/")
    else:
        return render_template("index.html", error=error_message)

@app.route("/logout")
def logout():
    users.log_out()
    return redirect("/")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    if len(username) < 1 or len(username) > 20:
        return render_template(
            "index.html", error="Username has to be 1-20 characters long")
    if users.user_exists(username):
        return render_template(
            "index.html", error="Username is already in use")
    password1 = request.form["password1"]
    if len(password1) < 8 or len(password1) > 32:
        return render_template(
            "index.html", error="Password has to be 8-32 characters long")
    password2 = request.form["password2"]
    if password1 != password2:
        return render_template(
            "index.html", error="Password was retyped incorrectly")
    account_type = request.form["account"]
    if account_type != "1" and account_type != "2":
        return render_template(
            "index.html", error="Account type not recognized")
    error_message = users.register(username, password1, account_type)
    if error_message == "no error":
        return redirect("/")
    else:
        return render_template("index.html", error=error_message)

@app.route("/newcampaign")
def new_campaign():
    return render_template("newcampaign.html")

@app.route("/createcampaign", methods=["POST"])
def create_campaign():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
    title = request.form["title"]
    password = request.form["password"]
    if len(title) > 100:
        return render_template("newcampaign.html", error="Title is too long")
    if len(password) < 8:
        return render_template(
            "newcampaign.html", error="Password is too short")
    if len(password) > 32:
        return render_template(
            "newcampaign.html", error="Password is too long")
    campaigns.create_campaign(title, password)
    return redirect("/")

@app.route("/account_status", methods=["POST", "GET"])
def change_account_status():
    if request.method == "GET":
        return render_template("account.html")

    if request.method == "POST":
        if session.get("username"):
            password = request.form["deact-password"]
            if users.deactivate_account(password):
                return render_template(
                    "/account.html", message="Account deactivated.")
            else:
                return render_template(
                    "/account.html",
                    message="Account could not be deactivated."
                    )
        else:
            username = request.form["username"]
            password = request.form["react-password"]
            if users.reactivate_account(username, password):
                return render_template(
                    "/account.html", message="Account activated.")
            else:
                return render_template(
                    "/account.html",
                    message="Account could not be activated."
                    )

@app.route("/campaign/<int:id>", methods=["GET"])
def campaign_page(id):
    # Check here if user has access rights
    if campaigns.is_active(id):
        campaign = campaigns.get_campaign_info(id)
        players = campaigns.get_campaign_players(id)
        return render_template(
            "campaign.html", campaign=campaign, players=players)
    return render_template("error.html", error="Campaign could not be loaded")
