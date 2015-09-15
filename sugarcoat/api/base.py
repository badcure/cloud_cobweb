import functools

import flask
import flask_wtf
import wtforms
from requests.packages import urllib3


urllib3.disable_warnings()

class LoginForm(flask_wtf.Form):
    username = wtforms.StringField('Username', [wtforms.validators.Length(min=1, max=25)])
    password = wtforms.PasswordField('Rackspace API Key')

app = flask.Flask(__name__)
app.secret_key = 'thisisdefinitelynotasecretkey'
