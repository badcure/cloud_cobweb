import re
import pprint
import flask
from . import base

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
        result += '{0}: {1}\n'.format(key, value)
    return result


@base.app.template_filter('convert_to_urls')
def convert_to_urls(result):
    if not isinstance(result, str):
        result = str(pprint.pformat(result))
    if not flask.g.user_info:
        return result
    if flask.g.list_obj:
        for replace_url, replace_url_info in flask.g.list_obj.get_auth().url_to_catalog_dict():
            result = result.replace('/' + '/'.join(replace_url_info), replace_url)
    url_prefix = flask.current_app.blueprints[flask.request.blueprint].url_prefix

    for url, replace_url_info in flask.g.user_info.url_to_catalog_dict():
        match_url = re.compile("\"({0})/*([^\"]*)\"".format(url))
        if len(replace_url_info) == 2:
            print(url + "\t" + str(replace_url_info))
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
