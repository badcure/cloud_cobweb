import requests
import rack_cloud_info.rack_apis.base

class FeedsAPI(rack_cloud_info.rack_apis.base.RackAPIBase):
    _catalog_key = 'cloudFeeds'
    _accept_header_json = 'application/vnd.rackspace.atom+json'

    def get_feed_events(self, feed_type, region):
        list_obj = self.get_list(region)
        for feed_info in list_obj[0]['service']['workspace']:
            if 'collection' in feed_info and feed_info['collection']['title'] == feed_type:
                return self.displayable_json_auth_request(url=feed_info['collection']['href'])
        return None