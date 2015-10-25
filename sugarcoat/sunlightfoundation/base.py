import sugarcoat.base
import copy
import time

import requests


class APIResult(sugarcoat.base.APIResult):
    safe_html = True
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

    def displayable_json_auth_request(self, **kwargs):
        kwargs['params'] = kwargs.get('params', {})
        kwargs['headers'] = kwargs.get('headers', {})
        if self.api_key:
            kwargs['headers']['X-APIKEY'] = self.api_key
        return super().displayable_json_auth_request(**kwargs)