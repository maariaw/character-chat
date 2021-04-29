from app import app
from db import db
from flask import redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import users, campaigns, chats

@app.route("/")
def index():
    role = session.get("role", 0)
    if role == 2:
        campaign_list = campaigns.get_created_campaigns(
            session.get("user_id", 0))
    elif role == 1:
        campaign_list = campaigns.get_joined_campaigns(
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

@app.route("/create-campaign", methods=[ "GET", "POST"])
def create_campaign():
    if request.method == "GET":
        return render_template("newcampaign.html")
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        title = request.form["title"]
        password = request.form["password"]
        if len(title) < 0:
            return render_template("newcampaign.html", error="Title cannot be empty")
        if len(title) > 100:
            return render_template("newcampaign.html", error="Title is too long")
        if campaigns.is_duplicate(title, session.get("user_id", 0)):
            return render_template(
                "newcampaign.html",
                error="You cannot create two campaigns with the same title"
                )
        if len(password) < 8:
            return render_template(
                "newcampaign.html", error="Password is too short")
        if len(password) > 32:
            return render_template(
                "newcampaign.html", error="Password is too long")
        campaigns.create_campaign(title, password)
        return redirect("/")

@app.route("/account-status", methods=["POST", "GET"])
def change_account_status():
    if request.method == "GET":
        return render_template("account.html")

    if request.method == "POST":
        username = session.get("username")
        if username:
            password = request.form["deact-password"]
            if users.deactivate_account(username, password):
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

@app.route("/campaign/<int:id>", methods=["GET", "POST"])
def campaign_page(id):
    user_id = session.get("user_id", 0)
    if not campaigns.has_access(id, user_id):
        return render_template(
            "error.html", error="You don't have access to this campaign")
    if not campaigns.is_active(id):
        return render_template(
            "error.html", error="Campaign could not be loaded")
    if request.method == "GET":
        campaign = campaigns.get_campaign_info(id)
        players = campaigns.get_campaign_players(id)
        chatlist = chats.get_campaign_chats(id)
        return render_template(
            "campaign.html",
            campaign=campaign,
            players=players,
            id=id,
            chatlist=chatlist,
            )
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        text = request.form["text"]
        chat_id = request.form["chat_id"]
        if 0 < len(text) <= 1000:
            chats.add_message(chat_id, text)
        close = request.form.get("close", 0)
        if close:
            chats.close(chat_id)
        return redirect(request.form["route"])

@app.route("/campaign/<int:id>/delete", methods=["GET", "POST"])
def delete_campaign(id):
    user_id = session.get("user_id", 0)
    if not campaigns.is_creator(id, user_id):
        return render_template(
            "error.html", error="No authority")
    if request.method == "GET":
        campaign = campaigns.get_campaign_info(id)
        players = campaigns.get_campaign_players(id)
        return render_template(
            "delete.html",
            campaign=campaign,
            players=players,
            id=id,
            )
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        password = request.form["password"]
        if campaigns.check_password(id, password):
            if campaigns.deactivate_campaign(id):
                return redirect("/")
            else:
                return render_template(
                    "error.html", error="Campaign could not be deleted")
        return render_template(
                "error.html", error="Campaign password was incorrect")

@app.route("/campaigns", methods=["GET"])
def list_campaigns():
    user_role = session.get("role", 0)
    if user_role == 0:
        return render_template("error.html", error="Log in to see campaigns")
    search = request.args.get("search_term", None)
    gm_checked = False
    if not search:
        message = None
        campaign_list = campaigns.get_all()
    else:
        search_type = request.args["search_by"]
        if search_type == "title":
            message = "Showing campaigns with \"" + search + "\" in title"
            campaign_list = campaigns.search_by_title(search)
        else:
            gm_checked = True
            message = "Showing campaigns with \"" + search + "\" in GM name"
            gm_id_list = users.search_gm_ids(search)
            campaign_list = campaigns.get_by_gm_ids(gm_id_list)
    return render_template(
        "listing.html",
        campaigns=campaign_list,
        message=message,
        gm_checked=gm_checked,
        )

@app.route("/campaign/<int:id>/join", methods=["GET", "POST"])
def join_campaign(id):
    user_id = session.get("user_id", 0)
    user_role = session.get("role", 0)
    if user_role != 1:
            return render_template(
                "error.html",
                error="You need to be logged in as player to join a campaign")
    url = "/campaign/" + str(id)
    if request.method == "GET":
        if campaigns.has_access(id, user_id):
            return redirect(url)
        this_campaign = campaigns.get_campaign_info(id)
        return render_template("join.html", campaign=this_campaign)
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        password = request.form["password"]
        if campaigns.check_password(id, password):
            campaigns.add_player(id, user_id)
            return redirect(url)

@app.route("/campaign/<int:id>/leave", methods=["GET", "POST"])
def leave_campaign(id):
    user_id = session.get("user_id", 0)
    if not campaigns.has_access(id, user_id):
        return render_template(
            "error.html", error="You don't have access to this campaign")
    if request.method == "GET":
        this_campaign = campaigns.get_campaign_info(id)
        return render_template("leave.html", campaign=this_campaign)
    if request.method == "POST":
        username = session.get("username")
        password = request.form["password"]
        if users.check_password(username, password):
            if campaigns.remove_user_from_campaign(id, user_id):
                return redirect("/")
            else:
                return render_template(
                    "error.html",
                    error="Could not remove player from campaign")
        else:
            return render_template(
                    "error.html", error="Password was incorrect")

@app.route("/campaign/<int:id>/create-chat", methods=["GET", "POST"])
def create_chat(id):
    user_id = session.get("user_id", 0)
    if not campaigns.is_creator(id, user_id):
        return render_template(
            "error.html", error="No authority")
    if request.method == "GET":
        campaign = campaigns.get_campaign_title(id)
        players = campaigns.get_campaign_players(id)
        return render_template(
            "newchat.html", campaign=campaign, players=players, id=id)
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        title = request.form["title"]
        if len(title) < 0:
            return render_template("newchat.html", error="Title cannot be empty")
        if len(title) > 300:
            return render_template("newchat.html", error="Title is too long")
        private = request.form.get("private", 0)
        chat_id = chats.create_chat(id, title, private)
        chats.add_chatter(chat_id, user_id)
        chatters = request.form.getlist("chatter")
        for chatter in chatters:
            chatter_id = users.get_user_id(chatter)
            if chatter_id:
                chats.add_chatter(chat_id, chatter_id)
        return redirect("/campaign/" + str(id))

@app.route("/chats", methods=["GET", "POST"])
def active_chats():
    user_id = session.get("user_id")
    if not user_id:
        return render_template(
            "error.html", error="You need to be logged in to chat")
    if request.method == "GET":
        campaign_list = []
        user_campaigns = campaigns.get_joined_campaigns(user_id)
        campaign_ids = [campaign.id for campaign in user_campaigns]
        for campaign_info in user_campaigns:
            campaign = {}
            campaign["info"] = campaign_info
            all_chats = chats.get_campaign_chats(campaign_info.id)
            campaign["chats"] = [
                chat for chat in all_chats
                if chat["closed"] == 0
                and session["username"] in chat["chatters"]
                ]
            campaign_list.append(campaign)
        return render_template("chatlist.html", campaign_list=campaign_list)
