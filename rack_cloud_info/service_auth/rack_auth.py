from __future__ import absolute_import

import requests
import json
import copy
AUTH_URL = 'https://identity.api.rackspacecloud.com/v2.0/tokens'

def generic_request(method, *args, **kwargs):
    return getattr(requests, method)(*args, **kwargs)
    pass

class RackAuth(object):
    _username = None
    _apikey = None
    _auth_token = None

    def __init__(self, username, apikey):
        self._username = username
        self._apikey = apikey

    def rackspace_request(self, method, url, **kwargs):
        request_method = getattr(requests, method)
        new_kwargs = kwargs.copy()
        new_kwargs['headers'] = new_kwargs.get('headers', {}).copy()
        if self._auth_token:
            new_kwargs['headers']['X-Auth-Token'] = self.token()

        if 'Content-Type' not in new_kwargs['headers'] and \
                        new_kwargs.get('data') is not None:
            new_kwargs['headers']['Content-Type'] = 'application/json'

        if isinstance(new_kwargs.get('data'), dict):
            new_kwargs['data'] = json.dumps(new_kwargs['data'])

        result = request_method(url, **new_kwargs)
        return result

    def connect(self):
        self._auth_token = None
        payload = {"auth": {
            "RAX-KSKEY:apiKeyCredentials":
                {"username":self._username, "apiKey": self._apikey}}}
        self._auth_token = self.post_request(AUTH_URL, data=payload).json()

    def get_request(self, *args, **kwargs):
        return self.rackspace_request('get', *args, **kwargs)

    def post_request(self, *args, **kwargs):
        return self.rackspace_request('post', *args, **kwargs)

    def access(self):
        return copy.deepcopy(self._auth_token['access'])

    def token(self):
        if not self._auth_token:
            return None
        return self.access()['token']['id']

    def service_catalog(self, name=None, type=None, region=None, region_specific=False):
        result = self.access()['serviceCatalog']
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

    def firstgen_endpoint_url(self):
        result = self.service_catalog(name='cloudServers')
        return [endpoint.get('publicURL') for endpoint in result[0]['endpoints']]

    def nextgen_endpoint_urls(self, region=None):
        result = self.service_catalog(name='cloudServersOpenStack', region=region)
        return [endpoint.get('publicURL') for endpoint in result[0]['endpoints']]

    def atom_hopper_urls_as_dict(self, region=None):
        result = self.service_catalog(name='cloudFeeds', region=region)
        urls = [endpoint.get('publicURL') for endpoint in result[0]['endpoints']]
        result = {}
        for url in urls:
            ah_result = self.get_request(url=url, headers={
                'Accept': 'application/vnd.rackspace.atomsvc+json'})
            result[url] = []
            for ah_endpoint in ah_result.json()['service']['workspace']:
                if not ah_endpoint.get('collection',{}).get('href'):
                    continue
                result[url].append( ah_endpoint.get('collection',{}).get('href'))
            if not result[url]:
                del result[url]
        return result



