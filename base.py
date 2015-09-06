import flask
import flask.ext
import functools
import flask_wtf
import wtforms
from rack_cloud_info.rack_apis.identity import Identity
from requests.packages import urllib3
urllib3.disable_warnings()


class RCIJSONEncoder(flask.json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Identity):
            return o.auth_payload
        return super(RCIJSONEncoder, self).default(o)


class LoginUser(Identity, flask.ext.login.UserMixin):

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


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_info' not in flask.session:
            return flask.redirect(flask.url_for('login_fn', next=flask.request.url))
        flask.g.user_info = Identity(auth_info=flask.session['user_info'])
        if not flask.g.user_info.token:
            return flask.redirect(flask.url_for('login_fn', next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function


@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return LoginUser(user_id)


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
            flask.session['user_info']['_secret_username'] = local_ident.username
            flask.session['user_info']['_secret_apikey'] = local_ident.apikey

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
