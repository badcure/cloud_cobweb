import copy
import time

import requests
import sugarcoat.rackspace_api.base


BASE_URL = 'https://identity.api.rackspacecloud.com'


class Identity(sugarcoat.rackspace_api.base.RackAPI):
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
        result = self.base_request(method='post', data=payload, url=url)
        try:
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
        if self._auth:
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
            region = region.upper()
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
            allowed_regions = [region, None]
            if region_specific:
                allowed_regions = [region]
            for service in result:
                new_endpoint = list()
                for endpoint in service['endpoints']:
                    if endpoint.get('region') in allowed_regions:
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
        result_dict['access']['token']['id'] = '<masked>'
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

    def refresh_auth(self):
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
                result_list.append((endpoint['publicURL'], (service_name, endpoint.get('region', 'all'))))
                result_list.append(('/'.join(endpoint['publicURL'].split('/')[0:3]), (service_name, endpoint.get(
                    'region', 'all'), '__root__')))
            result_list.append(('https://identity.api.rackspacecloud.com/v2.0', ('cloudIdentity', 'all')))
            result_list.append(('https://identity.api.rackspacecloud.com', ('cloudIdentity', 'all', '__root__')))

        return sorted(result_list, key=lambda key_pair: -(len(key_pair[1])*100+len(key_pair[0])))
