import flask
import string
import random
import os
from sugarcoat.base import SUGARCOAT_RESTFUL_KEY
from werkzeug.routing import Rule

app = flask.Flask(__name__)

ENVIRON_SECRETKEY_NAME = 'sugarcoat_secret'
if ENVIRON_SECRETKEY_NAME in os.environ:
    print("Using environment {0} for secret_key".format(ENVIRON_SECRETKEY_NAME))
    app.secret_key = os.environ[ENVIRON_SECRETKEY_NAME]
else:
    print("Randomly generating secret key")
    app.secret_key = ''.join(random.sample(string.ascii_letters, 24))
app.jinja_options['extensions'].append('jinja2.ext.do')

@app.errorhandler(404)
def page_not_found(e):
    result = cake_lie_view(404)
    return result, 404

@app.route('/')
def index():
    return flask.Response(flask.render_template('main_index.html'))

app.url_map.add(Rule('/cake_is_a_lie.html', endpoint='cake_lie_view'))

@app.endpoint('/cake_lie_view', )
def cake_lie_view(response_code=200):
    should_log = True
    restful_result = {"random":
             {"status": response_code,
              "message": "Not sure how you got here.",
              SUGARCOAT_RESTFUL_KEY:{
                  "links": [
                      {"rel": "mouse breaker", "href": 'http://orteil.dashnet.org/cookieclicker/'},
                      {"rel": "browser mmo", "href": 'http://agar.io/'},
                      {"rel": "selfless or selfish", "href": 'http://cursors.io/'},
                      {"rel": "RPG...I guess", "href": 'http://nekogames.jp/g.html?GID=gm0000001351&OTP&SID=9003216&r=1333941573&gid=PRM'},
                      {"rel": "coding music", "href": 'https://www.youtube.com/watch?v=hGlyFc79BUE'},
                      {"rel": "repo", "href": 'https://github.com/badcure/sugarcoat'},
                      {"rel": "bookmark", "href": 'https://sugarcoat.in'},
                      {"rel": "self", "href": flask.url_for('cake_lie_view',_external=True)},
                      {"rel": "request_url", "href": flask.request.url},
                  ],
                  'method': str(flask.request.method),
                  'url': str(flask.request.url),
                  'args': str(dict(flask.request.args)),
                  'data': flask.request.get_data(as_text=True),
                  'form': flask.request.form,

                  'headers': str(flask.request.headers),
                  'source_ipaddress': str(flask.request.remote_addr),
                  'info_logged': should_log
              }
              }
         }
    if should_log:
        app.logger.info(flask.json.dumps(restful_result))
    return flask.jsonify(restful_result)