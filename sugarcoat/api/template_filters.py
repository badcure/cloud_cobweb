import re
import pprint
import flask
from . import base

HEADER_LINKS = dict()
HEADER_LINKS['content-encoding'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.11')
HEADER_LINKS['content-length'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.13')
HEADER_LINKS['vary'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.44')
HEADER_LINKS['accept-ranges'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.5')
HEADER_LINKS['age'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.6')
HEADER_LINKS['accept-language'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.4')
HEADER_LINKS['accept-encoding'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.3')
HEADER_LINKS['accept'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.1')
HEADER_LINKS['last-modified'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.29')
HEADER_LINKS['connection'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.10')
HEADER_LINKS['content-type'] = dict(
    header_key='http://www.w3.org/Protocols/rfc1341/4_Content-Type.html')
HEADER_LINKS['etag'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.19')
HEADER_LINKS['content-language'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.12')
HEADER_LINKS['date'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.18')
HEADER_LINKS['server'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.38')
HEADER_LINKS['via'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.45')
HEADER_LINKS['x-newrelic-app-data'] = dict(
    header_key='https://docs.newrelic.com/docs/apm/transactions/cross-application-traces/cross-application-tracing')
HEADER_LINKS['x-auth-token'] = dict(
    header_key='http://docs.rackspace.com/auth/api/v2.0/auth-client-devguide/content/QuickStart-000.html#submit_API_request')
HEADER_LINKS['user-agent'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.43')
HEADER_LINKS['transfer-encoding'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.41')
HEADER_LINKS['cache-control'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.9')
HEADER_LINKS['access-control-allow-origin'] = dict(
    header_key='http://www.w3.org/TR/cors/#access-control-allow-origin-response-header')
HEADER_LINKS['access-control-max-age'] = dict(
    header_key='http://www.w3.org/TR/cors/#access-control-max-age-response-header')
HEADER_LINKS['access-control-allow-methods'] = dict(
    header_key='http://www.w3.org/TR/cors/#access-control-allow-methods-response-header')
HEADER_LINKS['access-control-allow-credentials'] = dict(
    header_key='http://www.w3.org/TR/cors/#access-control-allow-credentials-response-header')
HEADER_LINKS['access-control-allow-headers'] = dict(
    header_key='http://www.w3.org/TR/cors/#access-control-allow-headers-response-header')
HEADER_LINKS['etag'] = dict(
    header_key='http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.19')

@base.app.template_filter('format_json_html')
def format_json_html(obj, iteration=0):
    result = ""
    if isinstance(obj, dict):
        result += "<div class='json object' iteration={iteration}>".format(iteration=iteration)
        for key in sorted(obj.keys()):
            result += "<div class='json object_item' iteration={iteration}><span class='json object_key'>{key}" \
                      "</span><span class='json object_value'>{value}</span></div>".format(
                key=format_json_html(key, iteration=iteration+1), value=format_json_html(obj[key], iteration=iteration+1), iteration=iteration)
        result += "</div>"
    elif isinstance(obj, list):
        result += "<div class='json array'>"
        for value in obj:
            result += "<div class='json array_item' iteration={iteration}>{value}</div>".format(
                value=format_json_html(value, iteration=iteration+1), iteration=iteration)
        result += "</div>"
    elif isinstance(obj, str):
        result += "<span class='json string' iteration={iteration}>{obj}</span>".format(obj=obj, iteration=iteration)
    elif isinstance(obj, (int, float)):
        result += "<span class='json int' iteration={iteration}>{obj}</span>".format(obj=obj, iteration=iteration)
    elif obj is None:
        result += "<span class='json null' iteration={iteration}>null</span>".format(obj=obj, iteration=iteration)
    elif obj is True:
        result += "<span class='json true' iteration={iteration}>true</span>".format(obj=obj, iteration=iteration)
    elif obj is False:
        result += "<span class='json false' iteration={iteration}>false</span>".format(obj=obj, iteration=iteration)
    if iteration == 0:
        result = "<div class='json original'>{result}</div>".format(result=result)
    return result


@base.app.template_filter('print_headers')
def print_headers(obj):
    result = ''
    for key, value in obj.items():
        if key.lower() == 'x-trans-id' and 'repose' in obj.get('Via', obj.get('via', '')).lower():
            url = 'https://repose.atlassian.net/wiki/display/REPOSE/Tracing'
            result += '<a href="{url}">{key} <span class="glyphicon glyphicon-globe" aria-hidden="true"></span></a>: '.format(key=key, url=url)
        elif key.lower() in HEADER_LINKS:
            result += '<a href="{url}">{key} <span class="glyphicon glyphicon-globe" aria-hidden="true"></span></a>: '.format(key=key, url=HEADER_LINKS[key.lower()]['header_key'])
        else:
            result += '{key}: '.format(key=key)

        if key in ['Via', 'via'] and 'repose' in value.lower():
            url = 'https://repose.atlassian.net/wiki/display/REPOSE/Home'
            result += '<a href="{url}">{value} <span class="glyphicon glyphicon-globe" aria-hidden="true"></span></a>\n'.format(value=value, url=url)
        else:
            result += '{1}\n'.format(key, value)
    return result


@base.app.template_filter('convert_to_urls')
def convert_to_urls(result):
    if not isinstance(result, str):
        result = flask.json.dumps(result, indent=2)
    if not hasattr(flask.g, 'user_info') or not flask.g.user_info:
        return result
    if flask.g.list_obj:
        for replace_url, replace_url_info in flask.g.list_obj.get_auth().url_to_catalog_dict():
            result = result.replace('/' + '/'.join(replace_url_info), replace_url)
    url_prefix = flask.current_app.blueprints[flask.request.blueprint].url_prefix

    for url, replace_url_info in flask.g.user_info.url_to_catalog_dict():
        match_url = re.compile("\"({0})/*([^\"]*)\"".format(url))
        if len(replace_url_info) == 2:
            result = match_url.sub(r"<a href='{url_prefix}/{0}/{1}/\2'>\1/\2</a>".format(*replace_url_info, url_prefix=url_prefix), result)

    for url, replace_url_info in flask.g.user_info.url_to_catalog_dict():
        match_url = re.compile("\"({0})/*([^\"]*)\"".format(url))
        if len(replace_url_info) == 3:
            result = match_url.sub(r"<a href='{url_prefix}/{0}/{1}/{2}/\2'>\1/\2</a>".format(*replace_url_info, url_prefix=url_prefix), result)

    match_url = re.compile("\"((https?:\/\/)([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?)\"")
    result = match_url.sub(r'"<a href="\1">\1 <span class="glyphicon glyphicon-globe" aria-hidden="true"></span></a>"', result)

    return result

@base.app.template_filter('update_dict')
def update_dict(x,y):
    return x.update(y)
