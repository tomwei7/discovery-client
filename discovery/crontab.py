# -*- coding: utf-8 -*-
import time
import logging
import traceback

from threading import Lock, Thread, current_thread

LOG = logging.getLogger('crontab')


class Task(object):
    def __init__(self, name, interval, callback):
        self.name = name
        self.latest_run = 0
        self._interval = interval
        self._callback = callback
        self._picked = False

    def run(self):
        self.latest_run = time.time()
        self._callback()

    def pick(self):
        if self._picked:
            return False
        if self.latest_run + self._interval > time.time():
            return False
        self._picked = True
        return True

    def release(self):
        self._picked = False


class Crontab(object):

    """crontab implement simple crontab dispatch"""

    def __init__(self, threads, accuracy):
        """create crontab with gived working threads and accuracy

        :threads: thread pool size defalut 1
        :accuracy: min time interval use by crontab defalut 1s
        """

        self._accuracy = accuracy
        self._pick_lock = Lock()
        self._crontab_list = {}
        self._threads = []
        self._stoped = False
        self._start_worker(threads)

    def _start_worker(self, threads):
        for i in range(threads):
            name = 'crontab_worker_{}'.format(i)
            t = Thread(target=self._worker, name=name)
            t.start()
            LOG.info('start worker %s', name)
            self._threads.append(t)

    def stop(self):
        """ stop crontab """
        self._stoped = True
        for t in self._threads:
            t.join()

    def add_task(self, name, interval, callback):
        LOG.info('add task %s, interval %ds', name, interval)
        self._crontab_list[name] = Task(name, interval, callback)

    def _worker(self):
        while True:
            if self._stoped:
                LOG.info('stoped %s quit!', current_thread().name)
                return
            task = self._pick()
            if task is not None:
                LOG.info('run task %s in %s', task.name, current_thread().name)
                try:
                    task.run()
                except Exception as e:
                    LOG.error('task raise exception %s', str(e))
                    traceback.print_exc()
                task.release()
                continue
            time.sleep(self._accuracy)

    def _pick(self):
        self._pick_lock.acquire()
        for name, task in self._crontab_list.items():
            if task.pick():
                self._pick_lock.release()
                return task
        self._pick_lock.release()
        return None
