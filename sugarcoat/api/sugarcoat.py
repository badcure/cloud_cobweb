import flask
import string

import flask.ext
from requests.packages import urllib3
import sugarcoat.rackspace_api.root_apis

from sugarcoat.api.base import app, login_required
import sugarcoat.api.filters

urllib3.disable_warnings()


@app.route('/<string:servicename>/<string:region>')
@app.route('/<string:servicename>/<string:region>/')
@app.route('/<string:servicename>/<string:region>/<path:new_path>')
@login_required
def service_catalog_list(servicename,region,new_path=''):
    flask.g.list_obj = sugarcoat.rackspace_api.root_apis.get_catalog_api(servicename)(flask.g.user_info)
    query_args = ''
    new_path = ''.join(list(filter(lambda x: x in string.printable, new_path)))

    for key, value in flask.request.args.items():
        query_args += '&{0}={1}'.format(key, value)
    if query_args:
        query_args = '?'+ query_args[1:]
    new_path += query_args
    flask.g.api_response = flask.g.list_obj.get_api_resource(region=region, initial_url_append='/' + new_path)
    kwargs = flask.g.list_obj.kwargs_from_request(url=new_path, api_result=flask.g.api_response['result'], region=region)
    tenant_id = flask.g.user_info.tenant_id

    template_kwargs = dict()
    template_kwargs['region'] = region
    template_kwargs['tenant_id'] = flask.g.user_info.tenant_id

    return sugarcoat.api.filters.display_json(response=flask.g.api_response, new_path=new_path, tenant_id=tenant_id, template_kwargs=template_kwargs, region=region, **kwargs)


@app.route('/auth_token')
@login_required
def auth_token_view():
    return flask.json.jsonify(flask.g.user_info.display_safe())


@app.route('/refresh_auth', methods=['GET'])
@login_required
def refresh_auth_fn():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    flask.session['user_info'] = flask.g.user_info.refresh_auth()
    return flask.redirect('/')


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    message = ''
    return flask.Response(flask.render_template(
        'index.html', message=message, roles=flask.g.user_info.roles(),
        service_catalog=flask.g.user_info.service_catalog(), expire_time=flask.g.user_info.token_seconds_left(),
        username=flask.g.user_info.username))


if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
