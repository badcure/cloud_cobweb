from flask import Flask
from flask.json import jsonify
from flask import request
import os
from rack_cloud_info.rack_apis.identity import Identity
from rack_cloud_info.rack_apis.nextgen_servers import ServersAPI, ImagesAPI
app = Flask(__name__)

from requests.packages import urllib3
urllib3.disable_warnings()

global_ident = Identity(os.environ['CLOUD_USER'], os.environ['CLOUD_API'])

DEFAULT_REGION = 'ORD'
@app.route('/servers')
def server_list():
    api_type = ServersAPI
    region = request.args.get('region', DEFAULT_REGION)
    should_populate = request.args.get('populate', False)
    api_obj = api_type(global_ident)
    list_obj = api_obj.get_list(region)
    if should_populate:
        list_obj.populate_info(global_ident)

    return jsonify(request=list_obj)

@app.route('/images')
def image_list():
    list_obj = ImagesAPI
    region = request.args.get('region', DEFAULT_REGION)
    should_populate = request.args.get('populate', False)
    images = list_obj(global_ident).get_list(region)
    if should_populate:
        images.populate_info(global_ident)

    return jsonify(request=images)


@app.route('/auth_token')
def auth_token_view():
    global_ident.token
    return jsonify(global_ident.display_safe())


if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
