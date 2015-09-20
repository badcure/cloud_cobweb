import flask
import string

import flask.ext
from requests.packages import urllib3
import sugarcoat.rackspace_api.root_apis
import sugarcoat.rackspace_api.identity
from sugarcoat.api.base import app
import sugarcoat.api.base
import sugarcoat.api.filters
import sugarcoat.rackspace_api.base

urllib3.disable_warnings()


@app.route('/cloudIdentity/all', methods=['GET', 'POST'])
@app.route('/cloudIdentity/all/', methods=['GET', 'POST'])
@app.route('/cloudIdentity/all/<path:new_path>', methods=['GET', 'POST'])
def identity_request(new_path=''):

    method = flask.request.method
    request_data = flask.request.data
    additional_headers = {}
    for query_name, query_value in flask.request.args.items():
        if 'sugarcoat_method' in query_name:
            method = query_value
        elif 'sugarcoat_body' in query_name:
            request_data = query_value
        elif 'sugarcoat_header' in query_name:
            new_header = '_'.join(query_name.split('_')[2:])
            additional_headers[new_header] = query_value

    flask.g.list_obj = sugarcoat.rackspace_api.root_apis.IdentityAPI(flask.g.user_info)
    query_args = ''
    new_path = ''.join(list(filter(lambda x: x in string.printable, new_path)))

    for key, value in flask.request.args.items():
        if 'sugarcoat_' in key:
            continue
        query_args += '&{0}={1}'.format(key, value)
    if query_args:
        query_args = '?' + query_args[1:]
    new_path += query_args
    template_kwargs = dict()
    template_kwargs['region'] = 'all'
    form = sugarcoat.api.base.LoginForm(prefix='login')
    if flask.request.method == 'POST' and form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class

        request_data = {
            "auth": {
                "RAX-KSKEY:apiKeyCredentials": {
                    "username": form.username.data,
                    "apiKey": form.password.data
                }
            }
        }

    flask.g.api_response = flask.g.list_obj.get_api_resource(
        region='all', initial_url_append='/' + new_path, method=method, data=request_data,
        additional_headers=additional_headers)
    if flask.request.method == 'POST' and form.validate_on_submit():
        flask.g.api_response['request_body'] = flask.g.api_response['request_body'].replace(
            '"'+form.password.data+'"', '"<masked>"')
        if flask.g.api_response['status_code'] == 200:
            flask.session['user_info'] = flask.g.api_response['result']
            flask.g.user_info = sugarcoat.rackspace_api.identity.Identity(flask.session['user_info'])
    kwargs = flask.g.list_obj.kwargs_from_request(url=new_path, api_result=flask.g.api_response['result'], region='all')

    if 'region' in kwargs:
        del kwargs['region']
    return sugarcoat.api.filters.display_json(response=flask.g.api_response, template_kwargs=template_kwargs,
                                              region='all', **kwargs)


@app.route('/<string:service_name>/<string:region>')
@app.route('/<string:service_name>/<string:region>/')
@app.route('/<string:service_name>/<string:region>/<path:new_path>')
def service_catalog_list(service_name, region, new_path=''):
    flask.g.list_obj = sugarcoat.rackspace_api.root_apis.get_catalog_api(service_name)(flask.g.user_info)
    query_args = ''
    new_path = ''.join(list(filter(lambda x: x in string.printable, new_path)))

    for key, value in flask.request.args.items():
        query_args += '&{0}={1}'.format(key, value)
    if query_args:
        query_args = '?' + query_args[1:]
    new_path += query_args
    flask.g.api_response = flask.g.list_obj.get_api_resource(region=region, initial_url_append='/' + new_path)
    kwargs = flask.g.list_obj.kwargs_from_request(url=new_path, api_result=flask.g.api_response['result'],
                                                  region=region)

    template_kwargs = dict()
    template_kwargs['region'] = region
    template_kwargs['tenant_id'] = flask.g.user_info.tenant_id

    if 'region' in kwargs:
        del kwargs['region']
    return sugarcoat.api.filters.display_json(response=flask.g.api_response, tenant_id=flask.g.user_info.tenant_id,
                                              template_kwargs=template_kwargs, region=region, **kwargs)


@app.route('/auth_token')
def auth_token_view():
    return flask.json.jsonify(flask.g.user_info.display_safe())


@app.route('/refresh_auth', methods=['GET'])
def refresh_auth_fn():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    flask.session['user_info'] = flask.g.user_info.refresh_auth()
    return flask.redirect('/')


@app.route('/logout', methods=['GET'])
def logout_fn():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    del flask.session['user_info']
    flask.g.user_info = None
    return flask.redirect('/')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = sugarcoat.api.base.LoginForm(prefix='login')
    template_info = dict()
    template_info['message'] = ''
    template_info['form'] = form
    return flask.Response(flask.render_template('index.html', **template_info))


if __name__ == '__main__':
    app.run(host="0.0.0.0")
