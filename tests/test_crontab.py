# -*- coding: utf-8 -*-
import time
import unittest

from discovery.crontab import Crontab


class TestCrontab(unittest.TestCase):

    count_map = {}

    def _count(self, name):

        def count():
            if name in self.count_map:
                self.count_map[name] += 1
            else:
                self.count_map[name] = 1

        return count

    def test_crontab(self):
        cron = Crontab(threads=5, accuracy=0.1)
        cron.add_task('t1', 0.1, self._count('t1'))
        cron.add_task('t2', 0.2, self._count('t2'))
        time.sleep(0.5)
        cron.stop()
        self.assertGreaterEqual(self.count_map['t1'], 4)
        self.assertGreaterEqual(self.count_map['t2'], 2)
