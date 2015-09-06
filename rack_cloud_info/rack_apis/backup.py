import rack_cloud_info.rack_apis.base


class BackupConfiguration(rack_cloud_info.rack_apis.base.RestfulObject):

    def populate_info(self, identity_obj, **kwargs):
        result = super(BackupConfiguration, self).populate_info(identity_obj, update_self=False)
        self['agent_connections'] = result
        return None

    def details_url(self, identity_obj):
        result = identity_obj.service_catalog(name='cloudMonitoring')
        result = [endpoint.get('publicURL') for endpoint in result[0]['endpoints']][0]
        result += '/agents/{agentId}/connections'
        result = result.format(agentId=super()['id'])
        return result



class BackupConfigurationList(rack_cloud_info.rack_apis.base.RestfulList):
    _key = 'values'
    _sub_object = BackupConfiguration


class BackupAPI(rack_cloud_info.rack_apis.base.RackAPIBase):
    _catalog_key = 'cloudBackup'
    _initial_url_append = '/account'

    def backup_agents_list(self, region=None):
        return self.get_list(initial_url_append='/user/agents', data_object=BackupConfigurationList, region=region)

