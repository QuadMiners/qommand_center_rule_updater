#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
from abc import ABCMeta, abstractmethod
import threading

from queue import Queue


import logging

from command_center.library import schedule

logger = logging.getLogger(__name__)


class Interface(object):
    __metaclass__ = ABCMeta

    def suspend_getter(self):
        return

    def suspend_setter(self, value):
        return

    def exit_getter(self):
        return

    def exit_setter(self, value):
        return

    _suspend = abc.abstractproperty(suspend_getter, suspend_setter)
    _exit = abc.abstractproperty(exit_getter, exit_setter)


class ThreadInterface(Interface, threading.Thread):
    __suspend = False
    __exit = False

    def __init__(self, name=None):
        threading.Thread.__init__(self, name=name)
        self.finished = threading.Event()
        self.msg_queue = Queue(maxsize=1000)

    def put_queue(self, data):
        self.msg_queue.put(data)

    def run_queue(self):
        if self.msg_queue.empty() is False:
            while not self.msg_queue.empty():
                data = self.msg_queue.get()
                self.process(data)

    @abstractmethod
    def process(self, data):
        pass

    @abstractmethod
    def run(self):
        pass

    def suspend_getter(self):
        return self.__suspend

    def suspend_setter(self, value):
        self.__suspend = value

    def exit_getter(self):
        return self.__exit

    def exit_setter(self, value):
        self.finished.set()             # 깨우기위함
        self.__exit = value

    _suspend = abc.abstractproperty(suspend_getter, suspend_setter)
    _exit = abc.abstractproperty(exit_getter, exit_setter)


class SchedulerThreadInterface(ThreadInterface):

    def __init__(self, name=None):
        ThreadInterface.__init__(self, name)
        self.scheduler = schedule.Scheduler()

    def add_schedule(self, obj, callback, loop=None):
        if obj.loop == 'real' or (loop and loop == 'real'):
            self.scheduler.every().seconds.do(callback, data=obj)
        elif obj.loop == 'min' or (loop and loop == 'min'):
            self.scheduler.every().minutes.do(callback, data=obj)
        elif obj.loop == 'hour' or (loop and loop == 'hour'):
            self.scheduler.every().hours.at(":01").do(callback, data=obj)
        elif obj.loop == 'day' or (loop and loop == 'day'):
            self.scheduler.every().days.at("03:00").do(callback, data=obj)

    def add_schedule_func(self, callback, loop=None):
        """
            Loop 가 None 이면 1분 마다
        """

        if loop is None:
            self.scheduler.every().minutes.do(callback)
        elif loop == 'real':
            self.scheduler.every().seconds.do(callback)
        elif loop == 'min':
            self.scheduler.every().minutes.do(callback)
        elif loop == 'hour':
            self.scheduler.every().hours.at(":01").do(callback)
        elif loop == 'day':
            self.scheduler.every().days.at("03:00").do(callback)

    def callback_process(self, data):
        try:
            data.process()
        except Exception as e:
            logger.error("Process Exception {0}".format(e))


