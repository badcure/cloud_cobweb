from . import base


class CongressResult(base.APIResult):

    def get_resources(self):
        result = dict()
        return result


class CongressAPI(base.APIBase):
    catalog_key = 'congress'
    result_class = CongressResult
    root_url = 'https://congress.api.sunlightfoundation.com'

def get_catalog_api(catalog_key):
    for possible_class in base.APIBase.__subclasses__():
        if possible_class.catalog_key == catalog_key:
            return possible_class
    return None
