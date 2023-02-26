#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import base64
import logging
import subprocess
from configparser import ConfigParser

import command_center.library.AppDefine as app_define

from command_center.library.AppLibrary import model_id
from command_center.library.AppObject import QObject
from command_center.library.database import DBException
from command_center.library.database.fpgsql import FPgsql

logger = logging.getLogger(__name__)


def __parse_sys_info(buf):
    """
        명령어 실행 결과를 파싱하여 정보 추출
    :param buf: 명령어 실행 결과 스트림
    :return: 추출한 정보 (dict)
    """
    info_list = ["Manufacturer", "Product Name", "Family", "Serial Number", "UUID"]
    sys_info = {}

    for line in buf.splitlines():
        line_str = str(line)

        for item in info_list:
            find_str = item + ': '
            if line_str.find(find_str) != -1 :
                _item = item.replace(" ", "_").lower()
                sys_info[_item] = line_str[len(find_str):].strip()

    return sys_info

def system_model_info():
    """
        서버의 model 정보를 명령어 실행결과에 추출함
        추출정보 :  manufacturer, product_name, family, serial_number, uuid
    :return: model 정보 (dict)
    """

    command = 'dmidecode | grep -A 9 "System Information"'
    ret = None
    try:
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate()

        if error != b'':
            logger.error("Excute Error msg | {}".format(error))

        buf = output.decode('utf-8')
        ret = __parse_sys_info(buf)
        print(ret)

    except OSError as e:
        logger.error("Export OSError | {}".format(e))

    except subprocess.SubprocessError as e:
        logger.error("Subprocess Error | {}".format(e))

    return ret

def get_server_model_info():
    """
        서버의 모델정보 전체
        모델정보 종류 : manufacturer, product_name, family, serial_number, uuid, model_id
    :return: 모델정보 (dict)
    """
    server_model_info = system_model_info()
    server_model_info['machine_id'] = model_id()

    return server_model_info

class GetConfig(object):
    """get config file class"""
    __stream_count = 4

    def __init__(self):
        try:
            self.get_home = os.getenv(key=app_define.HOME_PATH, default=app_define.DEFAULT_APP_HOME)

            if self.get_home is None:
                logger.warning('your no Set env is QUAD_HOME ')
                exit

            self.debug = True
            self.command_center = QObject(dict(model='update', lang='korean', license_machine=False, site_code='-'))
            self.license= QObject(dict(uuid='-'))
            self.psql = QObject(dict(host='127.0.0.1', port=10090, name='quadminers', user='quadminers', passwd=base64.b64decode('N0RHVnhUNERLd1RV').decode('utf-8'), schema='black'))
            self.redis_config = QObject(dict(host_name='127.0.0.1', port=10080, schema=1, passwd="3QCBQYy8bD7VRpV"))
            self.server_model = QObject(get_server_model_info())
            self.initalize()

        except Exception as e:
            logger.error("Unexpected error:", sys.exc_info()[0], e)
            raise

    def set_debug(self, debug):
        self.debug = debug

    def initalize(self, configfile=None, debug=True):
        self.debug = debug
        if configfile:
            filename = "manager.conf"
        else:
            filename = os.path.join(self.get_home, "conf/manager.conf")
        if os.path.exists(filename):
            try:
                config = ConfigParser()
                config.read(filename)

                for section in config.sections():
                    for name, value in config.items(section):
                        if section == 'PSQL':
                            if name == 'passwd':
                                self.psql[name] = base64.b64decode(value).decode('utf-8')
                            elif name == 'host_name':
                                self.psql['host'] = value
                                self.redis_config['host_name'] = value
                            else:
                                self.psql[name] = value

            except Exception as e:
                logger.error("Config Exception |  {0}".format(e))
        else:
            logger.error("Not Found File | manager.conf  FilePath : {0}".format(filename))
        self.system_model_insert()
        self.server_type()

    def system_model_insert(self):
        try:
            s_model = get_server_model_info()
            str_query = """INSERT INTO command_center_info(manufacturer, product_name, family, serial_number, uuid, machine_id )
                        VALUES('{manufacturer}', '{product_name}', '{family}', '{serial_number}', '{uuid}', '{machine_id}')
                       ON CONFLICT(uuid) DO UPDATE SET  manufacturer= '{manufacturer}', product_name='{product_name}', family='{family}', serial_number='{serial_number}', uuid='{uuid}', machine_id='{machine_id}'
                       RETURNING site_code
                        """.format(**s_model)

            instance = FPgsql(self.psql)
            site_code = instance.execute(str_query, returning_id=True)
            self.command_center['site_code'] = site_code
        except DBException as e:
            logger.error("Error (system_model_insert) [%s] " % e)

    def server_type(self):
        instance = FPgsql(self.psql)
        try:
            query = """
                SELECT type, lang FROM command_center_model
                """
            with instance.get_cursor() as pcursor:
                pcursor.execute(query)
                type, lang = pcursor.fetchone()

            self.command_center['model'] = type
            self.command_center['lang'] = lang
        except DBException as e:
            logger.error("Error (server_type) [%s] " % e)

    def parent_update_server(self):
        query = """
            SELECT hostname, port, sign_flag, sign_file FROM command_center_parent_config
            """
        instance = FPgsql(self.psql)

        data = QObject()
        with instance.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            rows = pcursor.fetchall()
            columns = pcursor.description
            for row in rows:
                for (index, column) in enumerate(row):
                    data[columns[index][0].lower()] = column

        return data

    @property
    def database_config(self):
        return self.psql

    @property
    def command_info(self):
        return self.command_center