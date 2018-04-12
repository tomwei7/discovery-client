# -*- coding: utf-8 -*-
import logging
import os
import json
import socket

from collections import namedtuple
from urllib.request import Request, urlopen

from .crontab import Crontab
from .util import sign_params

LOG = logging.getLogger('discovery')

SCHEMA = 'discovery'

REGISTER_API = "http://{domain}/discovery/register"
CANCEL_API = "http://{domain}/discovery/cancel"
RENEW_API = "http://{domain}/discovery/renew"
POLL_API = "http://{domain}/discovery/polls"
NODES_API = "http://{domain}/discovery/nodes"
STATUS_UP = "1"
REGISTERGAP = 30

RENEW_INTERVAL = 30
CRON_MIN_INTERNAL = 1


Config = namedtuple(
    'Config', ['domain', 'key', 'secret', 'region', 'zone', 'env', 'host'])


def config_from_env(domain, key, secret):
    """
    create config from env

    :param str domain: discovery domain
    :param str key: app key
    :param str secret: app secret
    :rtype: Config
    """
    region = os.getenv('REGION', '')
    zone = os.getenv('ZONE', '')
    env = os.getenv('DEPLOY_ENV', '')
    host = socket.gethostname()
    return Config(domain=domain, key=key, secret=secret, region=region, zone=zone, env=env, host=host)


class DiscoveryError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__('discovery error code: {}, message: {}'.format(code, message))


class BaseClient(object):
    """discovery client"""

    def __init__(self, config):
        """
        :type config: Config
        :param config: discovery config
        """
        self._config = config
        self._apps = {}
        self._watch_list = {}
        self._start_daemon()

    def scheme(self):
        return 'discovery'

    def reload(self, config):
        raise NotImplementedError('oops!')

    def register(self, app_id, tree_id, http, rpc, weight, color, version='', metadata=None):
        raise NotImplementedError('oops!')

    def watch(self, tree_id, callback):
        """
        watch tree_id invoke callback when service change

        :param str tree_id: tree_id
        :param callback:
        """
        if not callable(callback):
            raise TypeError('callback %s not callable', callback)
        self._watch_list[tree_id] = callback

    def unwatch(self, tree_id):
        if tree_id in self._watch_list:
            self._watch_list.pop(tree_id)

    def fetch(self, tree_id):
        if tree_id not in self._apps:
            return []
        return self._apps[tree_id]['instances']

    def _start_daemon(self):
        raise NotImplementedError('oops!')

    def _register_req(self, app_id, tree_id, http, rpc, weight, color, version='', metadata=None):
        """
        :rtype: Request
        """
        params = self._common_params()
        params['appid'] = app_id
        params['treeid'] = tree_id
        params['http'] = http
        params['rpc'] = rpc
        params['status'] = STATUS_UP
        params['weight'] = weight
        params['color'] = color
        params['version'] = version
        params['metadata'] = '{}' if metadata is None else json.dumps(metadata)
        data = sign_params(params, self._config.key, self._config.secret)
        return Request(self._url_for(REGISTER_API), data, method='POST')

    def _renew_req(self, app_id, tree_id):
        """
        :rtype: Request
        """
        params = self._common_params()
        params['appid'] = app_id
        params['treeid'] = tree_id
        params = sign_params(params, self._config.key, self._config.secret)
        return Request(self._url_for(RENEW_API), params, method='POST')

    def _common_params(self):
        """
        :rtype: dict
        """
        return dict(region=self._config.region,
                    zone=self._config.zone,
                    env=self._config.host,
                    hostname=self._config.host)

    def _polls_req(self):
        """
        new polls request

        :rtype: Request
        """
        params = self._common_params()
        tree_ids = self._watch_list.keys()
        params['treeid'] = ','.join(map(lambda x: str(x), tree_ids))
        latest_timestamps = [self._apps['tree_id'] if tree_id in self._apps else 0 for tree_id in tree_ids]
        params['latest_timestamp'] = ','.join(map(lambda x: str(x), latest_timestamps))
        params = sign_params(params, self._config.key, self._config.secret)
        return Request(self._url_for(POLL_API) + '?' + params.decode(), method='GET')

    def _url_for(self, api_url):
        """
        :param str api_url:
        """
        return api_url.format(domain=self._config.domain)


class Client(BaseClient):

    def __init__(self, config, timeout=None, threads=1, accuracy=1):
        """
        new sync discovery client

        :param Config config: discovery config
        :param int timeout: socket timeout
        :param threads: max threads use by background job
        :param accuracy: crontab accuracy
        """
        if timeout is None:
            timeout = socket._GLOBAL_DEFAULT_TIMEOUT
        self._timeout = timeout
        self._crontab = Crontab(threads, accuracy)
        super().__init__(config)

    def stop(self):
        self._crontab.stop()

    def register(self, app_id, tree_id, http, rpc, weight, color, version='', metadata=None):
        """
        register instance

        :param str app_id: app_id
        :param str tree_id: tree_id
        :param str http: http addr
        :param str rpc: rpc addr
        :param int weight: weight
        :param str color: color
        :param version: version
        """
        LOG.info('register instance app_id: %s tree_id: %s http: %s rpc: %s weight: %s'
                 'color: %s version: %s metadata: %s',
                 app_id, tree_id, http, rpc, weight, color, version, metadata)
        req = self._register_req(app_id, tree_id, http, rpc, weight, color, version, metadata)
        self._send(req)
        name = 'renew_{}_{}'.format(app_id, tree_id)
        self._crontab.add_task(name, REGISTERGAP, self._renew(app_id, tree_id, req))

    def _renew(self, app_id, tree_id, register_req):
        """
        return renew callback function

        :param str app_id:
        :param str tree_id:
        :param Request register_req:
        """

        renew_req = self._renew_req(app_id, tree_id)

        def renew_callback():
            try:
                LOG.info('renew app_id %s, tree_id %s', app_id, tree_id)
                self._send(renew_req)
            except DiscoveryError as e:
                if e.code != -404:
                    raise
                # re register
                LOG.info('reregister app_id %s, tree_id %s', app_id, tree_id)
                self._send(register_req)
        return renew_callback

    def _send(self, req):
        """
        send http request

        :param Request req: http request
        :rtype: dict
        """
        resp = urlopen(req, timeout=self._timeout)
        resp_obj = json.loads(resp.read().decode())
        if resp_obj['code']:
            raise DiscoveryError(code=resp_obj['code'], message=resp_obj['message'])
        return resp_obj

    def _start_daemon(self):
        self._crontab.add_task('daemon-polls', 10, self._polls)

    def _polls(self):
        resp_obj = self._send(self._polls_req())
        apps = resp_obj['data']
        broadcast_tree_ids = []
        for tree_id, instances in apps.items():
            if tree_id not in self._apps:
                broadcast_tree_ids.append(tree_id)
            elif instances['latest_timestamp'] != self._apps[tree_id]['latest_timestamp']:
                broadcast_tree_ids.append(tree_id)
        self._apps = apps
        self._broadcast(broadcast_tree_ids)

    def _broadcast(self, tree_ids):
        for tree_id in tree_ids:
            if tree_id not in self._watch_list:
                LOG.warning('tree_id %s not in watch list', tree_id)
                continue
            self._watch_list[tree_id]()
