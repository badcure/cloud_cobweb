import sugarcoat.rackspace_api.base


class OrachastrationResult(sugarcoat.rackspace_api.base.RackAPIResult):

    def get_resources(self):
        result = dict()
        if 'resource_types' in self['result']:
            for index, entry in enumerate(self['result']['resource_types']):
                result['heat_resource_type'] = entry

        return result



class MonitoringResult(sugarcoat.rackspace_api.base.RackAPIResult):

    def get_resources(self):
        result = dict()
        result['region'] = 'DFW'
        if 'values' in self['result']:
            for monitor_obj in self['result']['values']:
                if 'checks' in monitor_obj:
                    for check in monitor_obj['checks']:
                        result['check_id'] = check['id']
                        result['check_type'] = check['type']
                if 'entity' in monitor_obj:
                    result['entity_id'] = monitor_obj['entity']['id']
                    result['server_uri'] = monitor_obj['entity']['uri']
                    result['entity_id'] = monitor_obj['entity']['id']
        elif 'uri' in self['result']:
            result['server_uri'] = self['result']['uri']
            result['entity_id'] = self['result']['id']

        return result


class LoadBalancerResult(sugarcoat.rackspace_api.base.RackAPIResult):

    pass


class BackupResult(sugarcoat.rackspace_api.base.RackAPIResult):

    def get_resources(self):
        result = dict()
        if isinstance(self['result'], list):
            for entry in self['result']:
                if 'HostServerId' in entry:
                    result['server_id'] = entry['HostServerId']
                if 'MachineAgentId' in entry:
                    result['machine_agent_id'] = entry['MachineAgentId']
                if 'SourceMachineAgentId' in entry:
                    result['machine_agent_id'] = entry['SourceMachineAgentId']
                if 'SourceMachineAgentId' in entry:
                    result['machine_agent_id'] = entry['SourceMachineAgentId']


        return result


class ServerResult(sugarcoat.rackspace_api.base.RackAPIResult):

    def get_resources(self):
        result = dict()
        if 'server' in self['result']:
            result['server_id'] = self['result']['server']['id']
            result['user_id'] = self['result']['server']['user_id']

            result['flavor_id'] = self['result']['server']['flavor']['id']
            result['image_id'] = self['result']['server']['image']['id']
            for link in self['result']['server']['links']:
                if link['rel'] == 'bookmark':
                    result['server_uri'] = link['href']
        return result


class ServersAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudServersOpenStack'
    url_kwarg_list = ('server_id', 'flavor_id', 'attachment_id', 'image_id', 'metadata_key', 'server_uri',
                       'flavor_class', 'server_request_id')
    result_class = ServerResult

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/servers')
        url_list.append('/servers/detail')
        url_list.append('/servers/{server_id}')
        url_list.append('/os-keypairs')
        url_list.append('/servers/{server_id}/ips')
        url_list.append('/servers/{server_id}/ips/networkLabel')
        url_list.append('/servers/{server_id}/os-volume_attachments')
        url_list.append('/servers/{server_id}/os-volume_attachments/{attachment_id}')
        url_list.append('/flavors')
        url_list.append('/flavors/detail')
        url_list.append('/flavors/{flavor_id}')
        url_list.append('/images/detail')
        url_list.append('/images/{image_id}')
        url_list.append('/servers/{server_id}/metadata')
        url_list.append('/servers/{server_id}/metadata/{metadata_key}')
        url_list.append('/limits')
        url_list.append('/flavors/{flavor_class}/os-extra_specs')
        url_list.append('/servers/{server_id}/os-instance-actions')
        url_list.append('/servers/{server_id}/os-instance-actions/{server_request_id}')
        url_list.append('/os-networksv2')
        return url_list


class FeedsAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudFeeds'
    url_kwarg_list = ('server_id', 'entity_id', 'user_id', 'container_name', 'machine_agent_id', 'username', 'load_balancer_id')
    _accept_header_json = 'application/vnd.rackspace.atom+json'
    feed_list_payload = dict()
    feed_region = 'all'
    feed_task = None


    def get_feed_events(self, feed_type, region):
        result_obj = self.get_api_resource(region)
        for feed_info in result_obj['result']['service']['workspace']:
            if 'collection' in feed_info and feed_info['collection']['title'] == feed_type:
                return [self.displayable_json_auth_request(url=feed_info['collection']['href'])]
        return None

    def public_endpoint_urls(self, region=None, version=None):
        if not self.feed_task:
            return super().public_endpoint_urls(region, version)
        for feed_entry in self.feed_list_payload.get('service', {}).get('workspace', []):
            if feed_entry['title'] == self.feed_task:
                return [feed_entry['collection']['href']]
        return None

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/__root__/nova/events/{tenant_id}/?search=(AND(cat=rid:{server_id}))')
        url_list.append('/__root__/monitoring/events/{tenant_id}/?search=(AND(cat=rid:{entity_id}))')
        url_list.append('/__root__/identity/events/{tenant_id}/?search=(AND(cat=rid:{user_id}))')
        url_list.append('/__root__/backup/events/{tenant_id}?search=(AND(cat=rid:{machine_agent_id}))')
        url_list.append('/__root__/feeds_access/events/{tenant_id}/?search=(AND(cat=tid:{username}))')
        url_list.append('/__root__/lbaas/events/{tenant_id}/?search=(AND(cat=rid:{load_balancer_id}))')

        return url_list


class BackupAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudBackup'
    url_kwarg_list = ('server_id', 'restore_id', 'machine_agent_id', 'backup_configuration_id', 'backup_id')
    result_class = BackupResult

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/agent/{machine_agent_id}')
        url_list.append('/agent/server/{server_id}')
        url_list.append('/user/agents')
        url_list.append('/backup-configuration')
        url_list.append('/backup-configuration/{backup_configuration_id}')
        url_list.append('/backup-configuration/system/{machine_agent_id}')
        url_list.append('/backup/{backup_id}')
        url_list.append('/backup/completed/{backup_configuration_id}')
        url_list.append('/backup/report/{backup_id}')
        url_list.append('/restore/files/{restore_id}')
        url_list.append('/backup/availableforrestore')
        url_list.append('/restore/{restore_id}')
        url_list.append('/restore/report/{restore_id}')
        url_list.append('/system/activity/{machine_agent_id}')
        url_list.append('/activity')
        return url_list


class MonitoringAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudMonitoring'
    only_region = 'all'
    url_kwarg_list = ('entity_id', 'check_id', 'metric_name', 'check_type_id', 'monitoring_zone_id', 'alarm_id',
                       'notification_plan_id', 'notification_id', 'alarm_example_id', 'suppession_id', 'server_uri')
    result_class = MonitoringResult

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/limits')
        url_list.append('/account')
        url_list.append('/audits')
        url_list.append('/usage')
        url_list.append('/entities')
        url_list.append('/entities/{entity_id}')
        url_list.append('/entities/{entity_id}/checks')
        url_list.append('/entities/{entity_id}/checks/{check_id}')
        url_list.append('/entities/{entity_id}/checks/{check_id}/metrics')
        url_list.append('/entities/{entity_id}/checks/{check_id}/metrics/{metric_name}/plot')
        url_list.append('/check_types')
        url_list.append('/check_types/{check_type_id}')
        url_list.append('/monitoring_zones')
        url_list.append('/monitoring_zones/{monitoring_zone_id}')
        url_list.append('/entities/{entity_id}/alarms')
        url_list.append('/entities/{entity_id}/alarms/{alarm_id}')
        url_list.append('/entities/{entity_id}/alarms/{alarm_id}/notification_history')
        url_list.append('/entities/{entity_id}/alarms/{alarm_id}/notification_history/{check_id}')
        url_list.append('/entities/{entity_id}/alarms/{alarm_id}/notification_history/{check_id}/uuid')
        url_list.append('/notification_plans')
        url_list.append('/notification_plans/{notification_plan_id}')
        url_list.append('/notifications')
        url_list.append('/notifications/{notification_id}')
        url_list.append('/notification_types')
        url_list.append('/views/overview')
        url_list.append('/views/overview?entity={entity_id}')
        url_list.append('/views/overview?uri={server_uri}')
        url_list.append('/changelogs/alarms')
        url_list.append('/alarm_examples')
        url_list.append('/alarm_examples/{alarm_example_id}')
        url_list.append('/suppression_logs')
        url_list.append('/suppressions/{suppession_id}')
        return url_list

    @classmethod
    def kwargs_from_request(cls, url, api_result,  **kwargs):
        result = super().kwargs_from_request(url, api_result, **kwargs)

        path_list = url.split('/')
        path_list.reverse()
        current_step = path_list.pop()

        if 'entities' == current_step:
            if path_list and path_list[-1]:
                result['entity_id'] = path_list.pop()
            if len(path_list) >= 2 and path_list[-1] == 'checks':
                path_list.pop()
                result['check_id'] = path_list.pop()

        return result


class OrchastrationAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudOrchestration'
    url_kwarg_list = ('stack_name', 'stack_id', 'heat_resource_name', 'heat_event_id', 'heat_resource_type', 'server_id')
    result_class = OrachastrationResult

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/stacks​')
        url_list.append('/stacks/{stack_name}')
        url_list.append('/stacks/{stack_name}/{stack_id}')
        url_list.append('/stacks/{stack_name}/resources')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources​')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources/{heat_resource_name}')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources/{heat_resource_name}/metadata')
        url_list.append('/resource_types')
        url_list.append('/resource_types/{heat_resource_type}')
        url_list.append('/resource_types/{heat_resource_type}/template')
        url_list.append('/stacks/{stack_name}/events')
        url_list.append('/stacks/{stack_name}/{stack_id}/events')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources/{heat_resource_name}/events​')
        url_list.append('/stacks/{stack_name}/{stack_id}/resources/{heat_resource_name}/events/{heat_event_id}')
        url_list.append('/build_info')


        return url_list


class CloudFilesAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudFiles'
    url_kwarg_list = ('container_name', 'object')

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/​')
        url_list.append('/{container_name}')
        url_list.append('/{container_name}/{object}')
        return url_list


class CloudFilesCDNAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudFilesCDN'
    url_kwarg_list = ()

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/​')
        return url_list


class RackspaceCDNAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'rackCDN'
    url_kwarg_list = ('flavor_id',)
    only_region = 'DFW'

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/')
        url_list.append('/ping')
        url_list.append('/health')
        url_list.append('/services')
        url_list.append('/flavors/{flavor_id}')

        return url_list


class CloudImages(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudImages'
    url_kwarg_list = ('image_id', 'member_id', 'task_id')

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/')
        url_list.append('/images')
        url_list.append('/images/{image_id}')
        url_list.append('/images/{image_id}/members')
        url_list.append('/images/{image_id}/members/{member_id}')
        url_list.append('/tasks')
        url_list.append('/tasks/{task_id}')
        url_list.append('/schemas/images')
        url_list.append('/schemas/image')
        url_list.append('/schemas/members')
        url_list.append('/schemas/member')
        url_list.append('/schemas/tasks')
        url_list.append('/schemas/task')

        return url_list


class CloudServersFirstGenAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudServers'
    url_kwarg_list = ('firstgen_id', 'firstgen_image_id', 'firstgen_ip_group_id')
    only_region = 'all'
    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/')
        url_list.append('/servers')
        url_list.append('/servers/detail')
        url_list.append('/servers/{firstgen_id}')
        url_list.append('/servers/{firstgen_id}/ips')
        url_list.append('/servers/{firstgen_id}/ips/public')
        url_list.append('/servers/{firstgen_id}/ips/private')
        url_list.append('/flavors')
        url_list.append('/flavors/detail')
        url_list.append('/images')
        url_list.append('/images/detail')
        url_list.append('/images/{firstgen_image_id}')
        url_list.append('/servers/{firstgen_id}/backup_schedule')
        url_list.append('/shared_ip_groups')
        url_list.append('/shared_ip_groups/detail')
        url_list.append('/shared_ip_groups/{firstgen_ip_group_id}')

        return url_list


class CloudSitesAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudSites'
    url_kwarg_list = ()

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/​')
        return url_list


class CloudNetworksAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudNetworks'
    url_kwarg_list = ()

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/​')
        url_list.append('/networks​')
        url_list.append('/subnets')
        url_list.append('/ports')
        return url_list


class CloudLoadBalancersAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudLoadBalancers'
    url_kwarg_list = ('load_balancer_id', 'load_balancer_node_id', 'load_balancer_meta_id')
    result_class = LoadBalancerResult

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/​')
        url_list.append('/loadbalancers')
        url_list.append('/loadbalancers/{load_balancer_id}')
        url_list.append('/loadbalancers/{load_balancer_id}/errorpage')
        url_list.append('/loadbalancers/{load_balancer_id}/nodes')
        url_list.append('/loadbalancers/{load_balancer_id}/nodes/{load_balancer_node_id}')
        url_list.append('/loadbalancers/{load_balancer_id}/nodes/events')
        url_list.append('/loadbalancers/{load_balancer_id}/virtualips')
        url_list.append('/loadbalancers/alloweddomains')
        url_list.append('/loadbalancers/{load_balancer_id}/usage')
        url_list.append('/loadbalancers/usage​')
        url_list.append('/loadbalancers/{load_balancer_id}/usage/current')
        url_list.append('/loadbalancers/billable​')
        url_list.append('/loadbalancers/{load_balancer_id}/accesslist')
        url_list.append('/loadbalancers/{load_balancer_id}/healthmonitor')
        url_list.append('/loadbalancers/{load_balancer_id}/sessionpersistence')
        url_list.append('/loadbalancers/{load_balancer_id}/connectionlogging')
        url_list.append('/loadbalancers/{load_balancer_id}/connectionthrottle')
        url_list.append('/loadbalancers/{load_balancer_id}/contentcaching')
        url_list.append('/loadbalancers/protocols')
        url_list.append('/loadbalancers/algorithms')
        url_list.append('/loadbalancers/{load_balancer_id}/ssltermination')
        url_list.append('/loadbalancers/{load_balancer_id}/metadata')
        url_list.append('/loadbalancers/{load_balancer_id}/metadata/{load_balancer_meta_id}')
        url_list.append('/loadbalancers/{load_balancer_id}/nodes/{load_balancer_node_id}/metadata')
        url_list.append('/loadbalancers/{load_balancer_id}/nodes/{load_balancer_node_id}/metadata/{load_balancer_meta_id}')

        return url_list

    @classmethod
    def kwargs_from_request(cls, url, api_result,  **kwargs):
        result = super().kwargs_from_request(url, api_result, **kwargs)

        path_list = url.split('/')
        path_list.reverse()
        if path_list[-1] != 'loadbalancers':
            return result
        path_list.pop()
        if path_list:
            try:
                result['load_balancer_id'] = int(path_list.pop())
            except ValueError:
                pass
        return result


class IdentityAPI(sugarcoat.rackspace_api.base.RackAPI):
    catalog_key = 'cloudIdentity'
    _base_url = 'https://identity.api.rackspacecloud.com'
    only_region = 'all'
    url_kwarg_list = ('user_id')

    @classmethod
    def available_urls(cls):
        url_list = list()
        url_list.append('/​')
        return url_list

    def get_api_resource(self, region=None, initial_url_append=None, data_object=None, **kwargs):
        root_url = self._base_url

        if '__root__' == initial_url_append.split('/')[1]:
            initial_url_append = '/' + '/'.join(initial_url_append.split('/')[2:])

            url = "{0}{1}".format(root_url, initial_url_append)
        else:
            url = "{0}/v2.0{1}".format(root_url, initial_url_append)

        result = self.displayable_json_auth_request(url=url, region=region, **kwargs)
        if isinstance(data_object, type):
            return data_object(result)

        return result

def get_catalog_api(catalog_key):
    for possible_class in sugarcoat.rackspace_api.base.RackAPI.__subclasses__():
        if possible_class.catalog_key == catalog_key:
            return possible_class
    return None



