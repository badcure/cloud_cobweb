import copy
import requests
import time
import json

MASK_HEADERS = ('X-Auth-Token',)


class APIResult(dict):
    _identity_obj = None
    additional_url_list = []
    result_type = 'Unknown'
    safe_html = None
    relation_urls = None

    def __init__(self, result, request_headers=None, response_headers=None, url=None, status_code=None,
                 identity_obj=None, **kwargs):
        super().__init__(**kwargs)
        self.relation_urls = list()
        self._identity_obj = identity_obj
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
            response_headers = dict(**result.headers)
        elif isinstance(result, requests.RequestException):
            self['result'] = str(result)
            url = result.request.url
            request_headers = dict(**result.request.headers)
            response_headers = dict()
            status_code = -1
        else:
            self['result'] = result
            status_code = -2

        self['request_headers'] = request_headers
        self['response_headers'] = response_headers
        self['url'] = url
        self['status_code'] = status_code

        for header_name in MASK_HEADERS:
            if header_name in self['request_headers']:
                self['request_headers'][header_name] = '<masked>'
            if header_name in self['response_headers']:
                self['response_headers'][header_name] = '<masked>'

    def pre_html_result(self):
        result = self['result']

        if isinstance(result, dict):
            result['_sugarcoat_relations'] = self.get_sorted_relations()
        return result

    def add_relation(self, url, region=None, resource_id=None, resource_name=None, resource_type=None):
        new_url = dict(href=url, rel='rel')
        if region and region.lower() != 'all':
            new_url['region'] = region
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
            resource_name_list = url_info.get('resource_name', ['unknown_resource'])
            for resource_name in resource_name_list:
                result[resource_type] = result.get(resource_type, dict())
                result[resource_type][resource_name] = result[resource_type].get(resource_name, list())
                result[resource_type][resource_name].append(url_info)
        return result

    @property
    def display_with_relation(self):
        result = self['result']
        if isinstance(result, dict):
            result = copy.deepcopy(self['result'])
            result['_sugarcoat_relations'] = self.get_sorted_relations()
        elif isinstance(result, list):
            result = copy.deepcopy(self['result'])
            result.append({'_sugarcoat_relations': self.get_sorted_relations()})

        return result

    def get_resources(self):
        return {}

    def add_relation_urls(self, api_base_obj, region, tenant_id):
        rel_urls = api_base_obj.get_relation_urls()
        url_kwargs = self.get_resources()
        url_kwargs['tenant_id'] = tenant_id

        for index, url_info in enumerate(rel_urls):
            url_kwargs['region'] = url_info[1].only_region or url_kwargs.get('region') or region

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
    _identity = None
    catalog_key = ''
    _list_object = None
    _accept_header_json = 'application/json'
    url_kwarg_list = list()
    only_region = None
    result_class = APIResult

    def _auth_request(self, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['X-Auth-Token'] = self.token
        result = self.display_base_request(**kwargs)
        return result

    def displayable_json_auth_request(self, region=None, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['X-Auth-Token'] = self.token
        if self._accept_header_json:
            kwargs['headers']['Accept'] = self._accept_header_json
        start_time = time.time()
        try:
            result = self.display_base_request(**kwargs)
        except requests.RequestException as exc:
            result = exc

        end_time = time.time()
        json_result = None
        if issubclass(self.result_class, APIResult):
            json_result = self.result_class(result, response_time=end_time-start_time, identity_obj=self._identity, region=region)
            json_result.add_relation_urls(self, region, self._identity.tenant_id)

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
        result = self._identity.service_catalog(name=self.catalog_key,
                                                region=region)
        return [endpoint.get('publicURL') for endpoint in
                result[0]['endpoints']]


    def get_api_resource(self, region=None, initial_url_append=None, data_object=None):
        region_url = self.public_endpoint_urls(region=region)[0]

        if '__root__' == initial_url_append.split('/')[1]:
            initial_url_append = '/' + '/'.join(initial_url_append.split('/')[2:])
            region_url = '/'.join(region_url.split('/')[0:3])

        url = "{0}{1}".format(region_url, initial_url_append)

        result = self.displayable_json_auth_request(url=url, region=region)
        if isinstance(data_object, type):
            return data_object(result)

        return result


    @classmethod
    def available_urls(cls):
        return []

    def filled_out_urls(self, region, **kwargs):

        for kwarg_name in self.url_kwarg_list:
            kwargs[kwarg_name] = kwargs.get(kwarg_name, 'KEY_{0}_UNDEFINED'.format(kwarg_name))

        url_list = self.available_urls()
        for index, url in enumerate(url_list):
            url_list[index] = '/{0}/{1}{2}'.format(self.catalog_key, self.only_region or region, url).format(**kwargs)

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
                        result_list.append((base_url + possible_url,rel_class,orig_common_ids))

        return result_list

    def get_relations(self):
        result_list = list()

        for possible_class in self.__class__.__base__.__subclasses__():
            common_ids = set(possible_class.url_kwarg_list) & set(self.url_kwarg_list)

            if common_ids and possible_class != self.__class__:
                result_list.append(possible_class)
        return result_list