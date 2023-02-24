import contextlib
import logging
#from functools import lru_cache, cache
from cachetools.func import lru_cache

import grpc

import library.database as db
from library.database import DBException
from protocol.site import server_pb2

from rule_updater.env import get_env_str

logger = logging.getLogger(__name__)

db.global_db_connect()
class ChannelMixin():

    server_type = 'relay'

    #@contextlib.contextmanager
    #@lru_cache
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
            query = """
                    SELECT hostname, port, sign_flag, sign_file 
                    FROM black.update_server_parent_config
                    """

            print(query)

            with db.pmdatabase.get_cursor() as pcursor:
                pcursor.execute(query)
                row = pcursor.fetchone()
                if row is None:
                    logger.error("Can't Load update_server_parent_config")
                    return None  # 등록된 IP 가 없음 update 서버일것..
                else:
                    hostname = row[0]
                    port = row[1]
                    sign_flag = row[2]
                    sign_file_path = row[3]

            try:
                if self.server_type == 'update':
                    hostname = 'localhost'
                elif self.server_type == 'relay':
                    hostname = get_env_str("TARGET_SERVER_IVPV4")
                else:
                    hostname = hostname

                if sign_flag == "Y":
                    with open(sign_file_path, "rb") as f:
                        cert = f.read()
                    credentials = grpc.ssl_channel_credentials(root_certificates=cert)
                    channel = grpc.secure_channel('{}:{}'.format(hostname, port),
                                                  credentials=credentials,
                                                  options=[('grpc.lb_policy_name', 'pick_first'),
                                                           ('grpc.enable_retries', 0),
                                                           ('grpc.keepalive_timeout_ms', 10000)],
                                                  compression=grpc.Compression.Gzip)

                    print('{}:{}'.format(hostname, port), "인증서 통신 모드")

                    return channel

                else:
                    #hostname = "192.168.10.56"
                    #port = "9000"
                    channel = grpc.insecure_channel('{}:{}'.format(hostname, port),
                                                    options=[('grpc.lb_policy_name', 'pick_first'),
                                                             ('grpc.enable_retries', 0),
                                                             ('grpc.keepalive_timeout_ms', 10000)],
                                                    compression=grpc.Compression.Gzip)

                    print('{}:{}'.format(hostname, port), "비인증서 통신 모드")

                    return channel

            except DBException as k:
                logger.error("Get Control Server Channel DB Error ".format(k))


class ResponseRequestMixin():

    @lru_cache
    def get_request_server(self):
        query = "SELECT site_id, key FROM black.license " \
                "JOIN server_info " \
                "ON license.server_info_id = server_info.id"

        request_server = server_pb2.RequestServer()

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            row = pcursor.fetchone()
            print(row)
            if pcursor.rowcount > 0:
                request_server.site_id = str(row[0])
                request_server.license_uuid = row[1]

        return request_server

class RequestCheckMixin():
    def request_check(self, request_server):

        query = """
                SELECT site, license_uuid FROM server_info 
                WHERE site = '{site_id}' 
                AND license_uuid = '{license_uuid}'
                """.format(**dict(site_id=request_server.site_id,
                                  license_uuid=request_server.license_uuid))

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                return True
            else:
                return False


