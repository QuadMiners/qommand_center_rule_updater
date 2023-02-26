#!/usr/bin/env python
# -*- coding: utf-8 -*-
import contextlib
import json
import uuid
from json import JSONDecodeError

import redis
import time

from redis import StrictRedis
from redis.exceptions import TimeoutError, ResponseError
import ast

from termcolor import cprint

from command_center.library.AppConfig import gconfig
from command_center.library.qredis import RedisChannel, RedisQuery

import logging

logger = logging.getLogger(__name__)

conf = gconfig.redis_config

redis_connector = redis.StrictRedis(host=conf.host_name.strip(),
                                    port=conf.port,
                                    db=conf.schema,
                                    password=conf.passwd.strip(),
                                    socket_connect_timeout=5, decode_responses=True)

def redis_conn_decorator(attribute):
    def _redis_conn_decorator(func):
        def wrapper(self, *args, **kwargs):

            try:
                return func(self, *args, **kwargs)

            except redis.exceptions.ConnectionError as e:
                logger.error("Redis Reconnect {0}".format(e))
                ret = self.redis_connect()
                time.sleep(3)
            except redis.exceptions.ResponseError as e:
                if str(e) == 'invalid password':
                    logger.error("Redis Exception {0}".format(e))
                    print("Error ) Redis Exception  {0}".format(e))
                    time.sleep(5)
                else:
                    logger.error("Redis Response Error >>", e)
                ret = False
            except redis.exceptions.TimeoutError as k:
                logger.error("Redis TimtoutException {0}".format(k))
                print("Redis TimeoutException {0}".format(k))

        return wrapper
    return _redis_conn_decorator


class RedisMixin(object):
    """
        기본 Redis 접속 관련 내용 
    """

    def redis_connect(self):

        try:
            self.rconn = redis_connector
            self.psub = self.rconn.pubsub()
            ret = True
        except TimeoutError as e:
            logger.error("Redis Connect Error : {0}".format(e))
            ret = False
        except ResponseError as e:
            logger.error("Redis Connect Response Error {0}".format(e))
            ret = False
        except redis.exceptions.TimeoutError as k:
            logger.error("Redis Timtout Exception {0}".format(k))
        return ret

    @contextlib.contextmanager
    def connect_redis(self)->StrictRedis:
        try:
            yield self.rconn
        except TimeoutError as e:
            logger.error("Redis Connect Error : {0}".format(e))
        except ResponseError as e:
            logger.error("Redis Connect Response Error {0}".format(e))
        except redis.exceptions.TimeoutError as k:
            logger.error("Redis Timtout Exception {0}".format(k))

    def get_data(self, key):
        value = self.rconn.get(key)
        if value:
            try:
                return ast.literal_eval(value.decode('utf-8'))
            except Exception as e:
                try:
                    return ast.literal_eval(value)
                except Exception:
                    return value
        else:
            return None

    def lpush_data(self, key, value, ttl=None):
        ret = self.rconn.lpush(key, value)
        if ttl:
            self.expire_data(key, ttl)
        return ret

    def lrange_data(self, key, start, end):
        values = self.rconn.lrange(key, start, end)
        return values

    def zadd_data(self, key, value, ttl=None):
        """
        :param key:
        :param value: dict( value = score)
        :return:
        """
        self.rconn.zadd(key, value, ch=True)
        if ttl:
            self.expire_data(key, ttl)

    def sadd_data(self, key, values, ttl=None):
        ret = self.rconn.sadd(key, values)
        if ttl:
            self.expire_data(key, ttl)
        return ret

    def smember_data(self, key):
        return self.rconn.smembers(key)

    def set_data(self, key, value, ttl = None):
        ret = self.rconn.set(key, str(value))
        if ttl:
            self.expire_data(key, ttl)
        return ret

    def expire_data(self, key, ttl=60):
        ret = self.rconn.expire(key, ttl)
        return ret

    def hmset_data(self, key, items, ttl=None):
        """
        :param key:
        :param items:  tuple 형태로  ( ('key', 'value'),  ('key', 'value'))
        :param ttl:
        :return:
        """
        ret = self.rconn.hmset(key, items)
        if ttl:
            self.expire_data(key, ttl)
        return ret

    def hmkeys(self, key):
        return self.rconn.hkeys(key)

    def hmget_data(self, key, field, index=0):
        ret = self.rconn.hmget(key, field)
        if index is not None:
            return ret[index]
        else:
            ret = {x:y for x, y in zip(field,ret)}
        return ret

    def hscan(self, path, match=None, cursor=0, count=1000, chart=False):

        value = self.rconn.hscan(path, match=match, cursor=cursor, count=count)[1]
        return value


class ClientRedisMixin(RedisMixin):
    channel = None

    def __init__(self):
        self.redis_connect()
        try:
            self.rconn.ping()
        except Exception as e:
            logger.error("Client Redis Not Connection")

    def public(self, name, data, user_channel=None):
        ret = None
        if self.channel or user_channel:
            send_data = json.dumps(dict(id=str(uuid.uuid4()),
                                        type='control',
                                        source='0', dest='0',
                                        name=name,
                                        body=data))
            if isinstance(user_channel, list) or isinstance(self.channel, list):
                channels = user_channel and user_channel or self.channel
                for channel in channels:
                    ret = self.rconn.publish(channel, send_data)
            else:
                ret = self.rconn.publish(user_channel and user_channel or self.channel, send_data)
        return ret


class ServerRedisMixin(RedisMixin):
    channels = [RedisChannel.FILTER.value,
                RedisChannel.PAYLOAD_SEARCH.value,
                RedisChannel.CONTENTS.value]

    def __init__(self):
        self.redis_connect()

    def redis_sub(self):
        self.psub.subscribe(self.channels)

    def redis_listen(self):
        """
            {'type': 'subscribe', 'pattern': None, 'channel': b'search_server', 'data': 1}
        """
        for item in self.psub.listen():
            yield item

    def redis_run(self, callback):
        ret = True

        try:
            self.redis_sub()
            for item in self.redis_listen():
                rdata = RedisQuery(item)

                if rdata.type == 'message':
                    callback(rdata)
        except redis.exceptions.ConnectionError as e:
            logger.error("Redis Reconnect [ {0} ]".format(e))
            cprint("Redis Reconnect [ {0} ] ".format(e))
            ret = self.redis_connect()
            time.sleep(3)
        except redis.exceptions.ResponseError as e:
            if str(e) == 'invalid password':
                logger.error("Redis Exception {0}".format(e))
                cprint("Error ) Redis Exception  {0}".format(e))
                time.sleep(5)
            else:
                logger.error("Redis Response Error >>", e)
            ret = False
        except redis.exceptions.TimeoutError as k:
            logger.error("Redis TimtoutException {0}".format(k))
            cprint("Redis Timeout Exception {0}".format(k))
        except JSONDecodeError as e:
            ret = False

        return ret