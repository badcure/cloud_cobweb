import sugarcoat.base
import copy
import time

import requests


class RackAPIResult(sugarcoat.base.APIResult):
    tenant_id = None
    region = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_relation_urls(self, api_base_obj):
        rel_urls = api_base_obj.get_relation_urls()
        orig_url_kwargs = self.get_resources()
        orig_url_kwargs['tenant_id'] = self.tenant_id
        for index, url_info in enumerate(rel_urls):
            url_kwargs = copy.deepcopy(orig_url_kwargs)
            url_kwargs['region'] = url_info[1].only_region or url_kwargs.get('region') or self.region
            try:
                url = url_info[0].format(**url_kwargs)
            except KeyError:
                continue
            resource_type = url_info[1].catalog_key
            resource_name = url_info[2]

            if '_UNDEFINED' not in url:
                self.add_relation(url=url, region=url_kwargs['region'], resource_name=resource_name, resource_type=resource_type)

        return

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

class RackAPI(sugarcoat.base.APIBase):
    result_class = RackAPIResult
    _base_url = None
    _identity = None
    only_region = None
    url_kwarg_list = tuple()
    image_url = None

    def __init__(self, identity):
        if not isinstance(identity, Identity):
            raise ValueError("Identity object required")
        self._identity = identity

    @property
    def token(self):
        return self._identity.token

    @classmethod
    def kwargs_from_request(cls, url, api_result, **kwargs):
        result = dict()
        return result

    @classmethod
    def get_catalog_api(cls, catalog_key):
        for possible_class in cls.__subclasses__():
            if possible_class.catalog_key == catalog_key:
                return possible_class
        return None

    def get_auth(self):
        return self._identity

    def displayable_json_auth_request(self, region=None, show_confidential=False, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['X-Auth-Token'] = self.token
        try:
            result = super().displayable_json_auth_request(show_confidential=show_confidential, **kwargs)
        except requests.RequestException as exc:
            result = exc

        if isinstance(result, RackAPIResult):
            result.region = region
            result.tenant_id = self._identity.tenant_id
            result.add_relation_urls(api_base_obj=self)
        return result

    def get_identity(self):
        return self._identity

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

    def public_endpoint_urls(self, region=None):
        if not self._identity.token:
            return []
        result = self._identity.service_catalog(name=self.catalog_key,
                                                region=region)

        return [endpoint.get('publicURL') for endpoint in
                result[0]['endpoints']]

    def get_api_resource(self, region=None, initial_url_append=None, data_object=None, **kwargs):
        if not self._identity.token:
            return {}

        region_url = self.public_endpoint_urls(region=region)[0]

        if '__root__' == initial_url_append.split('/')[1]:
            initial_url_append = '/' + '/'.join(initial_url_append.split('/')[2:])
            region_url = '/'.join(region_url.split('/')[0:3])

        url = "{0}{1}".format(region_url, initial_url_append)

        result = self.displayable_json_auth_request(url=url, region=region, **kwargs)
        if isinstance(data_object, type):
            return data_object(result)

        return result

BASE_URL = 'https://identity.api.rackspacecloud.com'


class Identity(RackAPI):
    _username = None
    _apikey = None
    _auth = None

    def __init__(self, username=None, apikey=None, auth_info=None):
        super().__init__(self)
        self._username = username
        self._apikey = apikey
        self._auth = auth_info
        if self._auth:
            if '_secret_username' in self._auth:
                self._username = self._auth['_secret_username']
                del self._auth['_secret_username']
            if '_secret_apikey' in self._auth:
                self._username = self._auth['_secret_apikey']
                del self._auth['_secret_apikey']

    def authenticate(self, apikey=None):
        """
        http://docs.rackspace.com/auth/api/v2.0/auth-client-devguide/content/POST_authenticate_v2.0_tokens_Token_Calls.html
        """
        apikey = apikey or self.apikey
        payload = self.generate_apikey_auth_payload(apikey=apikey)

        if not payload:
            self._auth = None
            return None

        url = "{0}/v2.0/tokens".format(BASE_URL)
        try:
            result = self.base_request(method='post', data=payload, url=url)
            result.raise_for_status()
            self._auth = result.json()
        except requests.HTTPError:
            pass

    def validate_token(self):
        """
        http://docs.rackspace.com/auth/api/v2.0/auth-client-devguide/content/GET_user-validateToken_v2.0_tokens__tokenId__Token_Calls.html
        :return: bool
        """
        url = "{0}/v2.0/tokens/{1}".format(BASE_URL, self.token)

        result = self._auth_request(url=url)
        result.raise_for_status()
        if result.status_code == 404:
            return False
        result.raise_for_status()
        return True

    def prepare_auth(self):
        if not self._auth:
            self.authenticate()

    @property
    def token(self):
        self.prepare_auth()
        if self._auth and 'access' in self._auth:
            print(self._auth)
            return self._auth['access']['token']['id']
        return None

    @property
    def username(self):
        if self._auth:
            return self._auth['access']['user']['name']
        return self._username

    @property
    def apikey(self):
        return self._apikey

    @property
    def auth_payload(self):
        return self._auth

    @property
    def tenant_id(self):
        if isinstance(self.auth_payload, dict):
            return self.auth_payload['access']['token']['tenant']['id']

    @property
    def tenant_name(self):
        if isinstance(self.auth_payload, dict):
            return self.auth_payload['access']['token']['tenant']['name']

    def generate_apikey_auth_payload(self, apikey=None):
        if not self._username or not (apikey or self._apikey):
            return None

        result = {
            "auth": {
                "RAX-KSKEY:apiKeyCredentials": {
                    "username": self._username,
                    "apiKey": apikey or self._apikey}
            }
        }
        return result

    def service_catalog(self, name=None, catalog_type=None, region=None, region_specific=False):
        if not self._auth:
            return list()
        if region:
            region = region.lower()
        self.prepare_auth()
        result = copy.deepcopy(self._auth['access']['serviceCatalog'])
        if name is not None:
            new_result = list()
            for service in result:
                if name == service['name']:
                    new_result.append(service)
            result = new_result

        if catalog_type is not None:
            new_result = list()
            for service in result:
                if catalog_type == service['type']:
                    new_result.append(service)
            result = new_result

        if region is not None:
            new_result = list()
            allowed_regions = [region, 'no region']
            if region_specific:
                allowed_regions = [region]
            for service in result:
                new_endpoint = list()
                for endpoint in service['endpoints']:
                    if endpoint.get('region', 'no region').lower() in allowed_regions:
                        new_endpoint.append(endpoint)
                service['endpoints'] = new_endpoint
                if service['endpoints']:
                    new_result.append(service)

            result = new_result
        return result

    @property
    def service_catalog_list(self):
        return self.service_catalog()

    def display_safe(self):
        result_dict = copy.deepcopy(self._auth)
        result_dict['access']['token']['id'] = 'MASKED INFO'
        return result_dict

    def roles(self):
        roles = []
        if self._auth:
            for role in self._auth.get('access', {}).get('user', {}).get('roles', []):
                roles.append(role)
        return roles

    def service_catalog_names(self):
        catalog_names = []
        for service_name in self._auth.get('access', {}).get('serviceCatalog', []):
            catalog_names.append(service_name['name'])
        return catalog_names

    @property
    def token_expire_time(self):
        if not self.token:
            return None
        expire_time = self._auth['access']['token']['expires']
        return time.strptime(('.'.join(expire_time.split('.')[0:-1])+" UTC"), '%Y-%m-%dT%H:%M:%S %Z')

    @property
    def token_seconds_left(self):
        if not self.token:
            return -1
        expire_in_seconds = time.mktime(self.token_expire_time)
        return int(expire_in_seconds - time.mktime(time.gmtime()))

    def refresh_auth(self, token=None):
        if not self.tenant_id or not self.token:
            return None

        payload = {'auth': {
            "tenantId": self.tenant_id,
            "token": {
                "id": self.token
            }}}
        result = self._auth_request(method='post', url=BASE_URL + "/v2.0/tokens", data=payload)
        self._auth = result.json()
        return self._auth

    def url_to_catalog_dict(self):
        result_list = []
        if not self._auth:
            return []
        for service in self._auth['access']['serviceCatalog']:
            service_name = service['name']
            for endpoint in service['endpoints']:
                result_list.append((endpoint['publicURL'], (service_name, endpoint.get('region', 'all').lower())))
                result_list.append(('/'.join(endpoint['publicURL'].split('/')[0:3]), (service_name, endpoint.get(
                    'region', 'all').lower(), '__root__')))
        result_list.append(('https://identity.api.rackspacecloud.com/v2.0', ('cloudIdentity', 'all')))
        result_list.append(('https://identity.api.rackspacecloud.com', ('cloudIdentity', 'all', '__root__')))

        return sorted(result_list, key=lambda key_pair: -(len(key_pair[1])*100+len(key_pair[0])))
