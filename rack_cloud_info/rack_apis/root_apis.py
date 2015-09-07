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
    only_region = None

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

    @classmethod
    def available_urls(cls):
        return []

    @classmethod
    def complete_urls(cls):
        url_list = list()
        return url_list

    def related_urls(self):
        url_list = list()
        return url_list

    def filled_out_urls(self, **kwargs):
        region = kwargs.get('region')
        for kwarg_name in self._url_kwarg_list:
            kwargs[kwarg_name] = kwargs.get(kwarg_name, 'KEY_{0}_UNDEFINED'.format(kwarg_name))

        url_list = self.available_urls()
        for index, url in enumerate(url_list):
            url_list[index] = self.public_endpoint_urls(region=region)[0] + url.format(**kwargs)

        for index, url in enumerate(self.complete_urls()):
            url_list.append(url.format(**kwargs))

        rel_url_list = self.get_relation_urls(region=region)
        for index, url in enumerate(rel_url_list):
            rel_url_list[index] = url.format(**kwargs)

        result = {'links': {'populated': [], 'rel': []}}
        for index, url in enumerate(url_list):
            result['links']['populated'].append(url)

        result['links']['populated'].sort()
        for index, url in enumerate(rel_url_list):
            if '_UNDEFINED' not in url:
                result['links']['rel'].append(url)
        result['links']['rel'].sort()

        return copy.deepcopy(result)

    def pprint_html_url_results(self, **kwargs):
        result = self.filled_out_urls(**kwargs)
        url_list_to_replace = list(self._identity.url_to_catalog_dict().items()) + list(self.custom_urls())
        for index, url in enumerate(result['links']['populated']):
            for replace_url, replace_url_info in url_list_to_replace:
                if replace_url in url and '_UNDEFINED' not in url:
                    new_regex = "^({0})([^']*)".format(replace_url)
                    match_url = re.compile(new_regex)
                    result['links']['populated'][index] = match_url.sub(r"<a href='/{0}/{1}\2'>\1\2</a>".format(*replace_url_info), url)

        for index, url in enumerate(result['links']['rel']):
            for replace_url, replace_url_info in url_list_to_replace:
                if replace_url in url and url.index(replace_url) == 0:
                    new_regex = "^({0})([^']*)".format(replace_url)
                    match_url = re.compile(new_regex)
                    result['links']['rel'][index] = match_url.sub(r"<a href='/{0}/{1}\2'>\1\2</a>".format(*replace_url_info), url)
                elif url.index('/') == 0:
                    result['links']['rel'][index] = "<a href='{0}'>{0}</a>".format(url)


        return result

    def get_relation_urls(self, region=None):
        result_list = list()

        for possible_class in RackAPIBase.__subclasses__():
            common_ids = set(possible_class._url_kwarg_list) & set(self._url_kwarg_list)
            if common_ids and possible_class != self.__class__:
                for possible_url in possible_class.available_urls():
                    tmp_url = None
                    for kwarg_id in common_ids:
                       if '{'+kwarg_id+'}' in possible_url:
                           tmp_url = (tmp_url or possible_url).replace('{'+kwarg_id+'}', '')
                    if tmp_url and '{' not in tmp_url:
                        if possible_class.only_region == 'all':
                            region = None
                        elif possible_class.only_region:
                            region = possible_class.only_region
                        base_url = self._identity.service_catalog(name=possible_class._catalog_key, region=region)[0]['endpoints'][0]['publicURL']
                        result_list.append(base_url + possible_url)

                for possible_url in possible_class.complete_urls():
                    tmp_url = None
                    for kwarg_id in common_ids:
                        if '{'+kwarg_id+'}' in possible_url:
                            tmp_url = (tmp_url or possible_url).replace('{'+kwarg_id+'}', '')
                    if tmp_url and '{' not in tmp_url:
                        if possible_class.only_region == 'all':
                            region = None
                        elif possible_class.only_region:
                            region = possible_class.only_region
                        result_list.append(possible_url)

        return result_list

    def custom_urls(self, **kwargs):
        return []

class RackAPIResult(dict):
    _identity_obj = None
    additional_url_list = []

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

        for url, url_info in self.additional_url_list:
            match_url = re.compile("'({0})([^']*)'".format(url))
            result = match_url.sub(r"'<a href='/{0}/{1}\2'>\1\2</a>'".format(*url_info), result)

        return result


class ServersAPI(RackAPIBase):
    _catalog_key = 'cloudServersOpenStack'
    _url_kwarg_list = ('server_id', 'flavor_id', 'attachment_id', 'image_id', 'metadata_key', 'server_uri',
                       'flavor_class', 'server_request_id')

    @classmethod
    def available_urls(cls):
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
        url_list.append('/limits')
        url_list.append('/flavors/{flavor_class}/os-extra_specs')
        url_list.append('/servers/{server_id}/os-instance-actions')
        url_list.append('/servers/{server_id}/os-instance-actions/{server_request_id}')
        url_list.append('/os-networksv2')
        return url_list


class FeedsAPI(RackAPIBase):
    _catalog_key = 'cloudFeeds'
    _url_kwarg_list = ('server_id', 'entity_id', 'user_id', 'container_name', 'machine_agent_id', 'username')
    _accept_header_json = 'application/vnd.rackspace.atom+json'
    feed_list_payload = dict()
    feed_region = 'all'
    feed_task = None


    def get_feed_events(self, feed_type, region):
        list_obj = self.get_list(region)
        for feed_info in list_obj[0]['result']['service']['workspace']:
            if 'collection' in feed_info and feed_info['collection']['title'] == feed_type:
                return [self.displayable_json_auth_request(url=feed_info['collection']['href'])]
        return None

    def custom_urls(self, **kwargs):
        url_list = list()
        for feed_entry in self.feed_list_payload.get('service', {}).get('workspace', []):
            if 'collection' not in feed_entry:
                continue
            title = feed_entry['title']
            url = feed_entry['collection']['href']
            url_list.append((url, ('cloudFeeds', '{0}/{1}'.format(self.feed_region, title))))

        return url_list

    def public_endpoint_urls(self, region=None, version=None):
        if not self.feed_task:
            return super().public_endpoint_urls(region, version)
        for feed_entry in self.feed_list_payload.get('service', {}).get('workspace', []):
            if feed_entry['title'] == self.feed_task:
                return [feed_entry['collection']['href']]
        return None

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/cloudFeeds/DFW/nova_events/?search=(AND(cat=rid:{server_id}))')
        return url_list

    @classmethod
    def complete_urls(cls):
        url_list = list()
        url_list.append('/cloudFeeds/DFW/nova_events/?search=(AND(cat=rid:{server_id}))')
        url_list.append('/cloudFeeds/DFW/monitoring_events/?search=(AND(cat=rid:{entity_id}))')
        url_list.append('/cloudFeeds/DFW/identity_events/?search=(AND(cat=rid:{user_id}))')
        url_list.append('/cloudFeeds/DFW/identity_events/?search=(AND(cat=tid:{container_name}))')
        url_list.append('/cloudFeeds/DFW/backup_events/?search=(AND(cat=rid:{machine_agent_id}))')
        url_list.append('/cloudFeeds/DFW/feedsaccess_events/?search=(AND(cat=tid:{username}))')

        return url_list



class BackupAPI(RackAPIBase):
    _catalog_key = 'cloudBackup'
    _url_kwarg_list = ('server_id', 'agent_id', 'restore_id', 'machine_agent_id', 'backup_configuration_id', 'backup_id')

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/agent/{machine_agent_id}')
        url_list.append('/agent/server/{server_id}')
        url_list.append('/user/agents')
        url_list.append('/backup-configuration')
        url_list.append('/backup-configuration/{backup_configuration_id}')
        url_list.append('/backup-configuration/system/{machine_agent_id}')
        url_list.append('/backup/{backup_id}')
        url_list.append('/backup/completed/{backup_configuration_id}')
        url_list.append('/backup/report/{backup_id}')
        url_list.append('/restore/files/{restore_id}')
        url_list.append('/backup/availableforrestore')
        url_list.append('/restore/{restore_id}')
        url_list.append('/restore/report/{restore_id}')
        url_list.append('/system/activity/{agent_id}')
        url_list.append('/activity')
        return url_list


class MonitoringAPI(RackAPIBase):
    _catalog_key = 'cloudMonitoring'
    only_region = 'all'
    _url_kwarg_list = ('entity_id', 'check_id', 'metric_name', 'check_type_id', 'monitoring_zone_id', 'alarm_id',
                       'notification_plan_id', 'notification_id', 'alarm_example_id', 'suppession_id', 'server_uri')

    @classmethod
    def available_urls(cls):
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
        url_list.append('/views/overview?entity={entity_id}')
        url_list.append('/views/overview?uri={server_uri}')
        url_list.append('/changelogs/alarms')
        url_list.append('/alarm_examples')
        url_list.append('/alarm_examples/{alarm_example_id}')
        url_list.append('/suppression_logs')
        url_list.append('/suppressions/{suppession_id}')


        return url_list


class OrchastrationAPI(RackAPIBase):
    _catalog_key = 'cloudOrchestration'
    _url_kwarg_list = ('stack_name', 'stack_id', 'resource_name', 'event_id', 'type_name')

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/stacks​')
        url_list.append('/stacks/{stack_name}')
        url_list.append('/stacks/{stack_name}/{stack_id}')
        url_list.append('/stacks/{stack_name}/resources')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources​')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources/{resource_name}')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources/{resource_name}/metadata')
        url_list.append('/resource_types')
        url_list.append('/resource_types/{type_name}')
        url_list.append('/resource_types/{type_name}/template')
        url_list.append('/stacks/{stack_name}/events')
        url_list.append('/stacks/{stack_name}/{stack_id}/events')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources/{resource_name}/events​')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources/{resource_name}/events/{event_id}')
        url_list.append('/build_info')


        return url_list


class CloudFilesAPI(RackAPIBase):
    _catalog_key = 'cloudFiles'
    _url_kwarg_list = ('container_name', 'object')

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/​')
        url_list.append('/{container_name}')
        url_list.append('/{container_name}/{object}')
        return url_list


class CloudFilesCDNAPI(RackAPIBase):
    _catalog_key = 'cloudFilesCDN'
    _url_kwarg_list = ()

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/​')
        return url_list


class RackspaceCDNAPI(RackAPIBase):
    _catalog_key = 'rackCDN'
    _url_kwarg_list = ('flavor_id',)
    only_region = 'DFW'

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/')
        url_list.append('/ping')
        url_list.append('/health')
        url_list.append('/services')
        url_list.append('/flavors/{flavor_id}')

        return url_list


class CloudImages(RackAPIBase):
    _catalog_key = 'cloudImages'
    _url_kwarg_list = ('image_id', 'member_id', 'task_id')

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/')
        url_list.append('/images')
        url_list.append('/images/{image_id}')
        url_list.append('/images/{image_id}/members')
        url_list.append('/images/{image_id}/members/{member_id}')
        url_list.append('/tasks')
        url_list.append('/tasks/{task_id}')
        url_list.append('/schemas/images')
        url_list.append('/schemas/image')
        url_list.append('/schemas/members')
        url_list.append('/schemas/member')
        url_list.append('/schemas/tasks')
        url_list.append('/schemas/task')

        return url_list


class CloudServersFirstGenAPI(RackAPIBase):
    _catalog_key = 'cloudServers'
    _url_kwarg_list = ('firstgen_id', 'firstgen_image_id', 'firstgen_ip_group_id')
    only_region = 'all'
    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/')
        url_list.append('/servers')
        url_list.append('/servers/detail')
        url_list.append('/servers/{firstgen_id}')
        url_list.append('/servers/{firstgen_id}/ips')
        url_list.append('/servers/{firstgen_id}/ips/public')
        url_list.append('/servers/{firstgen_id}/ips/private')
        url_list.append('/flavors')
        url_list.append('/flavors/detail')
        url_list.append('/images')
        url_list.append('/images/detail')
        url_list.append('/images/{firstgen_image_id}')
        url_list.append('/servers/{firstgen_id}/backup_schedule')
        url_list.append('/shared_ip_groups')
        url_list.append('/shared_ip_groups/detail')
        url_list.append('/shared_ip_groups/{firstgen_ip_group_id}')

        return url_list



def get_catalog_api(catalog_key):
    for possible_class in RackAPIBase.__subclasses__():
        if possible_class._catalog_key == catalog_key:
            return possible_class
    return None


