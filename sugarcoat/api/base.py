import flask
import string
import random
import os

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
    result = cake_lie_view()
    return result, 404

@app.route('/')
def index():
    return flask.Response(flask.render_template('main_index.html'))

@app.route('/cake_is_a_lie.html')
def cake_lie_view():
    restful_result = {"random":
             {"status": 404,
              "message": "Not sure how you got here.",
              "links": [
                  {"rel": "mouse breaker", "href": 'http://orteil.dashnet.org/cookieclicker/'},
                  {"rel": "browser mmo", "href": 'http://agar.io/'},
                  {"rel": "selfless or selfish", "href": 'http://cursors.io/'},
                  {"rel": "RPG...I guess", "href": 'http://nekogames.jp/g.html?GID=gm0000001351&OTP&SID=9003216&r=1333941573&gid=PRM'},
                  {"rel": "coding music", "href": 'https://www.youtube.com/watch?v=hGlyFc79BUE'},
                  {"rel": "repo", "href": 'https://github.com/badcure/sugarcoat'},
                  {"rel": "bookmark", "href": 'https://sugarcoat.in'},
                  {"rel": "self", "href": 'https://sugarcoat.in/cake_is_a_lie.html'}
              ]
              }
         }
    return flask.jsonify(restful_result)