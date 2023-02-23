#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from rule_updater.env import get_env_str, get_env_int

from .fdatabase import DBException, DBInterface, DBInfo
from .fpgsql import FPgsqlPool, FPgsql

import logging

logger = logging.getLogger(__name__)

pmdatabase = None

def global_db_connect(config=True, contents=True):
    global pmdatabase

    from rule_updater.env import get_env_str
    dbinfo = dict()
    dbinfo["name"] = get_env_str("POSTGRES_NAME")
    dbinfo["user"] = "quadminers"  # get_env_str("POSTGRES_USER")
    dbinfo["passwd"] = "quadminers"  # get_env_str("POSTGRES_PASSWORD")
    dbinfo["host"] = "127.0.0.1"  # get_env_str("POSTGRES_HOST")
    dbinfo["port"] = "10090"  # get_env_int("POSTGRES_PORT")
    dbinfo["schema"] = "black"  # get_env_str("POSTGRES_SCHEMA")

    if config:
        pmdatabase = FPgsqlPool(dbinfo)
        

class DatabasePoolMixin(object):

    from rule_updater.env import get_env_str
    dbinfo = dict()
    dbinfo["name"] = get_env_str("POSTGRES_NAME")
    dbinfo["user"] = "quadminers"  # get_env_str("POSTGRES_USER")
    dbinfo["passwd"] = "quadminers"  # get_env_str("POSTGRES_PASSWORD")
    dbinfo["host"] = "127.0.0.1"  # get_env_str("POSTGRES_HOST")
    dbinfo["port"] = "10090"  # get_env_int("POSTGRES_PORT")
    dbinfo["schema"] = "black"  # get_env_str("POSTGRES_SCHEMA")

    def dbconnect(self, config=True, pool_cnt=2):
        global pmdatabase
        pmdatabase = FPgsqlPool(self.dbinfo, pool_cnt)
