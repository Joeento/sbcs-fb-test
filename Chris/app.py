import facebook
import secrets
import requests
from flask import Flask, redirect, request, render_template
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html', APP_ID=secrets.APP_ID)

@app.route("/_get_cookie")
def get_cookie():
    cookie = request.cookies
    user = facebook.get_user_from_cookie(cookie, secrets.APP_ID, secrets.APP_SECRET)
    graph = facebook.GraphAPI(user['access_token'])
    user = graph.get_object("me")
    posts = graph.request('/me/feed')
    return str(posts)
