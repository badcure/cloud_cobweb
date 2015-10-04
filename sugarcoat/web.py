from sugarcoat.api import app
from requests.packages import urllib3
urllib3.disable_warnings()

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
