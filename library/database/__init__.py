#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .fdatabase import DBException, DBInterface, DBInfo
from .fpgsql import FPgsqlPool, FPgsql

import logging

logger = logging.getLogger(__name__)

pmdatabase = None


dbinfo = dict()
dbinfo['dbname'] = 'quadminers'
dbinfo["user"] = 'quadminers'
dbinfo["password"] = 'quadminers'
dbinfo["host"] = '127.0.0.1'
dbinfo["port"] = 10090
dbinfo["schema"] = 'black'


def global_db_connect(config=True, contents=True):
    global pmdatabase
    if config:
        pmdatabase = FPgsqlPool(dbinfo)
        

class DatabasePoolMixin(object):
    def dbconnect(self, config=True,pool_cnt=2):
        global pmdatabase
        pmdatabase = FPgsqlPool(dbinfo, pool_cnt)
