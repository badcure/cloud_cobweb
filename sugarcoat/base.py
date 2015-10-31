import copy
import requests
import time
import json
import flask

MASK_HEADERS = ('X-Auth-Token',)
SUGARCOAT_RESTFUL_KEY = '~sugarcoat'

class APIResult(dict):
    additional_url_list = []
    result_type = 'Unknown'
    safe_html = None
    relation_urls = None
    response_time = -1

    def __init__(self, result, request_headers=None, response_headers=None, url=None, status_code=-2,
                 method='Unknown', request_body=None, show_confidential=False, response_time=-1, **kwargs):
        super().__init__(**kwargs)
        self.relation_urls = list()
        if isinstance(result, requests.HTTPError):
            result = result.response

        if isinstance(result, requests.Response):
            try:
                self['result'] = result.json()
                self.result_type = 'JSON - '
                if isinstance(self['result'], str):
                    self.result_type += 'String'
                elif isinstance(self['result'], dict):
                    self.result_type += 'Dictionary'
                elif isinstance(self['result'], list):
                    self.result_type += 'List'
                else:
                    self.result_type += 'Unknown'
                self.safe_html = True
            except ValueError:
                self['result'] = result.text
                self.result_type = 'Unknown(String)'
                if not self['result']:
                    self.result_type = 'No Result'

            url = result.request.url
            status_code = result.status_code
            request_headers = dict(**result.request.headers)
            request_body = result.request.body
            response_headers = dict(**result.headers)
            method = result.request.method
        elif isinstance(result, requests.RequestException):
            self['result'] = str(result)
            url = result.request.url
            request_headers = dict(**result.request.headers)
            response_headers = dict()
            status_code = -1
        else:
            self['result'] = result

        self['request_headers'] = request_headers
        self['response_headers'] = response_headers
        self['url'] = url
        self['status_code'] = status_code
        self['method'] = method
        self['request_body'] = request_body
        self.response_time = response_time

        if not show_confidential:
            for header_name in MASK_HEADERS:
                if header_name in self['request_headers']:
                    self['request_headers'][header_name] = 'MASKED INFO'
                if header_name in self['response_headers']:
                    self['response_headers'][header_name] = 'MASKED INFO'

    def pre_html_result(self):
        result = self['result']

        if isinstance(result, dict):
            result[SUGARCOAT_RESTFUL_KEY] = self.get_sorted_relations()
        return result

    def add_relation(self, url, resource_id=None, resource_name=None, resource_type=None):
        new_url = dict(href=url, rel='rel')
        if resource_id:
            new_url['resource_id'] = resource_id
        if resource_name:
            new_url['resource_name'] = resource_name
        if resource_type:
            new_url['resource_type'] = resource_type

        new_url['href'] = new_url['href'].format(**new_url)

        self.relation_urls.append(new_url)

    def get_sorted_relations(self):
        result = dict()
        for url_info in self.relation_urls:
            resource_type = url_info.get('resource_type', 'unknown_resource')
            resource_name = url_info.get('resource_name', 'unknown_resource')
            result[resource_type] = result.get(resource_type, dict())
            result[resource_type][resource_name] = result[resource_type].get(resource_name, list())
            result[resource_type][resource_name].append(url_info)
        return result

    @property
    def display_with_relation(self):
        result = self['result']
        if isinstance(result, dict):
            result = copy.deepcopy(self['result'])
            result[SUGARCOAT_RESTFUL_KEY] = self.get_sorted_relations()
        elif isinstance(result, list):
            result = copy.deepcopy(self['result'])
            result.append({SUGARCOAT_RESTFUL_KEY: self.get_sorted_relations()})
        result = json.dumps(result, indent=2, sort_keys=True)
        return result

    def get_resources(self):
        return {}

    def add_relation_urls(self, api_base_obj):
        rel_urls = api_base_obj.get_relation_urls()
        orig_url_kwargs = self.get_resources()
        for index, url_info in enumerate(rel_urls):
            url_kwargs = copy.deepcopy(orig_url_kwargs)
            try:
                url = url_info[0].format(**url_kwargs)
            except KeyError:
                continue
            resource_type = url_info[1].catalog_key
            resource_name = url_info[2]

            if '_UNDEFINED' not in url:
                self.add_relation(url=url, region=url_kwargs['region'], resource_name=resource_name, resource_type=resource_type)

        return


class APIBase(object):
    catalog_key = ''
    _accept_header_json = 'application/json'
    url_kwarg_list = list()
    result_class = None
    root_url = None

    def _auth_request(self, **kwargs):
        if self.token:
            kwargs['headers'] = kwargs.get('headers', {})
            kwargs['headers']['X-Auth-Token'] = self.token
        result = self.display_base_request(**kwargs)
        return result

    def displayable_json_auth_request(self, show_confidential=False, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        if self._accept_header_json:
            kwargs['headers']['Accept'] = self._accept_header_json
        start_time = time.time()
        result = self.display_base_request(**kwargs)
        end_time = time.time()
        response_time=end_time-start_time
        if issubclass(self.result_class, APIResult):
            json_result = self.result_class(result, show_confidential=show_confidential, response_time=response_time)
            json_result.add_relation_urls(self)
            return json_result
        return result


    @classmethod
    def base_request(cls, method='get', **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})


        if isinstance(kwargs.get('data'), (dict, list, tuple)):
            kwargs['data'] = json.dumps(kwargs['data'])
            kwargs['headers']['Content-Type'] = 'application/json'

        if 'additional_headers' in kwargs:
            kwargs['headers'].update(kwargs['additional_headers'])
            del kwargs['additional_headers']

        kwargs['headers']['User-Agent'] = '{0} https://sugarcoat.in'.format(kwargs['headers'].get(
            'User-Agent', requests.utils.default_user_agent()))
        if flask.request.remote_addr:
            kwargs['headers']['User-Agent'] += ' requestip:{0}'.format(flask.request.remote_addr)
        kwargs['headers']['Connection'] = kwargs['headers'].get('Connection', 'close')
        kwargs['timeout'] = kwargs.get('timeout', 10)
        return getattr(requests, method.lower())(**kwargs)

    @classmethod
    def display_base_request(cls, **kwargs):
        return cls.base_request(**kwargs)

    def public_endpoint_urls(self):
        return []

    def get_api_resource(self, initial_url_append=None, data_object=None, **kwargs):
        region_url = self.public_endpoint_urls()[0]

        if '__root__' == initial_url_append.split('/')[1]:
            initial_url_append = '/' + '/'.join(initial_url_append.split('/')[2:])
            region_url = '/'.join(region_url.split('/')[0:3])

        url = "{0}{1}".format(region_url, initial_url_append)

        result = self.displayable_json_auth_request(url=url, **kwargs)
        if isinstance(data_object, type):
            return data_object(result)

        return result

    @classmethod
    def available_urls(cls):
        return []

    def filled_out_urls(self, **kwargs):

        for kwarg_name in self.url_kwarg_list:
            kwargs[kwarg_name] = kwargs.get(kwarg_name, 'KEY_{0}_UNDEFINED'.format(kwarg_name))

        url_list = self.available_urls()
        for index, url in enumerate(url_list):
            url_list[index] = '/{0}/{2}'.format(self.catalog_key, url).format(**kwargs)

        populate = list()
        for index, url in enumerate(url_list):
            populate.append(url)
        populate.sort()

        return {'populated': populate}

    def get_relation_urls(self):
        result_list = list()

        for rel_class in self.get_relations():
            base_url = '/' + rel_class.catalog_key + '/{region}'
            orig_common_ids = set(rel_class.url_kwarg_list) & set(self.url_kwarg_list)
            for possible_url in rel_class.available_urls():
                for kwarg_id in orig_common_ids:
                    if '{'+kwarg_id+'}' in possible_url:
                        result_list.append((base_url + possible_url,rel_class,kwarg_id))

        return result_list

    def get_relations(self):
        result_list = list()

        for possible_class in self.__class__.__base__.__subclasses__():
            common_ids = set(possible_class.url_kwarg_list) & set(self.url_kwarg_list)

            if common_ids and possible_class != self.__class__:
                result_list.append(possible_class)
        return result_list
