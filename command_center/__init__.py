import grpc
import contextlib
import logging

from command_center.library.database import DBException

import command_center.library.database as db
from command_center.library.AppConfig import gconfig

logger = logging.getLogger(__name__)


class ChannelMixin():

    server_type = 'relay'

    @contextlib.contextmanager
    def get_command_center_channel(self):
        hostname = None
        port = None
        sign_flag = None
        sign_file_path = None
        query = """
                SELECT hostname, port, sign_flag, sign_file 
                FROM command_center_parent_config
                """

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            hostname, port, sign_flag, sign_file_path, = pcursor.fetchone()

        try:

            if sign_flag == "K":
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

                yield channel

            else:
                channel = grpc.insecure_channel('{}:{}'.format(hostname, port),
                                                options=[('grpc.lb_policy_name', 'pick_first'),
                                                         ('grpc.enable_retries', 0),
                                                         ('grpc.keepalive_timeout_ms', 10000)],
                                                compression=grpc.Compression.Gzip)

                print('{}:{}'.format(hostname, port), "비인증서 통신 모드")

                yield channel

        except DBException as k:
            logger.error("Get Control Server Channel DB Error ".format(k))


class ResponseRequestMixin():

    def get_request_server(self):
        from command_center.protocol.site import server_pb2
        request_server = server_pb2.RequestServer(site_code=gconfig.command_center.site_code,
                                                  hardware_uuid=gconfig.server_model.uuid)
        return request_server


class RequestCheckMixin():
    def request_check(self, site_code, hardware_uuid):
        cnt = 0
        query = """
                SELECT count(*) FROM site_server_license
                WHERE server_info_id in ( SELECT id FROM site_server_info WHERE site_id in ( SELECT id FROM site WHERE site_code = '{site_code}' and hardware_uuid = '{server_uuid}' ))
                """.format(**dict(site_code=site_code, hardware_uuid=hardware_uuid))

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            cnt = pcursor.fetchone()
        return cnt

    def update_license_request_check(self, site_code, hardware_uuid):
        update_server_status = None
        auto_update = None
        expires = None
        """
            마지막 License 가 있는지 업데이트 되었는지 확인
            마지막 내용만 업데이트하고 만약 가저가지 않았더라도 전부 가저간걸로 한다.
            update_server_status = True 로 변경  
        """
        query = """
                SELECT update_server_status, auto_update, expire FROM site_server_license
                WHERE server_info_id in ( SELECT id FROM site_server_info WHERE site_id in ( SELECT id FROM site WHERE site_code = '{site_code}' and hardware_uuid = '{server_uuid}'))
                ORDER BY id desc limit 1
                """.format(**dict(site_code=site_code, hardware_uuid=hardware_uuid))

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                update_server_status, auto_update, expires = pcursor.fetchone()

        return update_server_status, auto_update, expires


