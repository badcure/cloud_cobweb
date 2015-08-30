from __future__ import absolute_import

import types
from rack_cloud_info.rack_apis.base import RackAPIBase, RestfulList, \
    RestfulObject
from rack_cloud_info.rack_apis.identity import Identity

class Server(RestfulObject):

    def _fix_link_url(self, value):
        return value.replace('rackspacecloud.com/', 'rackspacecloud.com/v2/')


class ServerList(RestfulList):
    _key = 'servers'
    _sub_object = Server
    pass


class ServerAPI(RackAPIBase):

    def nextgen_endpoint_urls(self, region=None):
        result = self._identity.service_catalog(name='cloudServersOpenStack',
                                                region=region)
        return [endpoint.get('publicURL') for endpoint in
                result[0]['endpoints']]

    def server_list(self, region):
        region_url = self.nextgen_endpoint_urls(region=region)[0]
        url = "{0}/servers".format(region_url)
        result = self.displable_json_auth_request(url=url)
        return ServerList(result)

    def server_detail(self, server_obj):
        if not isinstance(server_obj, Server):
            raise ValueError()

        result = self.displable_json_auth_request(url=server_obj.link('bookmark'))
        return Server(result)
