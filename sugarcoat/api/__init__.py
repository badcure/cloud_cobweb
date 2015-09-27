import flask
from .base import app
import sugarcoat.rackspace_cloud.blueprint.base

app.register_blueprint(sugarcoat.rackspace_cloud.blueprint.base.app)

@app.route('/')
def index():
    return flask.redirect('/rackspacecloud')