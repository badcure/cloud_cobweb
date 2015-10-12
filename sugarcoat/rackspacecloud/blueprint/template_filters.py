import pprint
import sugarcoat.rackspacecloud.blueprint.base
import re
import flask

@sugarcoat.rackspacecloud.blueprint.base.app.template_filter('print_headers')
def print_headers(obj):
    result = ''
    for key, value in obj.items():
        result += '{0}: {1}\n'.format(key, value)
    return result


def convert_to_related(region, api_result):
    resource_kwargs = api_result.get_resources()
    if 'region' not in resource_kwargs:
        resource_kwargs['region'] = region
    result = {'links': flask.g.list_obj.filled_out_urls(tenant_id=flask.g.user_info.tenant_id, **resource_kwargs)}
    url_list_to_replace = flask.g.list_obj.get_auth().url_to_catalog_dict()
    for index, url in enumerate(result['links']['populated']):
        for replace_url, replace_url_info in url_list_to_replace:
            url = url.replace('/' + '/'.join(replace_url_info), replace_url)
            new_regex = "^({0})/*([^']*)".format(replace_url)
            match_url = re.compile(new_regex)

            if replace_url in url and '_UNDEFINED' not in url:

                if len(replace_url_info) == 3:
                    result['links']['populated'][index] = match_url.sub(
                        r"<a href='/{0}/{1}/{2}/\2'>\1/\2</a>".format(*replace_url_info), url)
                else:
                    result['links']['populated'][index] = match_url.sub(
                        r"<a href='/{0}/{1}/\2'>\1/\2</a>".format(*replace_url_info), url)
            elif replace_url in url:
                result['links']['populated'][index] = match_url.sub(r"\1/\2", url)

    return result
