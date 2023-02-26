#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from quadlibrary.AppDefine import EUseDatabase

logger = logging.getLogger(__name__)


class DBException(Exception):
    __code = None
    __query = None
    message = "-"

    def __init__(self, code, message, query=None):
        if query:
            Exception.__init__(self, code, message, query)
        else:
            Exception.__init__(self, "DBException raised with arguments Code {0} , Message {1}, Query {2}".format(code, message, query))
        self.code = code
        self.message = message
        self.query = query

    def __repr__(self):
        if self.query:
            return "DBException raised with arguments Code {0} , Message {1}".format(self.code, self.message)
        else:
            return "DBException raised with arguments Code {0} , Message {1}, Query {2}".format(self.code, self.message, self.query)

    @property
    def code(self):
        return self.__code

    @code.setter
    def code(self, value):
        self.__code = value

    @property
    def query(self):
        return self.__query

    @query.setter
    def query(self, value):
        self.__query = value


class DBInterface(object):
    __dbinfo = None
    __database = None

    __dbstaus = None
    __dbconnect = None

    def __init__(self, dbinfo):
        if isinstance(dbinfo, dict):
            self.dbinfo = DBInfo(**dbinfo)
        else:
            self.dbinfo = dbinfo
        self.connect()

    def __del__(self):
        try:
            self.dbconnect.close()
        except:
            pass

    @property
    def dbinfo(self):
        return self.__dbinfo

    @dbinfo.setter
    def dbinfo(self, val):
        self.__dbinfo = val

    @property
    def dbconnect(self):
        return self.__dbconnect

    @dbconnect.setter
    def dbconnect(self, val):
        self.__dbconnect = val

    @classmethod
    def connect(self):
        return None

    @classmethod
    def getcursor(self):
        return None

    # returing_id 의 경우 Postgresql 에서만 사용
    @classmethod
    def execute(self, query: object, returning_id: object = False) -> object:
        return None


class DBInfo(object):
    '''
        DB 정보
    '''
    __status = None
    __name = None
    __database = None

    __dbname = None
    __user = None
    __port = None
    __host = None
    __password = None
    __schema = None

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        dbinfo = kwargs.get('dbinfo')
        if dbinfo:
            self.dbname = dbinfo['dbname']
            self.user = dbinfo["user"]
            self.passwd = dbinfo["password"]
            self.host = dbinfo["host"]
            self.port = int(dbinfo["port"])
            self.schema = dbinfo["schema"]
        else:
            self.dbname = kwargs.get('dbname')
            self.user = kwargs.get('user')
            self.passwd = kwargs.get('password')
            self.host = kwargs.get('host')
            self.port = kwargs.get('port')
            self.schema = kwargs.get("schema")

    def __str__(self):
        return " DB Connction Info  DBNAME:{0}, DBUSER:{1}, DBPASSWD:{2}, DBHOST:{3}, DBPORT:{4}".format(self.dbname,
                                                                                                         self.user,
                                                                                                         self.passwd,
                                                                                                         self.host,
                                                                                                         self.port)

    def get_database_object(self):
        from quadlibrary.database.fpgsql import FPgsql
        classname = FPgsql(dbinfo=self)
        return classname

    @property
    def dbname(self):
        return self.__dbname

    @dbname.setter
    def dbname(self, val):
        self.__dbname = val

    @property
    def schema(self):
        return self.__schema

    @schema.setter
    def schema(self, val):
        self.__schema = val

    @property
    def user(self):
        return self.__user

    @user.setter
    def user(self, val):
        self.__user = val

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, val):
        if isinstance(val, int):
            self.__port = val
        else:
            self.__port = int(val)

    @property
    def passwd(self):
        return self.__password

    @passwd.setter
    def passwd(self, val):
        self.__password = val

    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, val):
        self.__host = val

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, val):
        self.__name = val

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status):
        self.__status = status