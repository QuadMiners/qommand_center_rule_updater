#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .fdatabase import DBException, DBInterface, DBInfo
from .fpgsql import FPgsqlPool, FPgsql

import logging

from ..AppConfig import gconfig

logger = logging.getLogger(__name__)

pmdatabase = None


def global_db_connect():
    global pmdatabase
    pmdatabase = FPgsqlPool(gconfig.database_config)

class DatabasePoolMixin(object):

    def dbconnect(self, pool_cnt=2):
        global pmdatabase
        pmdatabase = FPgsqlPool(gconfig.database_config, pool_cnt)
