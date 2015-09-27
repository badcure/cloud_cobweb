import flask
from .base import app
import sugarcoat.rackspacecloud.blueprint.base

app.register_blueprint(sugarcoat.rackspacecloud.blueprint.base.app)

@app.route('/')
def index():
    return flask.redirect('/rackspacecloud')