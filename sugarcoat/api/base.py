import functools

import flask
import flask.ext.login
import flask_wtf
import wtforms
from requests.packages import urllib3
import sugarcoat.rackspace_api.identity
import sugarcoat.rackspace_api.root_apis
import sugarcoat.rackspace_api.base


urllib3.disable_warnings()

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


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not isinstance(flask.g.user_info, sugarcoat.rackspace_api.identity.Identity) or not flask.g.user_info.token or flask.g.user_info.token_seconds_left() <= 0:
            return flask.redirect(flask.url_for('login_fn', next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function



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