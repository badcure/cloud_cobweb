import sugarcoat.base


class RackAPIResult(sugarcoat.base.APIResult):
    pass


class RackAPI(sugarcoat.base.APIBase):
    result_class = RackAPIResult

    def __init__(self, identity):
        from .identity import Identity
        if not isinstance(identity, Identity):
            raise ValueError("Identity object required")
        self._identity = identity

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
