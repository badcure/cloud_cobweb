from __future__ import absolute_import

import types
from rack_cloud_info.rack_apis.base import RackAPIBase, RestfulList, \
    RestfulObject
from rack_cloud_info.rack_apis.identity import Identity

class User(RestfulObject):
    _key = 'image'

    def _fix_link_url(self, value):
        return value.replace('rackspacecloud.com/', 'rackspacecloud.com/v2/')

    def populate_info(self, identity_obj, **kargs):
        super(User, self).populate_info(identity_obj, link_type='bookmark')
        return None


class UserList(RestfulList):
    _key = 'users'
    _sub_object = User



class UserAPI(RackAPIBase):
    _catalog_key = 'cloudImages'
    _initial_url_append = '/images'
    _list_object = UserList
