import pprint
import copy

import requests
import re
import json
import time
import rack_cloud_info.rack_apis.base

MASK_HEADERS = ('X-Auth-Token',)


class RackAPIBase(object):
    _identity = None
    _catalog_key = ''
    _list_object = None
    _accept_header_json = 'application/json'
    _url_kwarg_list = list()

    def __init__(self, identity):
        from rack_cloud_info.rack_apis.identity import Identity
        if not isinstance(identity, Identity):
            raise ValueError("Identity object required")
        self._identity = identity


    def _auth_request(self, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['X-Auth-Token'] = self.token
        result = self.display_base_request(**kwargs)
        return result

    def displayable_json_auth_request(self, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['X-Auth-Token'] = self.token
        if self._accept_header_json:
            kwargs['headers']['Accept'] = self._accept_header_json
        start_time = time.time()
        result = self.display_base_request(**kwargs)
        end_time = time.time()

        json_result = RackAPIResult(result, response_time=end_time-start_time, identity_obj=self._identity)

        return json_result

    @classmethod
    def base_request(cls, method='get', **kwargs):
        if isinstance(kwargs.get('data'), dict):
            kwargs['data'] = json.dumps(kwargs['data'])
            kwargs['headers'] = kwargs.get('headers', {})
            kwargs['headers']['Content-Type'] = 'application/json'

        return getattr(requests, method)(**kwargs)

    @classmethod
    def display_base_request(cls, **kwargs):
        return cls.base_request(**kwargs)

    @property
    def token(self):
        return self._identity.token

    def public_endpoint_urls(self, region=None, version=None):
        result = self._identity.service_catalog(name=self._catalog_key,
                                                region=region)
        return [endpoint.get('publicURL') for endpoint in
                result[0]['endpoints']]

    def get_list(self, region=None, initial_url_append=None, data_object=None):
        result_list = []

        region_url = self.public_endpoint_urls(region=region)[0]
        url = "{0}{1}".format(region_url, initial_url_append)
        while url:
            result = self.displayable_json_auth_request(url=url)
            result_list.append(result)
            if result_list[-1].get('next'):
                url = region_url + result_list[-1].get('next')
                url = url.replace('/v2/v2', '/v2')
            else:
                url = None
        if isinstance(data_object, type):
            return data_object(result_list)
        elif isinstance(self.list_object_class, type):
            return self.list_object_class(result_list)
        else:
            return result_list

    @property
    def list_object_class(self):
        return self._list_object

    @list_object_class.setter
    def list_object_class(self, value):
        if not issubclass(value, rack_cloud_info.rack_apis.base.RestfulList):
            raise ValueError("Class is not a type of RestfulObject: {0}".format(type(value)))
        self._list_object = value

    def available_urls(self):
        return []

    def related_urls(self):
        url_list = list()
        return url_list

    def filled_out_urls(self, region=None, **kwargs):
        for kwarg_name in self._url_kwarg_list:
            kwargs[kwarg_name] = kwargs.get(kwarg_name, 'UNKNOWN_{0}'.format(kwarg_name))

        url_list = self.available_urls()
        for index, url in enumerate(url_list):
            url_list[index] = self.public_endpoint_urls(region=region)[0] + url.format(**kwargs)

        rel_url_list = self.related_urls()
        for index, url in enumerate(rel_url_list):
            rel_url_list[index] = self.public_endpoint_urls(region=region)[0] + url.format(**kwargs)

        result = {'links': {'populated': [], 'rel': []}}
        for index, url in enumerate(url_list):
            result['links']['populated'].append(url)

        result['links']['populated'].sort()
        for index, url in enumerate(rel_url_list):
            if 'UNKNOWN_' not in url:
                result['links']['rel'].append(url)
        result['links']['rel'].sort()

        return copy.deepcopy(result)

    def pprint_html_url_results(self, **kwargs):
        result = self.filled_out_urls(**kwargs)

        for type, url_list in result['links'].items():
            for index, url in enumerate(url_list):
                for replace_url, replace_url_info in self._identity.url_to_catalog_dict().items():
                    if replace_url in url and 'UNKNOWN_' not in url:
                        new_regex = "({0})([^']*)".format(replace_url)
                        match_url = re.compile(new_regex)
                        result['links'][type][index] = match_url.sub(r"<a href='/{0}/{1}\2'>\1\2</a>".format(*replace_url_info), url)
        return result


class RackAPIResult(dict):
    _identity_obj = None

    def __init__(self, result, request_headers=None, response_headers=None, url=None, status_code=None,
                 identity_obj=None, **kwargs):
        super().__init__(**kwargs)
        self._identity_obj = identity_obj
        if isinstance(result, requests.Response):
            try:
                self['result'] = result.json()
            except ValueError:
                self['result'] = result.text

            url = result.request.url
            status_code = result.status_code
            request_headers = dict(**result.request.headers)
            response_headers = dict(**result.headers)
        else:
            self['result'] = result

        self['request_headers'] = request_headers
        self['response_headers'] = response_headers
        self['url'] = url
        self['status_code'] = status_code

        for header_name in MASK_HEADERS:
            if header_name in self['request_headers']:
                self['request_headers'][header_name] = '<masked>'
            if header_name in self['response_headers']:
                self['response_headers'][header_name] = '<masked>'

    @property
    def pprint_html_result(self):
        result = str(pprint.pformat(self['result']))
        if not self._identity_obj:
            return result

        for url, url_info in self._identity_obj.url_to_catalog_dict().items():
            match_url = re.compile("'({0})([^']*)'".format(url))
            result = match_url.sub(r"'<a href='/{0}/{1}\2'>\1\2</a>'".format(*url_info), result)
        return result

    def filled_out_urls(self, region=None, **kwargs):
        for kwarg_name in self._url_kwarg_list:
            kwargs[kwarg_name] = kwargs.get(kwarg_name, 'UNKNOWN_{0}'.format(kwarg_name))

        return self.filled_out_urls(region, **kwargs)



class ServersAPI(RackAPIBase):
    _catalog_key = 'cloudServersOpenStack'

    def available_urls(self):
        url_list = list()
        url_list.append('/servers')
        url_list.append('/servers/detail')
        url_list.append('/servers/{server_id}')
        url_list.append('/os-keypairs')
        url_list.append('/servers/{server_id}/ips')
        url_list.append('/servers/{server_id}/ips/networkLabel')
        url_list.append('/servers/{server_id}/os-volume_attachments')
        url_list.append('/servers/{server_id}/os-volume_attachments/{attachment_id}')
        url_list.append('/flavors')
        url_list.append('/flavors/detail')
        url_list.append('/flavors/{flavor_id}')
        url_list.append('/images/detail')
        url_list.append('/images/{image_id}')
        url_list.append('/servers/{server_id}/metadata')
        url_list.append('/servers/{server_id}/metadata/{metadata_key}')
        url_list.append('/flavors')
        url_list.append('/flavors')
        return url_list


class FeedsAPI(RackAPIBase):
    _catalog_key = 'cloudFeeds'
    _accept_header_json = 'application/vnd.rackspace.atom+json'

    def get_feed_events(self, feed_type, region):
        list_obj = self.get_list(region)
        for feed_info in list_obj[0]['result']['service']['workspace']:
            if 'collection' in feed_info and feed_info['collection']['title'] == feed_type:
                return [self.displayable_json_auth_request(url=feed_info['collection']['href'])]
        return None


class BackupAPI(RackAPIBase):
    _catalog_key = 'cloudBackup'


class MonitoringAPI(RackAPIBase):
    _catalog_key = 'cloudMonitoring'
    _url_kwarg_list = ('entity_id', 'check_id', 'metric_name', 'check_type_id', 'monitoring_zone_id', 'alarm_id',
                       'notification_plan_id', 'notification_id', 'alarm_example_id', 'suppession_id')

    def available_urls(self):
        url_list = list()
        url_list.append('/limits')
        url_list.append('/account')
        url_list.append('/audits')
        url_list.append('/usage')
        url_list.append('/entities')
        url_list.append('/entities/{entity_id}')
        url_list.append('/entities/{entity_id}/checks')
        url_list.append('/entities/{entity_id}/checks/{check_id}')
        url_list.append('/entities/{entity_id}/checks/{check_id}/metrics')
        url_list.append('/entities/{entity_id}/checks/{check_id}/metrics/{metric_name}/plot')
        url_list.append('/check_types')
        url_list.append('/check_types/{check_type_id}')
        url_list.append('/monitoring_zones')
        url_list.append('/monitoring_zones/{monitoring_zone_id}')
        url_list.append('/entities/{entity_id}/alarms')
        url_list.append('/entities/{entity_id}/alarms/{alarm_id}')
        url_list.append('/entities/{entity_id}/alarms/{alarm_id}/notification_history')
        url_list.append('/entities/{entity_id}/alarms/{alarm_id}/notification_history/{check_id}')
        url_list.append('/entities/{entity_id}/alarms/{alarm_id}/notification_history/{check_id}/uuid')
        url_list.append('/notification_plans')
        url_list.append('/notification_plans/{notification_plan_id}')
        url_list.append('/notifications')
        url_list.append('/notifications/{notification_id}')
        url_list.append('/notification_types')
        url_list.append('/views/overview')
        url_list.append('/changelogs/alarms')
        url_list.append('/alarm_examples')
        url_list.append('/alarm_examples/{alarm_example_id}')
        url_list.append('/suppression_logs')
        url_list.append('/suppressions/{suppession_id}')


        return url_list


def get_catalog_api(catalog_key):
    for possible_class in RackAPIBase.__subclasses__():
        if possible_class._catalog_key == catalog_key:
            return possible_class
    return None


