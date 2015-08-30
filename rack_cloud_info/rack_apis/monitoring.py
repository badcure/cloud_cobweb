from __future__ import absolute_import

import types
from rack_cloud_info.rack_apis.base import RackAPIBase, RestfulList, \
    RestfulObject
from rack_cloud_info.rack_apis.identity import Identity

class Monitoring(RestfulObject):

    def populate_info(self, identity_obj, **kargs):
        super(Monitoring, self).populate_info(identity_obj, link_type='bookmark')
        return None

class MonitoringAgent(RestfulObject):

    def populate_info(self, identity_obj, **kargs):
        result = super(MonitoringAgent, self).populate_info(identity_obj, update_self=False)
        self['agent_connections'] = result
        return None

    def details_url(self, identity_obj):
        result = identity_obj.service_catalog(name='cloudMonitoring')
        result = [endpoint.get('publicURL') for endpoint in result[0]['endpoints']][0]
        result += '/agents/{agentId}/connections'
        result = result.format(agentId=self['id'])
        print result
        return result



class MonitoringList(RestfulList):
    _key = 'values'
    _sub_object = Monitoring


class MonitoringAgentList(RestfulList):
    _key = 'values'
    _sub_object = MonitoringAgent


class MonitoringAPI(RackAPIBase):
    _catalog_key = 'cloudMonitoring'
    _initial_url_append = '/account'
    _list_object = MonitoringList

    def monitoring_agent_list(self):
        return self.get_list(initial_url_append='/agents', data_object=MonitoringAgentList)
