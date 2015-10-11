import flask
from sugarcoat.api.base import app
import sugarcoat.api.template_filters
import sugarcoat.rackspacecloud.blueprint.base

app.register_blueprint(sugarcoat.rackspacecloud.blueprint.base.app)
