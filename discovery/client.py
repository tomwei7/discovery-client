# -*- coding: utf-8 -*-
import logging
import os
import json
import socket

from collections import namedtuple
from urllib.request import Request, urlopen

from .crontab import Crontab
from .util import sort_urlencode

LOG = logging.getLogger('discovery')

SCHEMA = 'discovery'

REGISTER_API = "http://{domain}/discovery/register"
CANCEL_API = "http://{domain}/discovery/cancel"
RENEW_API = "http://{domain}/discovery/renew"
POLL_API = "http://{domain}/discovery/polls"
NODES_API = "http://{domain}/discovery/nodes"
FETCH_API = "http://{domain}/discovery/fetch"

STATUS_UP = "1"
STATUS_WATING = "2"
STATUS_ALL = "3"

REGISTERGAP = 30

RENEW_INTERVAL = 30
CRON_MIN_INTERNAL = 1
LONG_POLL_TIMEOUT = 60


Config = namedtuple(
    'Config', ['domain', 'region', 'zone', 'env', 'host'])


def config_from_env(domain, **kwargs):
    """
    create config from env

    :param str domain: discovery domain
    :rtype: Config
    """
    region = kwargs.get('region', os.getenv('REGION', ''))
    zone = kwargs.get('zone', os.getenv('ZONE', ''))
    env = kwargs.get('deploy_env', os.getenv('DEPLOY_ENV', ''))
    host = kwargs.get('hostname', socket.gethostname())
    return Config(domain=domain, region=region, zone=zone, env=env, host=host)


class DiscoveryError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super(DiscoveryError, self).__init__('discovery error code: {}, message: {}'.format(code, message))


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

    def register(self, app_id, addr, **kwargs):
        raise NotImplementedError('oops!')

    def watch(self, app_id, callback):
        """
        watch app_id invoke callback when service change.

        :param str tree_id: tree_id
        :param callback:
        """
        if not callable(callback):
            raise TypeError('callback %s not callable', callback)
        self._watch_list[app_id] = callback

    def fetch(self, app_id):
        raise NotImplementedError('oops!')

    def unwatch(self, app_id):
        """
        unwatch app_id remove app_id from watch list.

        :param str app_id: app_id
        """
        if app_id in self._watch_list:
            self._watch_list.pop(app_id)

    def _start_daemon(self):
        raise NotImplementedError('oops!')

    def _register_req(self, app_id, addrs, metadata=None):
        """
        :param str app_id: app_id
        :param list[str] addrs: addrs to register, e.g. ['http://10.0.1.2:8000', 'grpc://10.0.1.2:5001']
        :rtype: Request
        """
        params = self._common_params()
        params['appid'] = app_id
        params['status'] = STATUS_UP
        params['addrs'] = ','.join(addrs)
        params['metadata'] = '{}' if metadata is None else json.dumps(metadata)
        return Request(self._url_for(REGISTER_API), sort_urlencode(params).encode(), method='POST')

    def _renew_req(self, app_id):
        """
        :rtype: Request
        """
        params = self._common_params()
        params['appid'] = app_id
        return Request(self._url_for(RENEW_API), sort_urlencode(params).encode(), method='POST')

    def _common_params(self, **kwargs):
        """
        :rtype: dict
        """
        env = self._config.env if 'env' not in kwargs else kwargs['env']
        zone = self._config.zone if 'zone' not in kwargs else kwargs['zone']
        region = self._config.region if 'region' not in kwargs else kwargs['region']
        return dict(region=region, zone=zone, env=env, hostname=self._config.host)

    def _polls_req(self):
        """
        new polls request

        :rtype: Request
        """
        params = self._common_params()
        app_ids = self._watch_list.keys()
        params['appid'] = ','.join(map(lambda x: str(x), app_ids))
        latest_timestamps = [self._apps[app_id]['latest_timestamp'] if app_id in self._apps else 0 for app_id in app_ids]
        params['latest_timestamp'] = ','.join(map(lambda x: str(x), latest_timestamps))
        return Request(self._url_for(POLL_API) + '?' + sort_urlencode(params), method='GET')

    def _fetch_req(self, app_id, status, **kwargs):
        params = self._common_params(**kwargs)
        params['appid'] = app_id
        params['status'] = status
        return Request(self._url_for(FETCH_API) + '?' + sort_urlencode(params), method='GET')

    def _url_for(self, api_url):
        """
        :param str api_url:
        """
        return api_url.format(domain=self._config.domain)


class Client(BaseClient):

    def __init__(self, config, timeout=None, threads=2, accuracy=1):
        """
        new sync discovery client

        :param Config config: discovery config
        :param int timeout: socket timeout
        :param threads: max threads use by background job
        :param accuracy: crontab accuracy
        """
        if timeout is None:
            timeout = socket._GLOBAL_DEFAULT_TIMEOUT
        if threads < 2:
            threads = 2
            LOG.warning('worker threads must greater than 1')
        self._timeout = timeout
        self._crontab = Crontab(threads, accuracy)
        super(Client, self).__init__(config)

    def stop(self):
        self._crontab.stop()

    def register(self, app_id, addrs, **kwargs):
        """
        register instance

        :param str app_id: app_id
        :param addrs list[str]: addrs to register, e.g. ['http://10.0.1.2:8000', 'grpc://10.0.1.2:5001']
        """
        metadata = {}
        LOG.info('register instance app_id: %s addrs: %s metadata: %s',
                 app_id, addrs, metadata)
        req = self._register_req(app_id, addrs, metadata)
        self._send(req)
        name = 'renew_{}'.format(app_id)
        self._crontab.add_task(name, REGISTERGAP, self._renew(app_id, req))

    def fetch(self, app_id, status=STATUS_UP, **kwargs):
        """
        fetch instance from discovery.

        :param str app_id: app_id
        """
        req = self._fetch_req(app_id, status, **kwargs)
        resp = self._send(req)
        return resp['data']['instances']

    def _renew(self, app_id, register_req):
        """
        return renew callback function

        :param str app_id:
        :param Request register_req:
        """

        renew_req = self._renew_req(app_id)

        def renew_callback():
            try:
                LOG.info('renew app_id %s', app_id)
                self._send(renew_req)
            except DiscoveryError as e:
                if e.code != -404:
                    raise
                # re register
                LOG.info('reregister app_id %s', app_id)
                self._send(register_req)
        return renew_callback

    def _send(self, req, timeout=None):
        """
        send http request

        :param Request req: http request
        :rtype: dict
        """
        if timeout is None:
            timeout = self._timeout
        resp = urlopen(req, timeout=timeout)
        resp_obj = json.loads(resp.read().decode())
        if resp_obj['code']:
            raise DiscoveryError(code=resp_obj['code'], message=resp_obj['message'])
        return resp_obj

    def _start_daemon(self):
        self._crontab.add_task('daemon-polls', 3, self._polls)

    def _polls(self):
        if not len(self._watch_list):
            return
        resp_obj = self._send(self._polls_req(), timeout=LONG_POLL_TIMEOUT)
        apps = resp_obj['data']
        broadcast_app_ids = []
        for app_id, instances in apps.items():
            if app_id not in self._apps:
                broadcast_app_ids.append(app_id)
            elif instances['latest_timestamp'] != self._apps[app_id]['latest_timestamp']:
                broadcast_app_ids.append(app_id)
        self._apps = apps
        self._broadcast(broadcast_app_ids)

    def _broadcast(self, app_ids):
        for app_id in app_ids:
            if app_id not in self._watch_list:
                LOG.warning('app_id %s not in watch list', app_id)
                continue
            self._watch_list[app_id](self._apps[app_id]['instances'])
