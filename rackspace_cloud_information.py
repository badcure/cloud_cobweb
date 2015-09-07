import flask
import flask.ext
import rack_cloud_info.rack_apis
import rack_cloud_info.rack_apis.base
import rack_cloud_info.rack_apis.feeds
from rack_cloud_info.rack_apis.nextgen_servers import ServersAPI, ImagesAPI
from rack_cloud_info.rack_apis.monitoring import MonitoringAPI
from rack_cloud_info.rack_apis.backup import BackupAPI
from base import app, login_required, display_json

from requests.packages import urllib3
urllib3.disable_warnings()


@app.route('/cloudServersOpenStack')
@login_required
def server_list():
    api_type = ServersAPI
    region = flask.request.args.get('region')
    api_obj = api_type(flask.g.user_info)
    list_obj = api_obj.get_list(region)
    return display_json(response=list_obj)


@app.route('/cloudFeeds')
@login_required
def feed_url_list():
    region = flask.request.args.get('region')
    feed_type = flask.request.args.get('type')

    api_type = rack_cloud_info.rack_apis.feeds.FeedsAPI
    api_obj = api_type(flask.g.user_info)
    if not feed_type:
        list_obj = api_obj.get_list(region)
    else:
        list_obj = api_obj.get_feed_events(feed_type=feed_type, region=region)
    return display_json(response=list_obj)


@app.route('/cloudImages')
@login_required
def image_list():
    list_obj = ImagesAPI
    region = flask.request.args.get('region')
    images = list_obj(flask.g.user_info).get_list(region)

    return display_json(response=images)


@app.route('/cloudMonitoring/all')
@app.route('/cloudMonitoring/all/')
@app.route('/cloudMonitoring/all/<path:new_path>')
@login_required
def monitoring_list(new_path='views/overview'):
    list_obj = MonitoringAPI(flask.g.user_info)

    result_list =list_obj.get_list(initial_url_append='/'+new_path)

    return display_json(response=result_list)


@app.route('/<string:servicename>/<string:region>')
@app.route('/<string:servicename>/<string:region>/')
@app.route('/<string:servicename>/<string:region>/<path:new_path>')
@login_required
def service_catalog_list(servicename,region,new_path=''):
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = servicename

    result_list = list_obj.get_list(region=region, initial_url_append='/' + new_path)

    return display_json(response=result_list)


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
