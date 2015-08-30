from flask import Flask
from flask.json import jsonify
from flask import request
import os
from rack_cloud_info.rack_apis.identity import Identity
from rack_cloud_info.rack_apis.nextgen_servers import ServerAPI
app = Flask(__name__)

from requests.packages import urllib3
urllib3.disable_warnings()

global_ident = Identity(os.environ['CLOUD_USER'], os.environ['CLOUD_API'])



@app.route('/servers')
def server_list():
    region = request.args.get('region', 'ORD')
    servers = ServerAPI(global_ident).server_list(region)
    return jsonify(servers)

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
