#!/usr/bin/python
# -*- coding: utf-8 -*-
from enum import Enum

import re

import datetime

import time


class EFolderType(Enum):
    SEARCH = 'search'
    CONTENTS = 'contents'
    FILE = 'FILE'
    PAYLOAD = 'payload'
    INDEX = 'index'


class EHardwareInfo(Enum):
    cpu = "cpu"
    memory = "memory"
    network = "network"
    disk = "disk"
    disk_io = "disk_io"


class LoopMixin(object):
    __loop = "hour"
    __desc = ""
    __path = ""

    """
        파티션 정보
    """
    __partition = ""


    """
        unlimit , 1hour, 1day 
        저장 기간
    """
    __storage = ""
    __storage_type = ""
    __path_exception = ""

    __related_table = ""
    __related_table_column = ""
    __related_redis_key = ""

    @classmethod
    def process(self):
        pass
    
    @property
    def loop(self):
        return self.__loop

    @loop.setter
    def loop(self, val):
        self.__loop = val

    @property
    def desc(self):
        return self.__desc

    @desc.setter
    def desc(self, val):
        self.__desc = val

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, val):
        self.__path = val

    @property
    def storage_type(self):
        return self.__storage_type

    @storage_type.setter
    def storage_type(self, val):
        self.__storage_type = val

    @property
    def storage(self):
        return self.__storage

    @storage.setter
    def storage(self, val):
        self.__storage = val

    def save_time(self):
        r_time = 0
        val = re.search("(?P<time>\d+)(?P<type>\w+)$", self.storage)
        t_data = val.groupdict()

        self.storage_type = t_data['type']

        if self.storage_type == 'min':
            r_time = datetime.datetime.now() - datetime.timedelta(minutes=int(val['time']))
        elif self.storage_type == 'hour':
            r_time = datetime.datetime.now() - datetime.timedelta(hours=int(val['time']))
        elif self.storage_type == 'day':
            r_time = datetime.datetime.now() - datetime.timedelta(days=int(val['time']))
        return r_time

    @property
    def partition(self):
        return self.__partition

    @partition.setter
    def partition(self, val):
        self.__partition = val

    @property
    def path_exception(self):
        return self.__path_exception

    @path_exception.setter
    def path_exception(self, val):
        self.__path_exception = val

        try:
            self.exception_dir_regex = re.compile(val)
        except:
            self.exception_dir_regex = None

    def check_exception_dir(self, in_dir):
        if self.exception_dir_regex is None or self.exception_dir_regex.match(in_dir) is None:
            return True
        return False

    def database_insert(self):
        pass