from __future__ import absolute_import

import types
from rack_cloud_info.rack_apis.base import RackAPIBase, RestfulList, \
    RestfulObject
from rack_cloud_info.rack_apis.identity import Identity

class Image(RestfulObject):
    _key = 'image'

    def _fix_link_url(self, value):
        return value.replace('rackspacecloud.com/', 'rackspacecloud.com/v2/')

    def populate_info(self, identity_obj, **kargs):
        super(Image, self).populate_info(identity_obj, link_type='bookmark')
        return None


class Flavor(RestfulObject):
    _key = 'flavor'

    def _fix_link_url(self, value):
        return value.replace('rackspacecloud.com/', 'rackspacecloud.com/v2/')

    def populate_info(self, identity_obj, **kargs):
        super(Flavor, self).populate_info(identity_obj, link_type='bookmark')
        return None


class Server(RestfulObject):
    _key = 'server'

    def populate_info(self, identity_obj, **kwargs):
        super(Server, self).populate_info(identity_obj)

        if isinstance(self.root_dict.get('image'), types.DictionaryType):
            self.root_dict['image'] = Image(self.root_dict['image'])

        if not isinstance(self.root_dict.get('image'), Image):
            raise ValueError("'image' is not defined or not an image {0}".format(type(self.root_dict.get('image'))))

        self.image.populate_info(identity_obj, **kwargs)

        if isinstance(self.root_dict.get('flavor'), types.DictionaryType):
            self.root_dict['flavor'] = Flavor(self.root_dict['flavor'])

        if not isinstance(self.root_dict.get('flavor'), Flavor):
            raise ValueError("'flavor' is not defined or not an flavor {0}".format(type(self.root_dict.get('image'))))

        self.flavor.populate_info(identity_obj, **kwargs)

        return None

    @property
    def image(self):
        return self.root_dict.get('image')

    @property
    def flavor(self):
        return self.root_dict.get('flavor')


class ServersList(RestfulList):
    _key = 'servers'
    _sub_object = Server


class ImagesList(RestfulList):
    _key = 'images'
    _sub_object = Image


class ServersAPI(RackAPIBase):
    _catalog_key = 'cloudServersOpenStack'
    _initial_url_append = '/servers'
    _list_object = ServersList


class ImagesAPI(RackAPIBase):
    _catalog_key = 'cloudImages'
    _initial_url_append = '/images'
    _list_object = ImagesList
