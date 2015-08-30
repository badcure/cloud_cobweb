from __future__ import absolute_import
# http://docs.rackspace.com/auth/api/v2.0/auth-client-devguide/content/QuickStart-000.html

import copy
import types
import requests
from rack_cloud_info.rack_apis.base import RackAPIBase

BASE_URL = 'https://identity.api.rackspacecloud.com/v2.0'

class Identity(RackAPIBase):
    _username = None
    _apikey = None
    _auth = None

    def __init__(self, username, apikey):
        super(Identity, self).__init__()
        self._username = username
        self._apikey = apikey

    def authenticate(self):
        """
        http://docs.rackspace.com/auth/api/v2.0/auth-client-devguide/content/POST_authenticate_v2.0_tokens_Token_Calls.html        """
        payload = self.generate_apikey_auth_payload()
        url = "{0}/tokens".format(BASE_URL)
        result = self.base_request(method='post', data=payload, url=url)
        result.raise_for_status()
        self._auth = result.json()

    def validate_token(self):
        """
        http://docs.rackspace.com/auth/api/v2.0/auth-client-devguide/content/GET_user-validateToken_v2.0_tokens__tokenId__Token_Calls.html
        :return: bool
        """
        url = "{0}/tokens/{1}".format(BASE_URL, self.token)

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


