from __future__ import absolute_import

import json
import requests

MASK_HEADERS = ('X-Auth-Token',)

class RestfulList(list):
    _key = None
    _sub_object = None

    def populate_info(self, identity_obj, region=None):
        from rack_cloud_info.rack_apis.identity import Identity

        if not isinstance(identity_obj, Identity):
            raise ValueError('Expected Identity obj, got {0}'.format(type(identity_obj)))

        for result in self:
            if isinstance(result, dict):
                result = result[self._key]
            if not isinstance(result, list):
                raise ValueError("Result is not list, type is {0}".format(type(result)))

            for index, result_obj in enumerate(result):
                if not isinstance(result_obj, self.sub_object_class):
                    result[index] = self._sub_object(result_obj)
                result[index].populate_info(identity_obj, region=region)

    @property
    def sub_object_class(self):
        return self._sub_object

    @sub_object_class.setter
    def sub_object_class(self, value):
        if not issubclass(value, RestfulObject):
            raise ValueError("Class is not a type of RestfulObject: {0}".format(type(value)))
        self._sub_object = value


class RestfulObject(dict):
    _key = ''
    _need_key = False
    _details_url = None
    _update_self = True

    @property
    def root_dict(self):
        if isinstance(super().get(self._key), dict):
            return super().get(self._key)

        return super()

    def link(self, link_type='bookmark'):
        for link_info in self.root_dict.get('links', list()):
            if link_info.get('rel') == link_type:
                result = self._fix_link_url(link_info['href'])
                return result

        return None

    def _fix_link_url(self, value):
        return value

    def populate_info(self, identity_obj, link_type='self', update_self=True, region=None, **kwargs):
        from rack_cloud_info.rack_apis.identity import Identity
        if not isinstance(identity_obj, Identity):
            raise ValueError('Expected Identity obj, got {0}'.format(type(identity_obj)))
        result = identity_obj.displayable_json_auth_request(url=self.details_url(identity_obj=identity_obj),method='get')

        # Delete everything current
        if update_self:
            self_key_list = list(self.keys())
            for self_key in self_key_list:
                del self[self_key]
            super().update(result)
            return None
        return result

    def details_url(self, **kwargs):
        if not self._details_url:
            self._details_url = self._details_url or self.link(link_type='self') or self.link(link_type='bookmark')
        return self._details_url


class RackAPIBase(object):
    _identity = None
    _catalog_key = ''
    _initial_url_append = None
    _list_object = None
    _accept_header_json = 'application/json'

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
        result = self.display_base_request(**kwargs)
        json_result = dict()
        try:
            json_result.update(result.json())
        except ValueError:
            json_result['result'] = result.text

        json_result['_cloud_info_request'] = {}
        json_result['_cloud_info_request']['url'] = result.request.url
        json_result['_cloud_info_request']['method'] = result.request.method
        json_result['_cloud_info_request']['headers'] = dict(result.request.headers)
        for header_name in MASK_HEADERS:
            if header_name in json_result['_cloud_info_request']['headers']:
                json_result['_cloud_info_request']['headers'][header_name] = '<masked>'
        json_result['_cloud_info_response'] = dict()
        json_result['_cloud_info_response']['status_code'] = result.status_code

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

    def nextgen_endpoint_urls(self, region=None):
        result = self._identity.service_catalog(name=self._catalog_key,
                                                region=region)
        return [endpoint.get('publicURL') for endpoint in
                result[0]['endpoints']]

    def get_list(self, region=None, initial_url_append=None, data_object=None):
        result_list = []
        initial_url_append = initial_url_append or self._initial_url_append or ''

        region_url = self.nextgen_endpoint_urls(region=region)[0]
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
        if not issubclass(value, RestfulList):
            raise ValueError("Class is not a type of RestfulObject: {0}".format(type(value)))
        self._list_object = value
