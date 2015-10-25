import sugarcoat.base
import copy
import time

import requests


class APIResult(sugarcoat.base.APIResult):
    pass


class APIBase(sugarcoat.base.APIBase):
    result_class = APIResult
    api_key = None

    def __init__(self, api_key=None):
        self.api_key = api_key

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

    def displayable_json_auth_request(self, path=None, **kwargs):
        kwargs['params'] = kwargs.get('params', {})
        if self.api_key:
            kwargs['params']['APPID'] = self.api_key
        if path is not None and 'url' not in kwargs:
            kwargs['url'] = 'http://api.openweathermap.org/data/2.5/{0}'.format(path)
        return super().displayable_json_auth_request(**kwargs)