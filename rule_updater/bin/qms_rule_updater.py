import os
import logging

from concurrent import futures

import grpc
import quadlibrary.AppDefine as app_define
from quadlibrary.AppDaemon import Daemon
from quadlibrary.database import DatabasePoolMixin

from protocol import rule_update_service_pb2_grpc
from rule_updater.env import get_env_int
from rule_updater.gRPC.server import QmcHeartbeatService, QmcVersionCheckService, QmcVersionDownloadService
from rule_updater.rule_update_process.heartbeat import HeartBeatProcess
from rule_updater.rule_update_process.version_check import VersionCheckProcess
from rule_updater.rule_update_process.version_update import VersionUpdateProcess

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 2147483647


class RuleUpdateApplication(Daemon, DatabasePoolMixin):
    heartbeat = None
    version_check = None
    version_update = None

    def __init__(self, pid):
        Daemon.__init__(self, pid)

    def run(self, *args, **kwargs):

        logger.info("--- Rule Update Application Start---")
        self.dbconnect()
        app_define.APP_DEBUG = self.debug_mode

        self._start_daemon("Rule Update Daemon Start PID [{0}]".format(os.getpid()))

        #Client Code Start (Scheduler)
        self.heartbeat = HeartBeatProcess(get_env_int('HEARTBEAT_TIME')).run()
        self.version_check = VersionCheckProcess(get_env_int('VERSION_CHECK_TIME')).run()
        self.version_update = VersionUpdateProcess(get_env_int('VERSION_UPDATE_TIME')).run()

        #Server Code Start
        heartbeat_service = QmcHeartbeatService()
        version_check_service = QmcVersionCheckService()
        version_download_service = QmcVersionDownloadService()
        main_server = grpc.server(futures.ThreadPoolExecutor(max_workers=30),
                                  options=[('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)])

        rule_update_service_pb2_grpc.add_HeartbeatServiceServicer_to_server(heartbeat_service, main_server)
        rule_update_service_pb2_grpc.add_VersionCheckServiceServicer_to_server(version_check_service, main_server)
        rule_update_service_pb2_grpc.add_VersionDownloadServiceServicer_to_server(version_download_service, main_server)
        main_server.add_insecure_port('[::]' + get_env_int('GRPC_SERVER_PORT'))
        main_server.start()

        while self.daemon_alive:
            #Command 처리부분.
            pass

        logger.info("--- Rule Update Application Stop ---")


def main():
    pass


if __name__ == '__main__':
    main()
