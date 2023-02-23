#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from rule_updater.env import get_env_str, get_env_int

from .fdatabase import DBException, DBInterface, DBInfo
from .fpgsql import FPgsqlPool, FPgsql

import logging

logger = logging.getLogger(__name__)

pmdatabase = None

class DBINFO():
    name = None
    database = None
    user = None
    passwd = None
    host = None
    port = None
    def __init__(self):
        from rule_updater.env import get_env_str, get_env_int
        self.database = get_env_str("POSTGRES_NAME")
        self.name = get_env_str("POSTGRES_NAME")
        self.user = get_env_str("POSTGRES_USER")
        self.passwd = get_env_str("POSTGRES_PASSWORD")
        self.host = get_env_str("POSTGRES_HOST")
        self.port = get_env_str("POSTGRES_PORT")
        self.schema = get_env_str("POSTGRES_SCHEMA")


def global_db_connect(config=True, contents=True):
    global pmdatabase

    dbinfo = DBINFO()

    if config:
        pmdatabase = FPgsqlPool(dbinfo)
        

class DatabasePoolMixin(object):

    dbinfo = DBINFO()

    def dbconnect(self, config=True, pool_cnt=2):
        global pmdatabase
        pmdatabase = FPgsqlPool(self.dbinfo, pool_cnt)
