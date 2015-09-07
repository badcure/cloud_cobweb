import requests
import rack_cloud_info.rack_apis.base

class Image(rack_cloud_info.rack_apis.base.RestfulObject):
    _key = 'image'

    def _fix_link_url(self, value):
        return value.replace('rackspacecloud.com/', 'rackspacecloud.com/v2/')

    def populate_info(self, identity_obj, **kwargs):
        super().populate_info(identity_obj, link_type='bookmark')
        return None


class Flavor(rack_cloud_info.rack_apis.base.RestfulObject):
    _key = 'flavor'

    def _fix_link_url(self, value):
        return value.replace('rackspacecloud.com/', 'rackspacecloud.com/v2/')

    def populate_info(self, identity_obj, **kwargs):
        super().populate_info(identity_obj, link_type='bookmark')
        return None


class Server(rack_cloud_info.rack_apis.base.RestfulObject):
    _key = 'server'

    def populate_info(self, identity_obj, region=None, **kwargs):
        super().populate_info(identity_obj)

        if isinstance(self.root_dict.get('image'), dict):
            self['image_details'] = Image(self.root_dict['image'])

        self['image_details'].populate_info(identity_obj, **kwargs)

        if isinstance(self.root_dict.get('flavor'), dict):
            self['flavor_details'] = Image(self.root_dict['flavor'])

        self['flavor_details'].populate_info(identity_obj, **kwargs)

        monitoring_url = identity_obj.service_catalog(name='cloudMonitoring')[0]['endpoints'][0]['publicURL']
        monitoring_url += '/views/overview?uri={uri}'.format(uri=self.link(link_type='bookmark'))
        self['monitoring_details'] = identity_obj.displayable_json_auth_request(url=monitoring_url)

        backup_url = identity_obj.service_catalog(name='cloudBackup', region=region)[0]['endpoints'][0]['publicURL']
        backup_url += '/agent/server/{hostServerId}'.format(hostServerId=self.root_dict['id'])
        try:
            self['backup_details'] = identity_obj.displayable_json_auth_request(url=backup_url)
        except requests.HTTPError as http_error:
            self['backup_details'] = http_error.response.url

        return None

    @property
    def image(self):
        return self.root_dict.get('image')

    @property
    def flavor(self):
        return self.root_dict.get('flavor')


class ServersList(rack_cloud_info.rack_apis.base.RestfulList):
    _key = 'servers'
    _sub_object = Server


class ImagesList(rack_cloud_info.rack_apis.base.RestfulList):
    _key = 'images'
    _sub_object = Image

