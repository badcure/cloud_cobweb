import sugarcoat.base
import copy
import time

import requests


class APIResult(sugarcoat.base.APIResult):
    pass


class APIBase(sugarcoat.base.APIBase):
    result_class = APIResult

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
