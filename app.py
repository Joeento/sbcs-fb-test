import facebook
import secrets
import flask
import requests
import urlparse
from flask import Flask, redirect, request, render_template, url_for
app = Flask(__name__)

OAUTH_DIALOG_API = "https://www.facebook.com/dialog/oauth"
OAUTH_TOKEN_API = "https://graph.facebook.com/oauth/access_token"


# A user will click login, amd be taken to /login 
@app.route("/")
def index():
    return render_template("index.html")

# A user will be redirected to the fb login page and then redirected to /result
@app.route("/login")
def login():
    redirect_url = url_for('result', _external=True)
    return redirect("{}?client_id={}&redirect_uri={}&scope={}".format(OAUTH_DIALOG_API, secrets.CLIENT_ID, redirect_url, "read_stream"))

# "code" will be extracted from the query string, the graph api will be initilized, an access token will be retrieved, said access token will be replaced with long-term access token, and then stored in database.
@app.route("/result")
def result():
    code = request.args.get('code')
    response = requests.get("{}?client_id={}&redirect_uri={}&client_secret={}&code={}".format(OAUTH_TOKEN_API, secrets.CLIENT_ID, url_for('result', _external=True), secrets.APP_SECRET, code))
    data = urlparse.parse_qs(response.text)
    if not data:
        return redirect('/error')
    access_token = data["access_token"][0]
    graph = facebook.GraphAPI(access_token)
    print "Token: "+access_token
    return render_template("result.html")

