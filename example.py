#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import logging

from discovery import Client, Config


def main():
    logging.basicConfig(level=logging.INFO)
    config = Config(domain='127.0.0.1:7171',
                    key='0c4b8fe3ff35a4b6',
                    secret='b370880d1aca7d3a289b9b9a7f4d6812',
                    region='local',
                    zone='local-1',
                    env='',
                    host='localhost')
    client = Client(config)
    client.register('account', 2233, '127.0.0.1:80', '127.0.0.1:8080', 1, 'red')

    def hello():
        print('hello')

    client.watch(2233, hello)
    try:
        time.sleep(3600)
    except KeyboardInterrupt:
        client.stop()


if __name__ == "__main__":
    main()
