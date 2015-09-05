import flask
from functools import wraps
from flask_wtf import Form
from flask.ext import login
from flask.json import jsonify, JSONEncoder
from flask import request
from wtforms import StringField, PasswordField, validators
from rack_cloud_info.rack_apis.identity import Identity, UserAPI
from rack_cloud_info.rack_apis.nextgen_servers import ServersAPI, ImagesAPI
from rack_cloud_info.rack_apis.monitoring import MonitoringAPI
from rack_cloud_info.rack_apis.backup import BackupAPI

app = flask.Flask(__name__)
app.secret_key = 'thisisdefinitelynotasecretkey'
login_manager = login.LoginManager()
login_manager.init_app(app)

from requests.packages import urllib3
urllib3.disable_warnings()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_info' not in flask.session:
            return flask.redirect(flask.url_for('login', next=request.url))
        flask.g.user_info = Identity(auth_info=flask.session['user_info'])
        if not flask.g.user_info.token:
            return flask.redirect(flask.url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


class RCIJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Identity):
            return o._auth
        return super(RCIJSONEncoder, self).default(o)

app.json_encoder = RCIJSONEncoder

DEFAULT_REGION = 'ORD'
class LoginUser(Identity, login.UserMixin):

    def is_authenticated(self):
        return bool(self.token)

    def is_anonymous(self):
        return not self.is_authenticated()

    def is_active(self):
        return True

    def get_id(self):
        return self._username


class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=25)])
    password = PasswordField('Rackspace API Key')


@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return LoginUser(user_id)


@app.route('/servers')
@login_required
def server_list():
    api_type = ServersAPI
    region = flask.request.args.get('region', DEFAULT_REGION)
    should_populate = flask.request.args.get('populate', False)
    api_obj = api_type(flask.g.user_info)
    list_obj = api_obj.get_list(region)
    if should_populate:
        list_obj.populate_info(flask.g.user_info, region=region)

    return jsonify(request=list_obj)


@app.route('/images')
@login_required
def image_list():
    list_obj = ImagesAPI
    region = flask.request.args.get('region', DEFAULT_REGION)
    should_populate = flask.request.args.get('populate', False)
    images = list_obj(flask.g.user_info).get_list(region)
    if should_populate:
        images.populate_info(flask.g.user_info)

    return jsonify(request=images)


@app.route('/users')
@login_required
def user_list():
    list_obj = UserAPI
    should_populate = request.args.get('populate', False)
    images = list_obj(flask.g.user_info).get_list()
    if should_populate:
        images.populate_info(flask.g.user_info)

    return jsonify(request=images)


@app.route('/monitoring')
@login_required
def monitoring_list():
    list_obj = MonitoringAPI(flask.g.user_info)
    should_populate = request.args.get('populate', False)

    result_list = []
    result_list.append(list_obj.get_list(initial_url_append='/account'))
    result_list.append(list_obj.get_list(initial_url_append='/entities'))
    result_list.append(list_obj.monitoring_agent_list())
    if should_populate:
        result_list[-1].populate_info(identity_obj=flask.g.user_info)
    result_list.append(list_obj.get_list(initial_url_append='/views/overview'))

    return jsonify(request=result_list)


@app.route('/backups')
@login_required
def backups_list():
    list_obj = BackupAPI(flask.g.user_info)
    should_populate = request.args.get('populate', False)

    result_list = list()
    result_list.append(list_obj.backup_agents_list())

    return jsonify(request=result_list)


@app.route('/auth_token')
@login_required
def auth_token_view():
    return jsonify(flask.g.user_info.display_safe())


@app.route('/login', methods=['GET', 'POST'])
def login_fn():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm(prefix='login')
    print "here"
    print form.validate_on_submit()
    print form.is_submitted()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        local_ident = LoginUser(form.username.data, form.password.data)
        if local_ident.token:
            login.login_user(local_ident)
            flask.session['user_info'] = local_ident

            flask.flash('Logged in successfully.')

            next = flask.request.args.get('next')
            return flask.redirect(next or flask.url_for('index'))
        else:
            flask.flash('Invalid login.')

    return flask.render_template('login.html', form=form, logged_in=False)


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    message = ''
    return flask.Response(flask.render_template('index.html', message=message))

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
