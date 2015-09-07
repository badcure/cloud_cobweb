import copy
import time
import requests
import rack_cloud_info.rack_apis.base

BASE_URL = 'https://identity.api.rackspacecloud.com'

class Identity(rack_cloud_info.rack_apis.base.RackAPIBase):
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
        url = "{0}/v2.0/tokens".format(BASE_URL)
        result = self.base_request(method='post', data=payload, url=url)
        result.raise_for_status()
        self._auth = result.json()

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
        try:
            self.prepare_auth()
        except requests.HTTPError as http_exc:
            print("Error response {status_code}: {message}".format(status_code=http_exc.response.status_code,
                                                                   message=http_exc.response.text))
            return None
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
        result = {
            "auth": {
                "RAX-KSKEY:apiKeyCredentials":{
                    "username": self._username,
                    "apiKey": apikey or self._apikey}
            }
        }
        return result

    def service_catalog(self, name=None, catalog_type=None, region=None, region_specific=False):
        if region:
            region=region.upper()
        self.prepare_auth()
        result = copy.deepcopy(self._auth['access']['serviceCatalog'])
        if name is not None:
            new_result = []
            for service in result:
                if name == service['name']:
                    new_result.append(service)
            result = new_result

        if catalog_type is not None:
            new_result = []
            for service in result:
                if catalog_type == service['type']:
                    new_result.append(service)
            result = new_result

        if region is not None:
            new_result = []
            allowed_regions = [region, None]
            if region_specific:
                allowed_regions = [region]
            for service in result:
                new_endpoint = []
                for endpoint in service['endpoints']:
                    if endpoint.get('region') in allowed_regions:
                        new_endpoint.append(endpoint)
                service['endpoints'] = new_endpoint
                if service['endpoints']:
                    new_result.append(service)

            result = new_result
        return result

    def display_safe(self):
        result_dict = copy.deepcopy(self._auth)
        result_dict['access']['token']['id'] = '<masked>'
        return result_dict

    def roles(self):
        roles = []
        for role in self._auth.get('access', {}).get('user', {}).get('roles', []):
            roles.append(role)
        return roles

    def service_catalog_names(self):
        catalog_names = []
        for service_name in self._auth.get('access', {}).get('serviceCatalog', []):
            catalog_names.append(service_name['name'])
        return catalog_names

    def token_expire_time(self):
        expire_time = self._auth['access']['token']['expires']
        if self.token:
            return time.strptime(('.'.join(expire_time.split('.')[0:-1])+" UTC"),'%Y-%m-%dT%H:%M:%S %Z')
        return None

    def token_seconds_left(self):
        if not self.token_expire_time():
            return None
        expire_in_seconds = time.mktime(self.token_expire_time())
        return int(expire_in_seconds - time.mktime(time.gmtime()))

    def refresh_auth(self):
        payload = {'auth': {
            "tenantId": self.tenant_id,
            "token": {
                "id": self.token
            }}}
        result = self._auth_request(method='post', url=BASE_URL + "/v2.0/tokens", data=payload)
        self._auth = result.json()
        return self._auth


class User(rack_cloud_info.rack_apis.base.RestfulObject):
    _key = 'user'

    def _fix_link_url(self, value):
        return value.replace('rackspacecloud.com/', 'rackspacecloud.com/v2/')

    def populate_info(self, identity_obj, region=None, **kwargs):
        self._details_url = BASE_URL + "/v2.0/users/{userId}/OS-KSADM/credentials/"
        self._details_url = self._details_url.format(userId=self.root_dict['id'])
        result = super().populate_info(identity_obj, update_self=False)
        self['credentials'] = result

        self._details_url = BASE_URL + "/v2.0/users/{userId}/roles"
        self._details_url = self._details_url.format(userId=self.root_dict['id'])
        result = super().populate_info(identity_obj, update_self=False)
        self['roles'] = result

        self._details_url = BASE_URL + "/v2.0/users/{userId}/RAX-AUTH/multi-factor/mobile-phones"
        self._details_url = self._details_url.format(userId=self.root_dict['id'])
        result = super().populate_info(identity_obj, update_self=False)
        self['multi-authenticate'] = result

        return None


class UserList(rack_cloud_info.rack_apis.base.RestfulList):
    _key = 'users'
    _sub_object = User


class UserAPI(rack_cloud_info.rack_apis.base.RackAPIBase):
    _catalog_key = None
    _initial_url_append = None

    _list_object = UserList

    def get_list(self, **kwargs):
        result_list = []
        region_url = BASE_URL + '/v2.0/users'
        url = region_url
        while url:
            result = self.displayable_json_auth_request(url=url)
            result_list.append(result)
            if result_list[-1].get('next'):
                url = BASE_URL + result_list[-1].get('next')
                url = url.replace('/v2/v2', '/v2')
            else:
                url = None

        return self._list_object(result_list)
