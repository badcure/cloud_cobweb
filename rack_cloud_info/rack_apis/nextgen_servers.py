from __future__ import absolute_import

import types
import requests
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

    def populate_info(self, identity_obj, region=None, **kwargs):
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

        monitoring_url = identity_obj.service_catalog(name='cloudMonitoring')[0]['endpoints'][0]['publicURL']
        monitoring_url += '/views/overview?uri={uri}'.format(uri=self.link(type='bookmark'))
        self['monitoring'] = identity_obj.displable_json_auth_request(url=monitoring_url)

        backup_url = identity_obj.service_catalog(name='cloudBackup', region=region)[0]['endpoints'][0]['publicURL']
        print region
        backup_url += '/agent/server/{hostServerId}'.format(hostServerId=self.root_dict['id'])
        print backup_url
        try:
            self['backup'] = identity_obj.displable_json_auth_request(url=backup_url)
        except requests.HTTPError as http_error:
            self['backup'] = http_error.response.url

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
