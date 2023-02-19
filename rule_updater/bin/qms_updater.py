import os
import logging

from concurrent import futures

import grpc
import quadlibrary.AppDefine as app_define
from quadlibrary.AppDaemon import Daemon

from library.database import DatabasePoolMixin
from protocol import rule_update_service_pb2_grpc
from rule_updater import ChannelMixin
from rule_updater.client import UpdateClient
from rule_updater.client.heartbeat import HeartBeatMixin
from rule_updater.env import get_env_int, get_env_str
from rule_updater.server.data_server import QmcDataService
from rule_updater.server.heartbeat_server import QmcHeartbeatService
from rule_updater.server.license_server import QmcLicenseService
from rule_updater.server.site_server import QmcSiteService

logger = logging.getLogger(__name__)


class RuleUpdateApplication(Daemon,HeartBeatMixin, ChannelMixin, DatabasePoolMixin):

    def update_server(self):
        site_service = QmcSiteService()
        license_service = QmcLicenseService()
        hb_service = QmcHeartbeatService()
        data_service = QmcDataService()

        main_server = grpc.server(futures.ThreadPoolExecutor(max_workers=100),
                                  options=[('grpc.max_receive_message_length', get_env_str('MAX_MESSAGE_LENGTH'))])

        rule_update_service_pb2_grpc.add_HeartbeatServiceServicer_to_server(hb_service, main_server)
        rule_update_service_pb2_grpc.add_DataUpdateServiceServicer_to_server(data_service, main_server)
        rule_update_service_pb2_grpc.add_LicenseServiceServicer_to_server(license_service, main_server)
        rule_update_service_pb2_grpc.add_SiteServiceServicer_to_server(site_service, main_server)
        main_server.add_insecure_port('[::]' + get_env_int('GRPC_SERVER_PORT'))
        main_server.start()

    def run(self, *args, **kwargs):

        """
            nbb 에서 동작할때는 client 만
            relay 서버일때는 Server  /  Client 동작
            update 서버일때는 Server 만


            h/w 정보 수집 내용도 포함해야됨.
        """
        logger.info("--- Rule Update Application Start---")
        self.dbconnect()
        app_define.APP_DEBUG = self.debug_mode

        self.update_server()

        while self.daemon_alive:
            try:
                self.heartbeat()
            except Exception as hb:
                logger.error("Heartbeat error: {0}".format(hb))

        logger.info("--- Rule Update Application Stop ---")


def main():
    RuleUpdateApplication(12345).run()
    pass


if __name__ == '__main__':
    main()
