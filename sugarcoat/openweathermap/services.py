from . import base


class CurrentWeatherResult(base.APIResult):

    def get_resources(self):
        result = dict()
        return result


class CurrentWeatherAPI(base.APIBase):
    catalog_key = 'currentWeather'
    result_class = CurrentWeatherResult

def get_catalog_api(catalog_key):
    for possible_class in base.APIBase.__subclasses__():
        if possible_class.catalog_key == catalog_key:
            return possible_class
    return None
