#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ast
import json
from enum import Enum
import logging
from json import JSONDecodeError

logger = logging.getLogger(__name__)


class RedisChannel(Enum):
    FILTER = 'filter'
    SYNC = 'sync'
    PAYLOAD_SEARCH = 'packet_search'
    CONTENTS = 'contents'
    ALERT = 'alert'
    SYSTEM = 'system'
    LINK = 'link'
    VIRUS = 'virus'
    NAPATECH = 'napatech'   # napatech 데몬
    PARSER = 'parser'       # parser 데몬
    DETAIL = 'detail'
    HEARTBEAT = 'heartbeat'
    ANALYSIS = 'analysis'
    SURICATA = 'suricata'   # suricata 데몬
    RPC_SERVER = 'rpcserver' # rpcserver 데몬
    HIERARCHY = 'hierarchy'
    IDS_LOGD = 'ids_logd'
    QUADX_LOGD = 'quadx_logd'
    NTA_SCNRD = 'nta_scnrd'
    AMS = 'ams'

class RedisQuery:
    """
        체널에서 넘어온 Data 정보 
        { }

        type = 'subscribe'   : 최초 메시지
                'message'   : 데이터 전송
    """
    _channel_type = None

    def __init__(self, data):
        self.set_attr(data)
        try:
            self.channel_type = RedisChannel(self.channel)
        except ValueError:
            self.channel_type = RedisChannel.DETAIL

    def set_attr(self, value):
        try:
            for column in value:
                if isinstance(value[column], list):
                    s_value = []
                    for item in value[column]:
                        setattr(self, column, s_value)
                else:
                    if column == 'data' and type(value[column]) is not int:
                        try:
                            setattr(self, column, json.loads(value[column]))
                        except TypeError as e:
                            logger.error("Redis Query SetAttrError [ {0} ]".format(e))
                            setattr(self, column, value[column])
                        except AttributeError as e:
                            """ decode 가 없을수 있음 """
                            setattr(self, column, json.loads(value[column]))
                        except JSONDecodeError:
                            try:
                                setattr(self, column, ast.literal_eval(value[column]))
                            except Exception as e:
                                setattr(self, column, value[column])
                    else:
                        setattr(self, column, value[column])
        except JSONDecodeError as e:
           logger.error("Redis JsonDecode Error Exception [{0}]".format(e))
           raise e

    @property
    def channel_type(self):
        return self._channel_type

    @channel_type.setter
    def channel_type(self, value):
        self._channel_type = value
