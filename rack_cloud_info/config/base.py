from __future__ import absolute_import

import types
import os
import yaml
import redis

DEFAULT_CONFIG = '/etc/rack_cloud_info.yaml'


class Settings(object):
    _redis_conn = None
    _prefix = None
    _delimiter = None
    _config_dict = None

    def __init__(self, config_dict, _redis_conn=None, _prefix=None,
                 delimiter='.'):
        if not isinstance(config_dict, types.DictionaryType):
            raise ValueError("Dictionary type required.")

        self._redis_conn = _redis_conn
        self._prefix = _prefix
        if self._prefix is None:
            self._prefix = "config"
        self._delimiter = delimiter
        self._config_dict = config_dict

        if self._redis_conn is None:
            try:
                redis_config = config_dict['redis']
                redis_host = redis_config['host']
                redis_port = redis_config['port']
                self._redis_conn = redis.Redis(host=redis_host,
                                               port=redis_port)
            except KeyError:
                raise KeyError("redis config is required, with host(string) "
                               "and port(integer) attributes")

    def get(self, key, default=None):
        # Check redis first
        new_key = key
        if self._prefix:
            new_key = "{0}{1}{2}".format(self._prefix,self._delimiter,key)
        result = self._redis_conn.get(new_key)

        if result:
            return result

        result = self._config_dict.get(key)
        if isinstance(result, types.DictionaryType):
            return Settings(config_dict=result, _redis_conn=self._redis_conn,
                            _prefix=self._prefix, delimiter=self._delimiter)
        return result


rack_cloud_info_config = os.environ.get('RACK_CLOUD_CONFIG',
                                        DEFAULT_CONFIG)

try:
    print "Loading config file %s" % rack_cloud_info_config
    with open(rack_cloud_info_config, "r") as f:
        conf = yaml.safe_load(f)
except Exception as exc:
    print "ERROR: Missing configuration at %s: %s" % (rack_cloud_info_config,
                                                      str(exc))
    raise exc

current_settings = Settings(conf)


