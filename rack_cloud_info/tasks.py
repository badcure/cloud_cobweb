from __future__ import absolute_import
from celery import Celery
import datetime

REDIS_SERVER = 'redis://localhost:6379/0'

class CeleryConfig(object):
    CELERYBEAT_SCHEDULE = {
        'add-every-30-seconds': {
            'task': 'tasks.add',
            'schedule': datetime.timedelta(seconds=60),
            'kwargs': (16, 16)
        },
    }

app = Celery('tasks', broker='redis://localhost//')

class AtomHopperWatch(app.Task):
    def run(self, ah_url):
        print "Starting request for {0}".format(ah_url)
        print "Completed request for {0}".format(ah_url)