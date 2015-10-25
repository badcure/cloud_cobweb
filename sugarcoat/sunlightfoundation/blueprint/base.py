import flask
import string
import flask_wtf
import wtforms
from ..base import APIBase, APIResult
from ..services import get_catalog_api


app = flask.Blueprint('sunlightfoundation', __name__, url_prefix='/sunlightfoundation', static_folder='static',
                      template_folder='./templates')


class LoginInfo(flask_wtf.Form):
    apikey = wtforms.StringField('API Key', [wtforms.validators.Length(min=32, max=32),
                                               wtforms.validators.Regexp('^[a-f0-9]+$')])

def convert_to_related(*args, **kwargs):
    result = dict(links=dict())
    return result


def display_json(response, template_kwargs=None, **kwargs):
    if not template_kwargs:
        template_kwargs = dict()

    try:
        if isinstance(response, APIResult):
            for mime_type, priority in flask.request.accept_mimetypes:
                if mime_type == 'text/html':
                    return flask.Response(flask.render_template(
                        'json_template.html', json_result=response, additional_urls=convert_to_related(
                            api_result=response), **template_kwargs))
                elif mime_type == 'application/json' or mime_type == '*/*':
                    return flask.jsonify(response, **kwargs)
    except IndexError:
        pass

    return flask.jsonify(response, **kwargs)


# noinspection PyUnusedLocal
@app.before_request
def before_request(*args, **kwargs):
    flask.g.sunlightfoundation_apikey = None
    if 'sunlightfoundation_apikey' in flask.session:
        flask.g.sunlightfoundation_apikey = flask.session['sunlightfoundation_apikey']


@app.after_request
def after_request(response):
    return response


@app.route('/login', methods=['GET', 'POST'])
def login_view():
    template_info = dict()

    template_info['message'] = ''
    template_info['form'] = LoginInfo()
    if flask.request.method == 'POST' and template_info['form'].validate_on_submit():
        flask.session['sunlightfoundation_apikey'] = template_info['form'].apikey.data
        return flask.redirect(flask.url_for('{0}.index'.format(app.name)))
    return flask.Response(flask.render_template('{0}/login.html'.format(app.name), **template_info))


@app.route('/logout', methods=['GET'])
def logout_view():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginFormAPI to validate.
    flask.g.sunlightfoundation_apikey = None
    if 'sunlightfoundation_apikey' in flask.session:
        del flask.session['sunlightfoundation_apikey']

    return flask.redirect('/')


@app.route('/', methods=['GET', 'POST'])
def index():
    template_info = dict()

    template_info['message'] = ''

    return flask.Response(flask.render_template('{0}/index.html'.format(app.name), **template_info))


@app.route('/<string:servicename>')
@app.route('/<string:servicename>/<path:new_path>')
def services_view(servicename, new_path=''):
    if flask.g.sunlightfoundation_apikey is None:
        return flask.redirect(flask.url_for('{0}.login_view'.format(app.name)))
    flask.g.list_obj = get_catalog_api(servicename)(flask.g.sunlightfoundation_apikey)
    query_args = {}
    new_path = ''.join(list(filter(lambda x: x in string.printable, new_path)))

    for key, value in flask.request.args.items():
        query_args[key] = value

    request_url = flask.g.list_obj.root_url
    if new_path:
        request_url += '/'+new_path
    flask.g.api_response = flask.g.list_obj.displayable_json_auth_request(url=request_url, params=query_args)
    kwargs = flask.g.list_obj.kwargs_from_request(url=new_path, api_result=flask.g.api_response['result'])

    template_kwargs = dict()
    return display_json(response=flask.g.api_response, template_kwargs=template_kwargs, **kwargs)
