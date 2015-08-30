from __future__ import absolute_import
# http://docs.rackspace.com/auth/api/v2.0/auth-client-devguide/content/QuickStart-000.html

import copy
import types
import requests
from rack_cloud_info.rack_apis.base import RackAPIBase, RestfulList, \
    RestfulObject

BASE_URL = 'https://identity.api.rackspacecloud.com'

class Identity(RackAPIBase):
    _username = None
    _apikey = None
    _auth = None

    def __init__(self, username, apikey):
        self._username = username
        self._apikey = apikey

    def authenticate(self):
        """
        http://docs.rackspace.com/auth/api/v2.0/auth-client-devguide/content/POST_authenticate_v2.0_tokens_Token_Calls.html        """
        payload = self.generate_apikey_auth_payload()
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
        self.prepare_auth()
        if self._auth:
            return self._auth['access']['token']['id']
        return None

    def generate_apikey_auth_payload(self):
        result = {
            "auth": {
                "RAX-KSKEY:apiKeyCredentials":{
                    "username": self._username,
                    "apiKey": self._apikey}
            }
        }
        return result

    def service_catalog(self, name=None, type=None, region=None, region_specific=False):
        self.prepare_auth()
        result = copy.deepcopy(self._auth['access']['serviceCatalog'])
        if name is not None:
            new_result = []
            for service in result:
                if name == service['name']:
                    new_result.append(service)
            result = new_result

        if type is not None:
            new_result = []
            for service in result:
                if type == service['type']:
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


class User(RestfulObject):
    _key = 'user'

    def _fix_link_url(self, value):
        return value.replace('rackspacecloud.com/', 'rackspacecloud.com/v2/')

    def populate_info(self, identity_obj, **kargs):
        self._details_url = BASE_URL + "/v2.0/users/{userId}/OS-KSADM/credentials/"
        self._details_url = self._details_url.format(userId=self.root_dict['id'])
        result = super(User, self).populate_info(identity_obj, update_self=False)
        self['credentials'] = result

        self._details_url = BASE_URL + "/v2.0/users/{userId}/roles"
        self._details_url = self._details_url.format(userId=self.root_dict['id'])
        result = super(User, self).populate_info(identity_obj, update_self=False)
        self['roles'] = result

        self._details_url = BASE_URL + "/v2.0/users/{userId}/RAX-AUTH/multi-factor/mobile-phones"
        self._details_url = self._details_url.format(userId=self.root_dict['id'])
        result = super(User, self).populate_info(identity_obj, update_self=False)
        self['multi-authenticate'] = result

        return None


class UserList(RestfulList):
    _key = 'users'
    _sub_object = User


class UserAPI(RackAPIBase):
    _catalog_key = None
    _initial_url_append = None

    _list_object = UserList

    def get_list(self, **kwargs):
        result_list = []
        region_url = BASE_URL + '/v2.0/users'
        url = region_url
        while url:
            print "Next url " + url
            result = self.displable_json_auth_request(url=url)
            result_list.append(result)
            if result_list[-1].get('next'):
                url = BASE_URL + result_list[-1].get('next')
                url = url.replace('/v2/v2', '/v2')
            else:
                url = None

        return self._list_object(result_list)
