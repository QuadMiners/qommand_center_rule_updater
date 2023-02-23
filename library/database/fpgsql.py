#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import sys
import logging
import time

import psycopg2
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
from quadlibrary.AppDefine import EUseDatabase
from .fdatabase import DBInterface, DBException


logger = logging.getLogger(__name__)


class FPgsql(DBInterface):

    __database = EUseDatabase.PSQL

    def __init__(self, dbinfo):
        DBInterface.__init__(self, dbinfo)

    def connect(self):
        try:
            self.dbconnect = psycopg2.connect("dbname={0}  user={1} password={2} port={3} host={4}".format(self.dbinfo.name, self.dbinfo.user, self.dbinfo.passwd, self.dbinfo.port,self.dbinfo.host))
            self.execute("SET search_path TO {0}".format(self.dbinfo.schema))
        except psycopg2.DatabaseError as e:
            raise DBException(e.pgcode, e)
        except:
            raise Exception

    @contextmanager
    def get_cursor(self, cusor_factory=None):
        cursor = None
        try:
            if cusor_factory is None:
                cursor = self.dbconnect.cursor()
            else:
                cursor = self.dbconnect.cursor(cusor_factory)
            yield cursor
        except psycopg2.DatabaseError as e:
            logger.error("Psql Error {0}".format(str(e)))
            if e.pgcode == '57P01':
                logger.error("PSQL ERROR {0}".format(e.pgcode))

                loop = 0
                for k in range(0, 20):
                    try:
                        self.connect()
                        if not self._dbpool.closed:
                            logger.info("Psql-Reconnect Success")
                            break
                    except Exception:
                        time.sleep(1)
                    loop = k

                if loop >= 19:
                    raise DBException('57P01', e)
                try:
                    conn = self._dbpool.getconn()
                    conn.autocommit = True
                    cursor = conn.cursor()
                    cursor.execute("SET search_path TO {0}".format(self._dbinfo.schema))
                    yield cursor
                except psycopg2.DatabaseError as e:
                    logger.error("Psql >> Error {0}".format(str(e)))
                    raise DBException(e.pgcode, e)
            else:
                raise DBException(e.pgcode, e)
        finally:
            if cursor:
                cursor.close()

    def execute(self, query, args=None, returning_id=False, ret_list=False) -> object:
        ret_id = None
        row_count = 0

        try:
            with self.get_cursor() as pcursor:
                pcursor.execute(query, vars=args)
                row_count = pcursor.rowcount
                self.dbconnect.commit()
                if returning_id is True:
                    if ret_list:
                        """
                            Update 될때 return  된 id 리스트 가져오기 
                        """
                        ret_id = pcursor.fetchall()
                    else:
                        ret_id = pcursor.fetchone()[0]
        except psycopg2.DatabaseError as e:
            self.dbconnect.rollback()
            raise DBException(e.pgcode, e, query)

        if returning_id is True:
            return ret_id

        return row_count



class FPgsqlPool():
    _dbinfo = None
    _dbpool = None
    pool_connection = None
    pool_cnt = None

    def __init__(self, dbinfo, pool_cnt=2):
        self._dbinfo = dbinfo
        self.pool_cnt = pool_cnt
        self.connect()
        self.pool_connection = datetime.datetime.now()

    def connect(self):
        try:
            self._dbpool = psycopg2.pool.ThreadedConnectionPool(self.pool_cnt, 20,
                                                                database=self._dbinfo['name'],
                                                                user=self._dbinfo['user'],
                                                                password=self._dbinfo['passwd'],
                                                                host=self._dbinfo['host'],
                                                                port=self._dbinfo['port'])
        except psycopg2.DatabaseError as e:
            logger.error("Error ) PostgreSQL Connection Code:{0} Msg:{1}".format(e.pgcode, e))
            raise DBException(e.pgcode, e)
        except Exception as e:
            logger.error("Error ) PostgreSQL Connection  Msg:{0}".format(sys.exc_info()[0]))
            raise DBException("Other Exception", e)

    def get_conn(self):
        return self._dbpool.getconn()

    def __reset_connection(self):
        durations_time = datetime.datetime.now() - self.pool_connection
        if durations_time.total_seconds() > 60:
            self._dbpool.minconn = 0
            self.pool_connection = datetime.datetime.now()

        if len(self._dbpool._pool) == 0 and self._dbpool.minconn == 0 and len(self._dbpool._used) == 0:
            self._dbpool.minconn = self.pool_cnt

    @contextmanager
    def get_cursor(self):
        conn = None
        cursor = None
        try:
            self.__reset_connection()
            conn = self._dbpool.getconn()
            conn.autocommit = True
            conn.get_transaction_status()
            
            cursor = conn.cursor()
            cursor.execute("SET search_path TO {0}".format(self._dbinfo.schema))
            yield cursor
        except psycopg2.DatabaseError as e:
            logger.error("Psql Error {0}".format(str(e)))
            if e.pgcode == '57P01':
                logger.error("PSQL ERROR {0}".format(e.pgcode))

                loop = 0
                for k in range(0, 20):
                    try:
                        self.connect()
                        if not self._dbpool.closed:
                            logger.info("Psql-Reconnect Success")
                            break
                    except Exception:
                        time.sleep(1)
                    loop = k

                if loop >= 19:
                    raise DBException('57P01', e)
                try:
                    conn = self._dbpool.getconn()
                    conn.autocommit = True
                    cursor = conn.cursor()
                    cursor.execute("SET search_path TO {0}".format(self._dbinfo.schema))
                    yield cursor
                except psycopg2.DatabaseError as e:
                    logger.error("Psql Error {0}".format(str(e)))
                    raise DBException(e.pgcode, e)
            else:
                raise DBException(e.pgcode, e)
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._dbpool.putconn(conn)

    def execute(self, query: object, args: object = None, returning_id: object = False, ret_list:bool = False) -> object:
        ret_id = None
        row_count = 0
        try:
            with self.get_cursor() as pcursor:
                pcursor.execute(query, args)
                row_count = pcursor.rowcount

                if returning_id is True:
                    if ret_list:
                        """
                            Update 될때 return  된 id 리스트 가져오기 
                        """
                        ret_id = pcursor.fetchall()
                    else:
                        ret_id = pcursor.fetchone()[0]

        except psycopg2.DatabaseError as e:
            raise DBException(e.pgcode, e, query=query)
        except DBException as e:
            e.query = query
            raise e

        if returning_id is True: 
            return ret_id
        return row_count
