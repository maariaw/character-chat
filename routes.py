from app import app
from db import db
from flask import redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import users, campaigns, chats

@app.route("/")
def index():
    campaign_list = campaigns.get_campaigns()
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
    if session.get("role", 0) != 2:
        return render_template(
            "error.html", error="Log in as GM to create a campaign")
    campaign_list = campaigns.get_campaigns()
    if request.method == "GET":
        return render_template("newcampaign.html", campaigns=campaign_list)
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        title = request.form["title"]
        password = request.form["password"]
        if len(title) < 1:
            return render_template(
                "newcampaign.html",
                error="Title cannot be empty",
                campaigns=campaign_list
                )
        if len(title) > 100:
            return render_template(
                "newcampaign.html",
                error="Title is too long",
                campaigns=campaign_list
                )
        if campaigns.is_duplicate(title, session.get("user_id", 0)):
            return render_template(
                "newcampaign.html",
                error="You cannot create two campaigns with the same title",
                campaigns=campaign_list
                )
        if len(password) < 8:
            return render_template(
                "newcampaign.html",
                error="Password is too short",
                campaigns=campaign_list
                )
        if len(password) > 32:
            return render_template(
                "newcampaign.html",
                error="Password is too long",
                campaigns=campaign_list
                )
        id = campaigns.create_campaign(title, password)
        url = "/campaign/" + str(id)
        return redirect(url)

@app.route("/account-status", methods=["POST", "GET"])
def change_account_status():
    campaign_list = campaigns.get_campaigns()
    if request.method == "GET":
        return render_template("account.html", campaigns=campaign_list)
    if request.method == "POST":
        username = session.get("username")
        if username:
            password = request.form["deact-password"]
            if users.deactivate_account(password):
                return render_template(
                    "/index.html",
                    message="Account deactivated.",
                    campaigns=campaign_list
                    )
            else:
                return render_template(
                    "/account.html",
                    error="Account could not be deactivated.",
                    campaigns=campaign_list
                    )
        else:
            username = request.form["username"]
            password = request.form["react-password"]
            if users.reactivate_account(username, password):
                return render_template(
                    "/index.html",
                    message="Account activated.",
                    campaigns=campaign_list
                    )
            else:
                return render_template(
                    "/account.html",
                    error="Account could not be activated.",
                    campaigns=campaign_list
                    )

@app.route("/campaign/<int:id>", methods=["GET", "POST"])
def campaign_page(id):
    campaign_list = campaigns.get_campaigns()
    user_id = session.get("user_id", 0)
    if not campaigns.has_access(id, user_id):
        return render_template(
            "error.html",
            error="You don't have access to this campaign",
            campaigns=campaign_list
            )
    if not campaigns.is_active(id):
        return render_template(
            "error.html",
            error="Campaign could not be loaded",
            campaigns=campaign_list
            )
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
            campaigns=campaign_list
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
    campaign_list = campaigns.get_campaigns()
    if not campaigns.is_creator(id, user_id):
        return render_template(
            "error.html", error="No authority", campaigns=campaign_list)
    campaign = campaigns.get_campaign_info(id)
    players = campaigns.get_campaign_players(id)
    if request.method == "GET":
        return render_template(
            "delete.html",
            campaign=campaign,
            players=players,
            id=id,
            campaigns=campaign_list
            )
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        password = request.form["password"]
        if campaigns.check_password(id, password):
            if campaigns.deactivate_campaign(id):
                return redirect("/")
            else:
                return render_template(
                    "error.html",
                    error="Campaign could not be deleted",
                    campaigns=campaign_list
                    )
        return render_template(
                "delete.html",
                error="Campaign password was incorrect",
                campaign=campaign,
                players=players,
                id=id,
                campaigns=campaign_list
                )

@app.route("/campaigns", methods=["GET"])
def list_campaigns():
    campaign_list = campaigns.get_campaigns()
    user_role = session.get("role", 0)
    if user_role == 0:
        return redirect("/")
    search = request.args.get("search_term", None)
    gm_checked = False
    if not search:
        message = None
        show_campaigns = campaigns.get_all()
    else:
        search_type = request.args["search_by"]
        if search_type == "title":
            message = "Showing campaigns with \"" + search + "\" in title"
            show_campaigns = campaigns.search_by_title(search)
        else:
            gm_checked = True
            message = "Showing campaigns with \"" + search + "\" in GM name"
            gm_id_list = users.search_gm_ids(search)
            show_campaigns = campaigns.get_by_gm_ids(gm_id_list)
    return render_template(
        "listing.html",
        show_campaigns=show_campaigns,
        message=message,
        gm_checked=gm_checked,
        campaigns=campaign_list
        )

@app.route("/campaign/<int:id>/join", methods=["GET", "POST"])
def join_campaign(id):
    campaign_list = campaigns.get_campaigns()
    user_id = session.get("user_id", 0)
    user_role = session.get("role", 0)
    if user_role != 1:
            return render_template(
                "error.html",
                error="You need to be logged in as player to join a campaign",
                campaigns=campaign_list
                )
    url = "/campaign/" + str(id)
    this_campaign = campaigns.get_campaign_info(id)
    if request.method == "GET":
        if campaigns.has_access(id, user_id):
            return redirect(url)
        if this_campaign:
            return render_template(
                "join.html", campaign=this_campaign, campaigns=campaign_list)
        else:
            return render_template(
                "error.html",
                error="Could not find the campaign you were looking for",
                campaigns=campaign_list
                )
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        password = request.form["password"]
        if password and campaigns.check_password(id, password):
            campaigns.add_player(id, user_id)
            return redirect(url)
        else:
            return render_template(
                "join.html",
                error="Incorrect password",
                campaign=this_campaign,
                campaigns=campaign_list
                )

@app.route("/campaign/<int:id>/leave", methods=["GET", "POST"])
def leave_campaign(id):
    campaign_list = campaigns.get_campaigns()
    user_id = session.get("user_id", 0)
    if not campaigns.has_access(id, user_id):
        return render_template(
            "error.html",
            error="You don't have access to this campaign",
            campaigns=campaign_list
            )
    this_campaign = campaigns.get_campaign_info(id)
    players = campaigns.get_campaign_players(id)
    if request.method == "GET":
        return render_template(
            "leave.html",
            campaign=this_campaign,
            players=players,
            campaigns=campaign_list)
    if request.method == "POST":
        username = session.get("username")
        password = request.form["password"]
        if users.check_password(username, password):
            if campaigns.remove_user_from_campaign(id, user_id):
                return redirect("/")
            else:
                return render_template(
                    "error.html",
                    error="Could not remove player from campaign",
                    campaigns=campaign_list
                    )
        else:
            return render_template(
                    "leave.html",
                    campaign=this_campaign,
                    players=players,
                    error="Password was incorrect",
                    campaigns=campaign_list)

@app.route("/campaign/<int:id>/create-chat", methods=["GET", "POST"])
def create_chat(id):
    campaign_list = campaigns.get_campaigns()
    user_id = session.get("user_id", 0)
    if not campaigns.is_creator(id, user_id):
        return render_template(
            "error.html", error="No authority", campaigns=campaign_list)
    campaign = campaigns.get_campaign_info(id)
    players = campaigns.get_campaign_players(id)
    if request.method == "GET":
        return render_template(
            "newchat.html",
            campaign=campaign,
            players=players,
            id=id,
            campaigns=campaign_list
            )
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        title = request.form["title"]
        if len(title) < 1:
            return render_template(
                "newchat.html",
                error="Title cannot be empty",
                campaign=campaign,
                players=players,
                id=id,
                campaigns=campaign_list
                )
        if len(title) > 300:
            return render_template(
                "newchat.html",
                error="Title is too long",
                campaigns=campaign_list
                )
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
    campaign_list = campaigns.get_campaigns()
    user_id = session.get("user_id")
    if not user_id:
        return render_template(
            "error.html",
            error="You need to be logged in to chat",
            campaigns=campaign_list
            )
    if request.method == "GET":
        chat_grouping = []
        campaign_ids = [campaign.id for campaign in campaign_list]
        for campaign_info in campaign_list:
            campaign = {}
            campaign["info"] = campaign_info
            all_chats = chats.get_campaign_chats(campaign_info.id)
            campaign["chats"] = [
                chat for chat in all_chats
                if chat["closed"] == 0
                and session["username"] in chat["chatters"]
                ]
            chat_grouping.append(campaign)
        return render_template(
            "chatlist.html",
            chat_grouping=chat_grouping,
            campaigns=campaign_list
            )

@app.route("/chats/leave/<int:id>", methods=["GET", "POST"])
def leave_chat(id):
    campaign_list = campaigns.get_campaigns()
    user_id = session.get("user_id")
    if not user_id or not chats.user_in_chat(id, user_id):
        return render_template(
            "error.html",
            error="You don't have access to this chat",
            campaigns=campaign_list
            )
    chat = chats.get_chat(id)
    campaign = campaigns.get_campaign_info(chat["campaign_id"])
    if request.method == "GET":
        return render_template(
            "chat.html", chat=chat, campaign=campaign, campaigns=campaign_list)
    if request.method == "POST":
        users.check_csrf(request.form["csrf_token"])
        leave = request.form.get("leave", 0)
        if leave:
            chats.remove_user_from_chat(user_id, id)
        return redirect("/chats")

@app.route("/terms-of-use", methods=["GET"])
def terms():
    campaign_list = campaigns.get_campaigns()
    return render_template("terms.html", campaigns=campaign_list)
