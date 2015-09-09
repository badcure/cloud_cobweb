import functools
import pprint

import flask
import flask.ext.login
import flask_wtf
import wtforms
from requests.packages import urllib3
import sugarcoat.rackspace_api.identity
import sugarcoat.rackspace_api.root_apis
import sugarcoat.rackspace_api.base
import re


urllib3.disable_warnings()

def display_json(response, template_kwargs=None, additional_urls=None, **kwargs):
    if not template_kwargs:
        template_kwargs = dict()
    if not additional_urls:
        additional_urls = list()

    try:
        if isinstance(response, sugarcoat.rackspace_api.base.RackAPIResult):
            for mime_type, priority in flask.request.accept_mimetypes:
                if mime_type == 'text/html':
                    return flask.Response(flask.render_template(
                            'json_template.html', json_result=response, additional_urls=additional_urls, **template_kwargs))
                elif mime_type == 'application/json' or mime_type == '*/*':
                    return flask.jsonify(response, **kwargs)
    except IndexError:
        pass

    return flask.jsonify(response, **kwargs)

class RCIJSONEncoder(flask.json.JSONEncoder):
    def default(self, o):
        if isinstance(o, sugarcoat.rackspace_api.identity.Identity):
            return o.auth_payload
        return super().default(o)


class LoginUser(sugarcoat.rackspace_api.identity.Identity, flask.ext.login.UserMixin):

    def is_authenticated(self):
        return bool(self.token)

    def is_anonymous(self):
        return not self.is_authenticated()

    def is_active(self):
        return True

    def get_id(self):
        return self._username


class LoginForm(flask_wtf.Form):
    username = wtforms.StringField('Username', [wtforms.validators.Length(min=1, max=25)])
    password = wtforms.PasswordField('Rackspace API Key')


app = flask.Flask(__name__)
app.secret_key = 'thisisdefinitelynotasecretkey'
login_manager = flask.ext.login.LoginManager()
login_manager.init_app(app)
app.json_encoder = RCIJSONEncoder


@app.template_filter('pprint_obj')
def pprint_obj(obj):
    return pprint.pformat(obj)

@app.template_filter('convert_to_urls')
def convert_to_urls(result):
    print(flask.g.user_info)
    if not isinstance(result, str):
        result = str(pprint.pformat(result))
    if not flask.g.user_info:
        return result

    for url, replace_url_info in flask.g.user_info.url_to_catalog_dict():
        match_url = re.compile("'({0})([^']*)'".format(url))
        if len(replace_url_info) == 3:
            result = match_url.sub(r"<a href='/{0}/{1}/{2}\2'>\1\2</a>".format(*replace_url_info), result)
        else:
            result = match_url.sub(r"<a href='/{0}/{1}\2'>\1\2</a>".format(*replace_url_info), result)

    return pprint.pformat(result)

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not isinstance(flask.g.user_info, sugarcoat.rackspace_api.identity.Identity) or not flask.g.user_info.token or flask.g.user_info.token_seconds_left() <= 0:
            return flask.redirect(flask.url_for('login_fn', next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function


@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return LoginUser(user_id)

@app.before_request
def before_request(*args, **kwargs):
    if 'user_info' in flask.session:
        flask.g.user_info = sugarcoat.rackspace_api.identity.Identity(auth_info=flask.session['user_info'])
    else:
        flask.g.user_info = None


@app.after_request
def after_request(response):
    return response


@app.route('/login', methods=['GET', 'POST'])
def login_fn():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm(prefix='login')
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        local_ident = LoginUser(form.username.data, form.password.data)
        if local_ident.token:
            flask.ext.login.login_user(local_ident)
            flask.session['user_info'] = local_ident.auth_payload

            flask.flash('Logged in successfully.')

            next_url = flask.request.args.get('next')
            return flask.redirect(next_url or flask.url_for('index'))
        else:
            flask.flash('Invalid login.')

    return flask.render_template('login.html', form=form, logged_in=False)



@app.route('/logout', methods=['GET'])
def logout_fn():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    flask.session['user_info'] = None
    flask.g.user_info = None
    return flask.redirect('/')
