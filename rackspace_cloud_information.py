import flask
import flask.ext
import rack_cloud_info.rack_apis
import rack_cloud_info.rack_apis.feeds
from rack_cloud_info.rack_apis.identity import UserAPI
from rack_cloud_info.rack_apis.nextgen_servers import ServersAPI, ImagesAPI
from rack_cloud_info.rack_apis.monitoring import MonitoringAPI
from rack_cloud_info.rack_apis.backup import BackupAPI
from base import app, login_required

from requests.packages import urllib3
urllib3.disable_warnings()

@app.route('/servers')
@login_required
def server_list():
    api_type = ServersAPI
    region = flask.request.args.get('region')
    should_populate = flask.request.args.get('populate', False)
    api_obj = api_type(flask.g.user_info)
    list_obj = api_obj.get_list(region)
    if should_populate:
        list_obj.populate_info(flask.g.user_info, region=region)

    return flask.json.jsonify(request=list_obj)

@app.route('/feeds')
@login_required
def feed_url_list():
    region = flask.request.args.get('region')
    feed_type = flask.request.args.get('type')

    api_type = rack_cloud_info.rack_apis.feeds.FeedsAPI
    should_populate = flask.request.args.get('populate', False)
    api_obj = api_type(flask.g.user_info)
    if not feed_type:
        list_obj = api_obj.get_list(region)
    else:
        list_obj = api_obj.get_feed_events(feed_type=feed_type, region=region)
    return flask.json.jsonify(request=list_obj)

@app.route('/images')
@login_required
def image_list():
    list_obj = ImagesAPI
    region = flask.request.args.get('region')
    should_populate = flask.request.args.get('populate', False)
    images = list_obj(flask.g.user_info).get_list(region)
    if should_populate:
        images.populate_info(flask.g.user_info)

    return flask.json.jsonify(request=images)


@app.route('/users')
@login_required
def user_list():
    list_obj = UserAPI
    should_populate = flask.request.args.get('populate', False)
    images = list_obj(flask.g.user_info).get_list()
    if should_populate:
        images.populate_info(flask.g.user_info)

    return flask.json.jsonify(request=images)


@app.route('/monitoring')
@login_required
def monitoring_list():
    list_obj = MonitoringAPI(flask.g.user_info)
    should_populate = flask.request.args.get('populate', False)

    result_list = list()
    result_list.append(list_obj.get_list(initial_url_append='/account'))
    result_list.append(list_obj.get_list(initial_url_append='/entities'))
    result_list.append(list_obj.monitoring_agent_list())

    if should_populate:
        result_list[-1].populate_info(identity_obj=flask.g.user_info)

    result_list.append(list_obj.get_list(initial_url_append='/views/overview'))

    return flask.json.jsonify(request=result_list)


@app.route('/backups')
@login_required
def backups_list():
    list_obj = BackupAPI(flask.g.user_info)
    region = flask.request.args.get('region')

    result_list = list()
    result_list.append(list_obj.backup_agents_list(region=region))

    return flask.json.jsonify(request=result_list)


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
