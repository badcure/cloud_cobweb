
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

