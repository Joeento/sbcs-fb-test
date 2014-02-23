import facebook
import secrets
import requests
import urlparse
import time
from flask import Flask, redirect, request, render_template, url_for
app = Flask(__name__)

OAUTH_DIALOG_API = "https://www.facebook.com/dialog/oauth"
OAUTH_TOKEN_API = "https://graph.facebook.com/oauth/access_token"

NUM_QUERIES = 10

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login")
def login():
    redirect_url = url_for('test_login', _external=True)
    return redirect("{}?client_id={}&redirect_uri={}&scope={}".format(OAUTH_DIALOG_API, secrets.CLIENT_ID, redirect_url, "read_stream"))

@app.route("/test_login")
def test_login():
    code = request.args.get('code')
    response = requests.get("{}?client_id={}&redirect_uri={}&client_secret={}&code={}".format(OAUTH_TOKEN_API, secrets.CLIENT_ID, url_for('test_login', _external=True), secrets.APP_SECRET, code))    
    data = urlparse.parse_qs(response.text)
    access_token = data["access_token"][0]
    graph = facebook.GraphAPI(access_token)
    args = {
        "since": int(time.mktime(time.localtime())-24*60*60*200),
        "limit": NUM_QUERIES * 5,    # only will run about ten queries through the Google Prediction API per user
    }
    posts = graph.request("me/feed", args)
    message_list = [post[u"message"] for post in posts[u"data"] if u"message" in post]
    return str(message_list)
