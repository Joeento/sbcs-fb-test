import facebook
import secrets
import requests
import urlparse
import time
import string
from oauth2client.client import SignedJwtAssertionCredentials
from apiclient import discovery
import httplib2
import flask
from flask import Flask, redirect, request, render_template, url_for
app = Flask(__name__)

OAUTH_DIALOG_API = "https://www.facebook.com/dialog/oauth"
OAUTH_TOKEN_API = "https://graph.facebook.com/oauth/access_token"

NUM_QUERIES = 10

scope = [
	'https://www.googleapis.com/auth/prediction'
]
with open("privatekey.pem") as key_file:
    key = key_file.read()

credentials = SignedJwtAssertionCredentials("718613259106-nprethvrluh9j7ud2gfbkmbs57mllk6a@developer.gserviceaccount.com", key, scope)

def service():
    if hasattr(flask.g, "google_api_service"):
        return flask.g.google_api_service
    http = httplib2.Http()
    http = credentials.authorize(http)
    new_service = discovery.build('prediction', 'v1.6', http=http)
    flask.g.google_api_service = new_service
    print "MADE NEW SERVICE"
    return new_service

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login")
def login():
    redirect_url = url_for('test_login', _external=True)
    return redirect("{}?client_id={}&redirect_uri={}&scope={}".format(OAUTH_DIALOG_API, secrets.CLIENT_ID, redirect_url, "read_stream"))

def _remove_punctuation(text):
    exclude = set(string.punctuation)
    exclude.remove('\'')
    exclude.remove('?')
    exclude.remove('#')
    exclude.remove('-') 
    exclude.remove('!')
    
    text = text.lower()
    new_text = ''
    for ch in text:
        if ch not in exclude:
            new_text += ch
        else: 
            new_text += ' '
    new_text = new_text.replace('?',' ? ').replace('#',' # ').replace('!',' ! ').replace('\n','')
    return new_text

def feature_from_content(content):
    return {
        "input" : {
            "csvInstance": content
        }
    }

def _get_features(post, profile):
    message = post.get(u"message", "") 
    message = _remove_punctuation(message)
    link = _remove_punctuation(post.get(u"link", "NULL"))
    word_count = len(message.split())
    message_tags = post.get(u"message_tags", {})    #  get length somewhere, and check if user is self
    found_person = 0
    for key in message_tags:
        for tag in  message_tags[key]:
            print tag[u"id"], profile[u"id"]
            if tag[u"id"] == profile[u"id"]:
                found_person = 1
    status_type = 1 if post.get(u"status_type", "") == u"shared_story" else 0 
    
    return feature_from_content([
        _remove_punctuation(message),
        link,
        1 if post.get(u"type") == "photo" else 0,   
        status_type,
        found_person,
        len(message_tags),
        len(message.split()),
    ])

def predict(features):
    return service().trainedmodels().predict(project=secrets.PROJECT_ID, body=features, id=secrets.MODEL_ID).execute() 

@app.route("/test_login")
def test_login():
    code = request.args.get('code')
    response = requests.get("{}?client_id={}&redirect_uri={}&client_secret={}&code={}".format(OAUTH_TOKEN_API, secrets.CLIENT_ID, url_for('test_login', _external=True), secrets.APP_SECRET, code))    
    data = urlparse.parse_qs(response.text)
    access_token = data["access_token"][0]
    graph = facebook.GraphAPI(access_token)
    args = {
        "limit": NUM_QUERIES * 5,    # only will run about ten queries through the Google Prediction API per user
    }
    result = graph.request("me/posts", args)
    posts = [x for x in result[u"data"] if u"story" not in x]
    profile = graph.get_object('me')
    predicted_posts = posts[:5]
    features_list = [_get_features(post, profile) for post in predicted_posts]
    predictions = map(predict, features_list)

    return "".join(["<div>{0}@@@@@@@{1}</div>".format(prediction, post) for prediction, post in zip(predictions, predicted_posts)])
    return "".join(["<div>{0}:{1}</div>".format(message, post) for message, post in zip(message_list, posts)])
