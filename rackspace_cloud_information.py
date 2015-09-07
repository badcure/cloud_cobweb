import flask
import flask.ext
import rack_cloud_info.rack_apis
import rack_cloud_info.rack_apis.root_apis
from base import app, login_required, display_json

from requests.packages import urllib3
urllib3.disable_warnings()

@app.route('/cloudFeeds/<string:region>/<string:title>')
@app.route('/cloudFeeds/<string:region>/<string:title>/')
@app.route('/cloudFeeds/<string:region>/<string:title>/<path:new_path>')
def cloudfeeds_list(region, title, new_path=''):
    list_obj = rack_cloud_info.rack_apis.root_apis.get_catalog_api('cloudFeeds')(flask.g.user_info)
    list_obj.feed_region = region
    list_obj.feed_task = title
    query_args = ''
    for key, value in flask.request.args.items():
        query_args += '&{0}={1}'.format(key, value)
    if query_args:
        query_args = '?'+ query_args[1:]
    new_path += query_args

    if 'cloudFeeds_'+region not in flask.session:
        result = list_obj.get_list(region=region, initial_url_append='/')[0]
        flask.session['cloudFeeds_'+region] = result['result']
    list_obj.feed_list_payload = flask.session['cloudFeeds_'+region]

    result = dict()
    kwargs = dict()
    result['response']=list_obj.get_list(region=region, initial_url_append='/' + new_path)
    result['response'][0].additional_url_list = list_obj.custom_urls()
    result['template_kwargs'] = list_obj.pprint_html_url_results(region=region, **kwargs)

    return display_json(**result)

@app.route('/<string:servicename>/<string:region>')
@app.route('/<string:servicename>/<string:region>/')
@app.route('/<string:servicename>/<string:region>/<path:new_path>')
@login_required
def service_catalog_list(servicename,region,new_path=''):
    list_obj = rack_cloud_info.rack_apis.root_apis.get_catalog_api(servicename)(flask.g.user_info)
    query_args = ''
    for key, value in flask.request.args.items():
        query_args += '&{0}={1}'.format(key, value)
    if query_args:
        query_args = '?'+ query_args[1:]

    result = dict()
    new_path += query_args
    result['response']=list_obj.get_list(region=region, initial_url_append='/' + new_path)

    path_list = new_path.split('/')
    path_list.reverse()
    kwargs = dict()
    main_resource = path_list.pop()
    if path_list and main_resource == 'servers':
        if path_list and '-' in path_list[-1]:
            kwargs['server_id'] = path_list.pop()
            if 'server' in result['response'][0]['result']:
                kwargs['flavor_id'] = result['response'][0]['result']['server']['flavor']['id']
                kwargs['image_id'] = result['response'][0]['result']['server']['image']['id']
                for link in result['response'][0]['result']['server']['links']:
                    if link['rel'] == 'bookmark':
                        kwargs['server_uri'] = link['href']
    elif path_list and main_resource == 'entities':
        if path_list and path_list[-1]:
            kwargs['entity_id'] = path_list.pop()
        if len(path_list) >= 2 and path_list[-1] == 'checks':
            path_list.pop()
            kwargs['check_id'] = path_list.pop()
    elif servicename == 'cloudFeeds':
        flask.session['cloudFeeds_'+region] = result['response'][0]['result']
        list_obj.feed_region = region

        list_obj.feed_list_payload = flask.session['cloudFeeds_'+region]
        result['response'][0].additional_url_list = list_obj.custom_urls()
    elif servicename == 'cloudBackup':
        if main_resource == 'backup-configuration' and path_list[-1] == 'system':
            kwargs['machine_agent_id'] = path_list[-2]

    result['template_kwargs'] = list_obj.pprint_html_url_results(region=region, **kwargs)

    return display_json(**result)


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
