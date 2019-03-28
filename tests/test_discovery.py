# -*- coding: utf-8 -*-
import os
import unittest
import time
import logging

from discovery import Client, config_from_env

logging.basicConfig(level=logging.INFO)


class TestDiscovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.domain = os.getenv('DISCOVERY_DOMAIN', None)
        if cls.domain is None:
            cls.skipTest('DISCOVERY_DOMAIN not set')
        os.environ['DEPLOY_ENV'] = 'uat'
        os.environ['ZONE'] = 'sh001'

    def test_watch(self):
        def callback_fn(input_instances):
            self.assertTrue(len(input_instances) == 2)
        client1 = Client(config_from_env(self.domain, hostname='testhost1'))
        client2 = Client(config_from_env(self.domain, hostname='testhost2'))
        client3 = Client(config_from_env(self.domain, hostname='testhost3'))

        client1.register('test.python.watch', ['gorpc://192.168.1.23:80'])
        client2.register('test.python.watch', ['gorpc://192.168.1.23:81'])
        self.assertTrue(len(client3.fetch('test.python.watch')) == 2)
        client3.watch('test.python.watch', callback_fn)
        time.sleep(3)
        client1.stop()
        client2.stop()
        client3.stop()
