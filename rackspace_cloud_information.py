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


@app.route('/cloudMonitoring')
@login_required
def monitoring_list():
    list_obj = MonitoringAPI(flask.g.user_info)

    result_list =list_obj.get_list(initial_url_append='/views/overview')

    return display_json(response=result_list)


@app.route('/cloudBackup')
@login_required
def backups_list():
    list_obj = BackupAPI(flask.g.user_info)
    region = flask.request.args.get('region')

    result_list = list_obj.backup_agents_list(region=region)

    return display_json(response=result_list)


@app.route('/cloudBlockStorage')
@login_required
def cloudBlockStorage_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudBlockStorage'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region)

    return display_json(response=result_list)


@app.route('/cloudQueues')
@login_required
def cloudQueues_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudQueues'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region)

    return display_json(response=result_list)


@app.route('/cloudBigData')
@login_required
def cloudBigData_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudBigData'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region, initial_url_append='/stacks')

    return display_json(response=result_list)


@app.route('/cloudOrchestration')
@login_required
def cloudOrchestration_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudOrchestration'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region, initial_url_append='/stacks')

    return display_json(response=result_list)


@app.route('/cloudDatabases')
@login_required
def cloudDatabases_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudDatabases'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region, initial_url_append='/instances')

    return display_json(response=result_list)


@app.route('/cloudNetworks')
@login_required
def cloudNetworks_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudNetworks'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region, initial_url_append='/')

    return display_json(response=result_list)


@app.route('/cloudMetrics')
@login_required
def cloudMetrics_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudMetrics'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region, initial_url_append='/metrics/search')

    return display_json(response=result_list)


@app.route('/cloudLoadBalancers')
@login_required
def cloudLoadBalancers_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudLoadBalancers'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region)

    return display_json(response=result_list)


@app.route('/cloudSites')
@login_required
def cloudSites_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudSites'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region, initial_url_append='/')

    return display_json(response=result_list)


@app.route('/cloudDNS')
@login_required
def cloudDNS_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudDNS'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region)

    return display_json(response=result_list)


@app.route('/cloudServers')
@login_required
def cloudServers_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudServers'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region)

    return display_json(response=result_list)


@app.route('/rackCDN')
@login_required
def rackCDN_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'rackCDN'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region)

    return display_json(response=result_list)


@app.route('/cloudFilesCDN')
@login_required
def cloudFilesCDN_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudFilesCDN'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region)

    return display_json(response=result_list)


@app.route('/cloudFiles')
@login_required
def cloudFiles_list():
    list_obj = rack_cloud_info.rack_apis.base.RackAPIBase(flask.g.user_info)
    list_obj._catalog_key = 'cloudFiles'
    region = flask.request.args.get('region')

    result_list = list_obj.get_list(region=region)

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
