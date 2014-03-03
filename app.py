from descriptions import descriptions
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
import os.path
import urlparse
from collections import defaultdict
from flask import Flask, redirect, request, render_template, url_for
app = Flask(__name__)

OAUTH_DIALOG_API = "https://www.facebook.com/dialog/oauth"
OAUTH_TOKEN_API = "https://graph.facebook.com/oauth/access_token"

NUM_QUERIES = 10

scope = [
	'https://www.googleapis.com/auth/prediction'
]
with open(os.path.join(os.path.dirname(__file__),"privatekey.pem")) as key_file:
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
    redirect_url = url_for('result', _external=True)
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
    link = post.get(u"link", "NULL")
    if 'NULL' not in link:
        parsed_uri  =  urlparse.urlparse(link)
        link = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    link = _remove_punctuation(link)
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

def sort_predictions(predictions):
    totals_dict = defaultdict(int)
    multi_outputs = [pred[u'outputMulti'] for pred in predictions]
    for multi_output in multi_outputs:
        for output in multi_output:
            totals_dict[output[u'label']] += float(output[u'score'])
    pred_tuples = [(totals_dict[key], key) for key in totals_dict]
    pred_tuples.sort()
    pred_tuples.reverse()
    print pred_tuples
    return [y for x, y in pred_tuples]

def predict(features):
    return service().trainedmodels().predict(project=secrets.PROJECT_ID, body=features, id=secrets.MODEL_ID).execute()

@app.route("/result")
def result():
    code = request.args.get('code')
    response = requests.get("{}?client_id={}&redirect_uri={}&client_secret={}&code={}".format(OAUTH_TOKEN_API, secrets.CLIENT_ID, url_for('result', _external=True), secrets.APP_SECRET, code))
    data = urlparse.parse_qs(response.text)
    if not data:
        return redirect(url_for('index'))
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
    sorted_outputs = sort_predictions(predictions)
    title, commentary = descriptions[sorted_outputs[0]]
    return render_template("result.html", result = title, description = commentary)
    
