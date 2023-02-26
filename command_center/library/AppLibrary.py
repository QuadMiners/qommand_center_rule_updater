#!/usr/bin/env python
# -*- coding: utf-8 -*-
import decimal
import hashlib
import os
import datetime
import random
import re
import socket
import string
import math
import logging.config
import subprocess
import sys
from configparser import RawConfigParser
from copy import copy
from optparse import Option, OptionValueError

from jinja2 import Template


import logging

from command_center.library.AppDefine import HOME_PATH, DEFAULT_APP_HOME

logger = logging.getLogger(__name__)


# function to check/convert option value to datetime object
def valid_date(option, opt, value):
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M')
    except ValueError:
        raise OptionValueError('option %s: invalid date format: %r' % (opt, value))


class ManagerConfigParser(RawConfigParser):
    """
    set ConfigParser options for case sensitive.
    """
    def optionxform(self, optionstr):
        return optionstr


# extend Option class with date type
class MyOption(Option):
    TYPES = Option.TYPES + ('date',)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER['date'] = valid_date


def datetime_to_dir(dir_datetime):
    return os.path.join( str(dir_datetime.year),
                         str(dir_datetime.month),
                         str(dir_datetime.day),
                         str(dir_datetime.hour),
                         str(dir_datetime.minute)
                         )

def inet_values(msg):
    if isinstance(msg, int):
        return "'0.0.0.0'::inet + {0}".format(msg)
    else:
        return sql_replace(msg)


def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True


def path_to_order_date(path, asc=False):
    """
        /data/contents/<category>/<year>/<month>/</day>/
    """
    def _path_year(dirs, k_asc):
        values = []
        year_list = os.listdir(dirs)

        for int_k in year_list:
            try:
                values.append(int(int_k))
            except ValueError:
                pass

        if len(values) > 0:
            return sorted(values, reverse=k_asc)[0]
        return 0

    year = _path_year(path, asc)
    if year == 0 or year < 1970:
        return None

    month = _path_year(os.path.join(path, str(year)), asc)
    if month == 0 or not (month in range(1, 13)):
        return datetime.datetime.strptime("{0}-1-1".format(year), "%Y-%m-%d")
    day = _path_year(os.path.join(path, str(year), str(month)), asc)
    if day == 0 or not (day in range(1, 32)):
        return datetime.datetime.strptime("{0}-{1}-1".format(year, month), "%Y-%m-%d")

    return datetime.datetime.strptime("{0}-{1}-{2}".format(year, month, day), "%Y-%m-%d")


def path_to_date(path, regex, asc=False, file_flag=True):
    path_list = list()

    re_path = re.compile("{0}/{1}".format(path, regex))
    try:
        for dirpath, d2, fi in os.walk(path):
            ot = re_path.search(dirpath)
            if ot:
                output = ot.groupdict()

                """ 파일 flag 가 True 이면 파일이 있어야 하고 아니면 모두 Yes """
                flag = file_flag and len(fi) > 0 or True

                if flag:
                    path_list.append(datetime.datetime(year=int(output.get('year', 1990)),
                                                       month=int(output.get('month', 1)),
                                                       day=int(output.get('day', 1)),
                                                       hour=int(output.get('hour', 0)),
                                                       minute=int(output.get('minute', 0))))

        if len(path_list) > 0:
            return sorted(path_list, reverse=asc)

        else:
            return None

    except Exception as e:
        logger.error("Path_To Date Exception {0}".format(e))


def get_dir_files(path, asc=False):
    ret = None
    try:
        for dirpath, d2, fi in os.walk(path):
            if len(fi) > 0:
                ret = sorted(fi, reverse=asc)
    except Exception as e:
        logger.error("Path_To Date Exception {0}".format(e))
        pass

    return ret


def datetime_range_array(start_date, end_date, time_step):
    delta = end_date - start_date
    delta_sec = delta.days * 24 * 60 * 60 + delta.seconds
    res = [start_date + datetime.timedelta(0, t) for t in range(0, delta_sec, time_step)]
    return res


def datetime_range_array_start_end(start_date: datetime.datetime, end_date: datetime.datetime, time_step: int):
    """
        Index 파일이나 , NTA 파일에 시간 검색 용도로 사용
    :return:
        각 데이터는 datetime
        [ (start_date, end_date) , (start_date, end_date) , ]

        2020-03-04 00:10  ~  2020-03-04 01:10
            [ (  2020-03-04 00:10 ,  2020-03-04 00:59 ), (  2020-03-04 01:00, 2020-03-04 01:10) ]
    """
    if start_date > end_date:
        raise DateRangeException(47000, "Fun Start Date datetime_range_array_start_end  : {0} ~ {1} ".format(start_date, end_date))

    last_end_date = None
    tmp_start_date = start_date.replace(second=0, microsecond=0)

    if time_step == 60:  # 1분
        tmp_start_date = start_date.replace(second=0, microsecond=0)
    elif time_step == 60 * 60:  # 1r간
        tmp_start_date = start_date.replace(minute=0, second=0, microsecond=0)
    elif time_step == 60 * 60 * 24:     # 1시간
        tmp_start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    delta = end_date - tmp_start_date
    delta_sec = delta.days * 24 * 60 * 60 + delta.seconds
    ret_tuple = []

    for t in range(time_step, delta_sec, time_step):
        if len(ret_tuple) == 0:
            ret_tuple.append((start_date,  tmp_start_date + datetime.timedelta(0, t)))
        else:
            ret_tuple.append((last_end_date,  tmp_start_date + datetime.timedelta(0, t)))
        last_end_date = tmp_start_date + datetime.timedelta(0, t)

    if last_end_date is None:   # Time Stap 범위를 벗어나면
        ret_tuple.append((start_date, end_date))
    else:
        ret_tuple.append((last_end_date, end_date))

    return ret_tuple


def id_generator(size=24, chars=string.ascii_uppercase + string.digits):
    """
        Rendom String 제공
    """
    return ''.join(random.choice(chars) for _ in range(size))


def array_to_insql(array):
    """
        array 정보를 in 쿼리문으로 변경하기 
         
        [ a , b, c, d ]  ==>>  'a', 'b', 'c', 'd' 로 변경됨 
    """
    return ",".join(["'" + t + "'" for t in array])


def sql_replace(in_str):
    """
        string 에 포함된  \n , 혹은  '  을 '' 로 변경 
    """
    if in_str is None:
        return "'NULL'"

    if isinstance(in_str, int):
        in_str = str(in_str)

    return "'" + in_str.replace('\n', '').replace("'", "''") + "'"


def sql_json_replace(in_json):
    """
     dict type 을 sql 에 넣을수 있는 string 으로 변경한다.
    
    """
    return "'" + Template("{{in_json|tojson}}").render(**dict(in_json=in_json)) + "'"


def marge_json_to_json(v_to, v_from):
    """
        2개의 json 을 to 에 합침
    """
    if v_to is None:
        return v_from

    if v_from and (isinstance(v_from, dict) or isinstance(v_from, QObject)):
        v_to.__dict__.update(v_from.__dict__.items())
    return v_to


def hardware_key():
    """
        HW 키 정보 
    """
    ret = 'none'
    command = "dmidecode -t system | awk '/UUID/ {print $2}'"

    if sys.platform == 'darwin':
        return ret
    try:
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate()
        if error != b'':
            return ret

        return sql_replace(output.decode('utf-8'))
    except OSError:
        pass
    except subprocess.SubprocessError:
        pass
    return ret


def model_id():
    """
        모델 id 정보 추
    :return: model id (str)
    """
    command = "cat /etc/machine-id"
    ret = 'none'

    try:
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = p.communicate()
        if error != b'':
            return ret

        ret = output.decode('utf-8').replace('\n','')
    except OSError as e:
        logger.error("Export OSError | {}".format(e))

    except subprocess.SubprocessError as e:
        logger.error("Subprocess Error | {}".format(e))

    return ret


def convert_size(size_bytes, bit=False):
    """
        int 를  byte/bit 정보로 변경
    """
    if isinstance(size_bytes, decimal.Decimal):
        size_bytes = int(size_bytes)

    if size_bytes == 0:
        return "0B"

    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    if bit:
        size_name = ("bps", "Kbps", "Mbps", "Gbps", "Tbps", "Pbps", "Ebps", "Zbps", "Ybps")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def string_to_hash(s_hash):
    if isinstance(s_hash, str):
        hash_object = hashlib.sha256(s_hash.encode('utf-8'))
    else:
        hash_object = hashlib.sha256(s_hash)
    return str(hash_object.hexdigest())


"""
static uint32_t inline url_hash(const char * key)
{
    uint32_t h = 3323198485ul;
    for (;*key;++key) {
        h ^= *key;
        h *= 0x5bd1e995;
        h ^= h >> 15;
    }
    return h;
}
"""

def url_hash(key:str)->int:
    """
    C 언어로 사용되는 Hash 구하는 공식
    """
    def unsigned32(n):
        return n & 0xFFFFFFFF

    h = 3323198485

    for k_in in key:
        h = unsigned32( h ^ ord(k_in))
        h = unsigned32(h * 0x5bd1e995 )
        h = unsigned32(h ^ (h >> 15))
    return h % 0x10000


def pm_logging(log_filename):

    home = os.getenv(key=HOME_PATH, default=DEFAULT_APP_HOME)
    info = os.path.join(home, "log/{0}_info.log".format(log_filename))
    err = os.path.join(home, "log/{0}_err.log".format(log_filename))

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,  # this fixes the problem
        'formatters': {
            'standard': {
                'format': u'%(asctime)s [%(levelname)s%(code)s] %(name)s | %(lineno)d : %(message)s'
            },
            'syslog' :{
                'format': u'1 %(isotime)s %(hostname)s %(processName)s %(process)d engine [meta@0112 %(code)s]  %(name)s | %(lineno)d : %(message)s \n'
            }
        },
        'handlers': {
            'info_file_handler': {
                'level': 'INFO',
                'class': 'pcapbox_library.AppLogging.LoggerRotationFileHandler',
                'formatter': 'standard',
                'filename': info,
                "maxBytes": 1024*1024*20,
                "backupCount": 10,
                "encoding": "utf8",
            },
            'error_file_handler': {
                'level': 'ERROR',
                'class': 'pcapbox_library.AppLogging.LoggerRotationFileHandler',
                'formatter': 'standard',
                'filename': err,
                "maxBytes": 1024*1024*20,
                "backupCount": 10,
                "encoding": "utf8",
            },
            'syslog_handler': {
                'level': 'INFO',
                'class': 'pcapbox_library.AppLogging.LoggerSyslogHandler',
                'formatter': 'syslog',
            },
        },
        'loggers': {
            'system': {
                'level': 'ERROR',
                'propagate': True,
                'handlers': ['info_file_handler', 'error_file_handler', 'syslog_handler'],
            },
            'sync_server': {
                'level': 'INFO',
                'propagate': True,
                'handlers': ['info_file_handler', 'error_file_handler', 'syslog_handler'],
            },
            'sync_client': {
                'level': 'INFO',
                'propagate': True,
                'handlers': ['info_file_handler', 'error_file_handler',"syslog_handler"],
            },
        },
        "root": {
            'level': 'INFO',
            'propagate': True,
            "handlers": ["info_file_handler", "error_file_handler", "syslog_handler"]
        }
    })
