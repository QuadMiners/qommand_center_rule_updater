import os
import logging

from concurrent import futures

import grpc
import quadlibrary.AppDefine as app_define
from quadlibrary.AppDaemon import Daemon
from quadlibrary.database import DatabasePoolMixin

from protocol import rule_update_service_pb2_grpc
from rule_updater.env import get_env_int, get_env_str

logger = logging.getLogger(__name__)


class RuleUpdateApplication(Daemon, DatabasePoolMixin):
    heartbeat = None
    version_check = None
    version_update = None

    def __init__(self, pid):
        Daemon.__init__(self, pid)

    def run(self, *args, **kwargs):

        logger.info("--- Rule Update Application Start---")
        #self.dbconnect()
        app_define.APP_DEBUG = self.debug_mode

        self._start_daemon("Rule Update Daemon Start PID [{0}]".format(os.getpid()))

        #Server Code Start
        heartbeat_service = QmcHeartbeatService()
        version_check_service = QmcVersionCheckService()
        version_download_service = QmcVersionDownloadService()

        main_server = grpc.server(futures.ThreadPoolExecutor(max_workers=100),
                                  options=[('grpc.max_receive_message_length', get_env_str('MAX_MESSAGE_LENGTH'))])

        rule_update_service_pb2_grpc.add_HeartbeatServiceServicer_to_server(heartbeat_service, main_server)
        rule_update_service_pb2_grpc.add_VersionCheckServiceServicer_to_server(version_check_service, main_server)
        rule_update_service_pb2_grpc.add_VersionDownloadServiceServicer_to_server(version_download_service, main_server)
        main_server.add_insecure_port('[::]' + get_env_int('GRPC_SERVER_PORT'))
        main_server.start()

        while self.daemon_alive:
            print("hello")
            #Command 처리부분.
            pass

        logger.info("--- Rule Update Application Stop ---")


def main():
    RuleUpdateApplication(12345).run()
    pass


if __name__ == '__main__':
    main()
