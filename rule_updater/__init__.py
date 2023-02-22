import contextlib
import logging
#from functools import lru_cache, cache
from cachetools.func import lru_cache

import grpc

import library.database as db
from library.database import DBException
from library.database.fquery import fetchone_query_to_dict
from protocol.site import server_pb2

logger = logging.getLogger(__name__)


class ChannelMixin(object):

    server_type = 'update'

    @contextlib.contextmanager
    @lru_cache
    def get_update_server_channel(self):
        hostname = None
        port = None
        sign_flag = None
        sign_file_path = None
        """
            Relay Server 일경우 IP 접속
            그거외에 Domain  접속
        """
        if self.server_type == 'nbb':
            query = """ SELECT value from manager_config 
                            WHERE keyword_group = 'update' and keyworrd = 'update_server'
                    """
        else:
            query = """ SELECT * from update_server_parent_config """

            try:
                result_dict = fetchone_query_to_dict(query)
                if result_dict is 0:
                    logger.error("Can't Load update_server_parent_config")
                    yield None  # 등록된 IP 가 없음
                else:
                    if self.server_type == 'relay':
                        from rule_updater.env import get_env_str
                        hostname = get_env_str("GRPC_SERVER_IPV4")
                    else:
                        hostname = result_dict["hostname"]
                    port = result_dict["port"]
                    sign_flag = result_dict["sign_flag"]
                    sign_file_path = result_dict["sign_file"]

                if sign_flag is "Y":
                    with open(sign_file_path, "rb") as f:
                        cert = f.read()
                    credentials = grpc.ssl_channel_credentials(root_certificates=cert)
                    channel = grpc.secure_channel('{}:{}'.format(hostname, port),
                                                  credentials=credentials,
                                                  options=[('grpc.lb_policy_name', 'pick_first'),
                                                           ('grpc.enable_retries', 0),
                                                           ('grpc.keepalive_timeout_ms', 10000)],
                                                  compression=grpc.Compression.Gzip)

                    yield channel

                else:
                    channel = grpc.insecure_channel(target='{}:{}'.format(hostname, port),
                                                    options=[('grpc.lb_policy_name', 'pick_first'),
                                                             ('grpc.enable_retries', 0),
                                                             ('grpc.keepalive_timeout_ms', 10000)],
                                                    compression=grpc.Compression.Gzip)
                    yield channel

            except DBException as k:
                logger.error("Get Control Server Channel DB Error ".format(k))


class ResponseRequestMixin(ChannelMixin):

    @lru_cache
    def get_request_server(self):
        request_server = server_pb2.RequestServer()

        query = "SELECT * FROM site"
        result_dict = fetchone_query_to_dict(query)
        request_server.site_id = result_dict["id"]

        """
            자신의 라이센스 아이디 어떻게 구하지..?
            update_server_info_model에 uuid ?
        """
        request_server.license_uuid
        return request_server

class RequestCheckMixin():
    def request_check(self, request_server):
        """
        RequestServer : proto
        """
        site_id = request_server.site_id
        license_uuid = request_server.license_uuid

        query = """
                SELECT * FROM server_info WHERE site = '{site_id}' AND license_uuid = '{license_uuid}'
                """
        result_dict = fetchone_query_to_dict(query)
        if result_dict is None or result_dict <= 0:
            return False # 허용 안된 서버
        else:
            return True # 허용된 서버



