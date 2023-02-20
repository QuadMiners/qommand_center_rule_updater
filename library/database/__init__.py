#!/usr/bin/env python
# -*- coding: utf-8 -*-
from rule_updater.env import get_env_str, get_env_int
from .fdatabase import DBException, DBInterface, DBInfo
from .fpgsql import FPgsqlPool, FPgsql

import logging

logger = logging.getLogger(__name__)

pmdatabase = None


dbinfo = dict()
dbinfo['dbname'] = get_env_str("POSTGRES_NAME")
dbinfo["user"] = get_env_str("POSTGRES_USER")
dbinfo["password"] = get_env_str("POSTGRES_PASSWORD")
dbinfo["host"] = get_env_str("POSTGRES_HOST")
dbinfo["port"] = get_env_int("POSTGRES_PORT")
dbinfo["schema"] = get_env_str("POSTGRES_SCHEMA")


def global_db_connect(config=True, contents=True):
    global pmdatabase
    if config:
        pmdatabase = FPgsqlPool(dbinfo)
        

class DatabasePoolMixin(object):
    def dbconnect(self, config=True, pool_cnt=2):
        global pmdatabase
        pmdatabase = FPgsqlPool(dbinfo, pool_cnt)
