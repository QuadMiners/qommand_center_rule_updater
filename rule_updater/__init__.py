import contextlib
import logging
from functools import lru_cache, cache

import grpc

import library.database as db
from library.database import DBException
from protocol.site.server_pb2 import RequestServer

logger = logging.getLogger(__name__)

class ChannelMixin(object):
    @contextlib.contextmanager
    @lru_cache
    def get_update_server_channel(self):
        """
            Relay Server 일경우 IP 접속
            그거외에 Domain  접속
        """
        query = """ SELECT update_server from table """
        try:
            with db.pmdatabase.get_cursor() as pcursor:
                pcursor.execute(query)
                if pcursor.rowcount > 0:
                    ipaddr, = pcursor.fetchone()
                    channel = grpc.insecure_channel(target='{}:{}'.format(ipaddr, 9000),
                                                    options=[('grpc.lb_policy_name', 'pick_first'),
                                                             ('grpc.enable_retries', 0),
                                                             ('grpc.keepalive_timeout_ms', 10000)],
                                                    compression=grpc.Compression.Gzip)
                    yield channel
                else:
                    yield None     # 등록된 IP 가 없음
        except DBException as k:
            logger.error("Get Control Server Channel DB Error ".format(k))

class ResponseRequestMixin(ChannelMixin):

    @cache
    def get_request_server(self):
        request_server = RequestServer()
        request_server.site_id = "site"
        request_server.license_uuid = "11111-"
        return request_server

class RequestCheckMixin():
    def request_check(self, request_server):
        """
        RequestServer : proto
        """
        site_id = request_server.site_id
        license_uuid = request_server.license_uuid

        query = """
                
            """



