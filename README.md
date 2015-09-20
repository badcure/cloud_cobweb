# Sugarcoat
Helping to make APIs easier to consume

To run, simply:

    apt-get install python3-setuptools
    python3 setup.py install

Uwsgi

    [uwsig]
    autoload = true
    master = true
    workers = 2
    no-orphans = true
    pidfile = /run/uwsgi/%(deb-confnamespace)/%(deb-confname)/pid
    socket = /run/uwsgi/%(deb-confnamespace)/%(deb-confname)/socket
    chmod-socket = 660
    log-date = true
    uid = www-data
    gid = www-data
    module = sugarcoat.api.web:app
    plugin = python3

Nginx

    upstream flask {
        server unix:///run/uwsgi/app/sugarcoat/socket;
        #server 127.0.0.1:5564;
    }
    server {
        location / {
                uwsgi_pass  flask;
                include     /etc/nginx/uwsgi_params;
        }
    }