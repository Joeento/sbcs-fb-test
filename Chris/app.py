import facebook
import secrets
import requests
import urlparse
import time
from flask import Flask, redirect, request, render_template, url_for
app = Flask(__name__)

OAUTH_DIALOG_API = "https://www.facebook.com/dialog/oauth"
OAUTH_TOKEN_API = "https://graph.facebook.com/oauth/access_token"

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
        "since": int(time.mktime(time.localtime())-24*60*60*600),
        "limit": 200,
    }
    posts = graph.request("me/feed", args)
    return str(len(posts[u"data"]))  
