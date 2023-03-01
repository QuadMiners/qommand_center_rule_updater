import grpc
import contextlib
import logging
import command_center.library.database as db
from command_center import DBException

from command_center.library.AppConfig import gconfig


logger = logging.getLogger(__name__)

"""
    Relay 서버 Client 
"""

class ClientRequestMixin(object):

    def get_request_server(self):
        from command_center.protocol.site import server_pb2

        server_type = server_pb2.ServerType.RELAY

        request_server = server_pb2.RequestServer(server_type=server_type,
                                                  site_code=gconfig.command_center.site_code,
                                                  hardware_uuid=gconfig.server_model.uuid)
        return request_server


    @contextlib.contextmanager
    def get_command_center_channel(self):
        hostname = None
        port = None
        sign_flag = None
        sign_file_path = None
        query = """
                SELECT hostname, port, sign_flag, sign_file 
                FROM qommand_center_parent_config
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
