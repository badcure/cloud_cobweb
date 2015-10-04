import flask
import string
import random
import os

app = flask.Flask(__name__)
ENVIRON_SECRETKEY_NAME = 'sugarcoat_secret'
if ENVIRON_SECRETKEY_NAME in os.environ:
    print("Using environment {0} for secret_key".format(ENVIRON_SECRETKEY_NAME))
    app.secret_key = os.environ[ENVIRON_SECRETKEY_NAME]
else:
    print("Randomly generating secret key")
    app.secret_key = ''.join(random.sample(string.ascii_letters, 24))
app.jinja_options['extensions'].append('jinja2.ext.do')

@app.errorhandler(404)
def page_not_found(e):
    return flask.redirect('/')