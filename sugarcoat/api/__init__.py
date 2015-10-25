import flask
from sugarcoat.api.base import app
import sugarcoat.api.template_filters
import sugarcoat.rackspacecloud.blueprint.base
import sugarcoat.openweathermap.blueprint.base
import sugarcoat.sunlightfoundation.blueprint.base

app.register_blueprint(sugarcoat.rackspacecloud.blueprint.base.app)
app.register_blueprint(sugarcoat.openweathermap.blueprint.base.app)
app.register_blueprint(sugarcoat.sunlightfoundation.blueprint.base.app)
