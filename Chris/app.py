import facebook
import secrets
import requests
from flask import Flask, redirect, request, render_template
app = Flask(__name__)

APP_ID = "214736522060342"

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/_get_cookie")
def get_cookie():
    cookie = request.cookies
    user = facebook.get_user_from_cookie(cookie, APP_ID, secrets.APP_SECRET)
    graph = facebook.GraphAPI(user['access_token'])
    user = graph.get_object("me")
    posts = graph.request('/me/feed')
    return str(posts)
