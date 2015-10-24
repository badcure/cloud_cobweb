import flask
import string
import re
import flask_wtf
import wtforms
from ..base import APIBase, APIResult
from ..services import get_catalog_api

app = flask.Blueprint('openweathermap', __name__, url_prefix='/openweathermap', static_folder='static',
                      template_folder='./templates')


class LoginInfo(flask_wtf.Form):
    apikey = wtforms.StringField('API Key', [wtforms.validators.Length(min=32, max=32),
                                               wtforms.validators.Regexp('^[a-f0-9]+$')])

def convert_to_related(*args, **kwargs):
    result = dict()
    return result


def display_json(response, region, template_kwargs=None, **kwargs):
    region = region.lower()

    if not template_kwargs:
        template_kwargs = dict()

    try:
        if isinstance(response, APIResult):
            for mime_type, priority in flask.request.accept_mimetypes:
                if mime_type == 'text/html':
                    return flask.Response(flask.render_template(
                        'json_template.html', json_result=response, additional_urls=convert_to_related(
                            region=region, api_result=response), **template_kwargs))
                elif mime_type == 'application/json' or mime_type == '*/*':
                    return flask.jsonify(response, **kwargs)
    except IndexError:
        pass

    return flask.jsonify(response, **kwargs)


# noinspection PyUnusedLocal
@app.before_request
def before_request(*args, **kwargs):
    flask.g.openweathermap_api = None
    if 'openweathermap_apikey' in flask.session:
        flask.g.openweathermap_api = flask.session['openweathermap_apikey']

@app.after_request
def after_request(response):
    return response


@app.route('/login', methods=['GET', 'POST'])
def login_view():
    template_info = dict()

    template_info['message'] = ''
    template_info['form'] = LoginInfo()
    if flask.request.method == 'POST' and template_info['form'].validate_on_submit():
        print("Loggedin")
        flask.session['openweathermap_apikey'] = template_info['form'].apikey.data
        return flask.redirect(flask.url_for('{0}.index'.format(app.name)))
    return flask.Response(flask.render_template('{0}/login.html'.format(app.name), **template_info))


@app.route('/logout', methods=['GET'])
def logout_view():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginFormAPI to validate.
    flask.g.openweathermap_api = None
    if 'openweathermap_apikey' in flask.session:
        del flask.session['openweathermap_apikey']

    return flask.redirect('/')


@app.route('/', methods=['GET', 'POST'])
def index():
    template_info = dict()

    template_info['message'] = ''

    return flask.Response(flask.render_template('{0}/index.html'.format(app.name), **template_info))


@app.route('/<string:servicename>')
@app.route('/<string:servicename>/<path:new_path>')
def services_view(servicename, new_path=''):
    if flask.g.openweathermap_api is None:
        return flask.redirect(flask.url_for('{0}.login_view'.format(app.name)))
    flask.g.list_obj = get_catalog_api(servicename)
    print(flask.g.list_obj)
    query_args = ''
    new_path = ''.join(list(filter(lambda x: x in string.printable, new_path)))

    for key, value in flask.request.args.items():
        query_args += '&{0}={1}'.format(key, value)
    if query_args:
        query_args = '?'+ query_args[1:]
    new_path += query_args
    flask.g.api_response = flask.g.list_obj.get_api_resource()
    kwargs = flask.g.list_obj.kwargs_from_request(url=new_path, api_result=flask.g.api_response['result'])

    template_kwargs = dict()

    if 'region' in kwargs:
        del kwargs['region']
    return display_json(response=flask.g.api_response, template_kwargs=template_kwargs, **kwargs)
