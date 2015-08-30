from __future__ import absolute_import

import types
import json
import requests

MASK_HEADERS = ('X-Auth-Token',)

class RestfulList(dict):
    _key = None
    _sub_object = None

    def __init__(self, *args, **kwargs):
        super(RestfulList, self).__init__(*args, **kwargs)
        for index, value in enumerate(self[self._key]):
            self[self._key][index] = self._sub_object(value)

    def __getitem__(self, value):
        if isinstance(value, types.IntType):
            return super(RestfulList, self).__getitem__(self._key)[value]
        return super(RestfulList, self).__getitem__(value)

    def __iter__(self):
        for x in self[self._key]:
            yield x

    def __len__(self):
        return len(self[self._key])


class RestfulObject(dict):
    _key = None
    _need_key = False

    @property
    def root_dict(self):
        if len(self) != 1 or self._key not in self:
            return self
        return self[self._key]

    @property
    def links(self):
        return self.root_dict['links']

    def link(self, type='bookmark'):
        result = None
        for link_info in self.links:
            if link_info.get('rel') == type:
                result = self._fix_link_url(link_info['href'])
                return result

        return result

    def _fix_link_url(self, value):
        return value


class RackAPIBase(object):
    _identity = None

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

    def displable_json_auth_request(self, **kwargs):
        kwargs['headers'] = kwargs.get('headers', {})
        kwargs['headers']['X-Auth-Token'] = self.token
        result = self.display_base_request(**kwargs)
        json_result = result.json()
        json_result['_cloud_information'] = {}
        json_result['_cloud_information']['url'] = result.request.url
        json_result['_cloud_information']['method'] = result.request.method
        json_result['_cloud_information']['headers'] = dict(result.request.headers)
        for header_name in MASK_HEADERS:
            if header_name in json_result['_cloud_information']['headers']:
                json_result['_cloud_information']['headers'][header_name] = '<masked>'
        return json_result

    @staticmethod
    def base_request(method='get', **kwargs):
        if isinstance(kwargs.get('data'), types.DictionaryType):
            kwargs['data'] = json.dumps(kwargs['data'])
            kwargs['headers'] = kwargs.get('headers', {})
            kwargs['headers']['Content-Type'] = 'application/json'

        return getattr(requests, method)(**kwargs)

    @staticmethod
    def display_base_request(method='get', **kwargs):
        return RackAPIBase.base_request(**kwargs)


    @property
    def token(self):
        return self._identity.token
