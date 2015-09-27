import flask
import string
import random
import os

app = flask.Flask(__name__)
app.secret_key = os.environ.get('sugarcoat_secret') or ''.join(random.sample(string.ascii_letters, 24))
