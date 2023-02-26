#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
from json import JSONEncoder


class QObject(object):
    def __init__(self, init=None):
        if init is not None:
            self.__dict__.update(init)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __delitem__(self, key):
        del self.__dict__[key]

    def __contains__(self, key):
        return key in self.__dict__

    def __len__(self):
        return len(self.__dict__)

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return json.dumps(self.__dict__)


class ServerInfo(QObject):
    """
    server_id
    name
    ipaddr
    ipaddr_data
    host_name
    """
    pass