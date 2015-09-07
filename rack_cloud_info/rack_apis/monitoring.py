import rack_cloud_info.rack_apis.base

class Monitoring(rack_cloud_info.rack_apis.base.RestfulObject):

    def populate_info(self, identity_obj, **kwargs):
        super().populate_info(identity_obj, link_type='bookmark')
        return None

class MonitoringAgent(rack_cloud_info.rack_apis.base.RestfulObject):

    def populate_info(self, identity_obj, **kwargs):
        result = super().populate_info(identity_obj, update_self=False)
        self['agent_connections'] = result
        return None

    def details_url(self, identity_obj):
        result = identity_obj.service_catalog(name='cloudMonitoring')
        result = [endpoint.get('publicURL') for endpoint in result[0]['endpoints']][0]
        result += '/agents/{agentId}/connections'
        result = result.format(agentId=super()['id'])
        return result


class MonitoringList(rack_cloud_info.rack_apis.base.RestfulList):
    _key = 'values'
    _sub_object = Monitoring


class MonitoringAgentList(rack_cloud_info.rack_apis.base.RestfulList):
    _key = 'values'
    _sub_object = MonitoringAgent
