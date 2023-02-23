import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import logging
import time

from concurrent import futures

import grpc
from quadlibrary.AppDaemon import Daemon


from library.database import DatabasePoolMixin

from protocol import rule_update_service_pb2_grpc
from rule_updater import ChannelMixin
#from rule_updater.client import UpdateClient

from rule_updater.env import get_env_int, get_env_str
#from rule_updater.server.data_server import QmcDataService
#from rule_updater.server.heartbeat_server import QmcHeartbeatService
from rule_updater.server.license_server import QmcLicenseService
#from rule_updater.server.site_server import QmcSiteService

logger = logging.getLogger(__name__)


class RuleUpdateApplication(Daemon, ChannelMixin, DatabasePoolMixin):

    def update_server(self):
        #site_service = QmcSiteService()
        license_service = QmcLicenseService()
        #hb_service = QmcHeartbeatService()
        #data_service = QmcDataService()

        main_server = grpc.server(futures.ThreadPoolExecutor(max_workers=100),
                                  options=[('grpc.max_receive_message_length', get_env_str('MAX_MESSAGE_LENGTH'))])

        #rule_update_service_pb2_grpc.add_HeartbeatServiceServicer_to_server(hb_service, main_server)
        #rule_update_service_pb2_grpc.add_DataUpdateServiceServicer_to_server(data_service, main_server)
        rule_update_service_pb2_grpc.add_LicenseServiceServicer_to_server(license_service, main_server)
        #rule_update_service_pb2_grpc.add_SiteServiceServicer_to_server(site_service, main_server)
        main_server.add_insecure_port(get_env_str('GRPC_SERVER_IPV4') + ":" + get_env_str('GRPC_SERVER_PORT'))
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

        mode = 'UPDATE'

        if mode == 'nbb':
            self.update_server()
        elif mode == 'relay':
            self.update_server()
        else:
            self.update_server()

        while self.daemon_alive:
            try:
                #print(mode + ' server alive')
                #time.sleep(10)
                pass
                #self.heartbeat()
            except Exception: #as hb:
                logger.error("Heartbeat error: {0}")#.format(hb))

        logger.info("--- Rule Update Application Stop ---")


def main():
    RuleUpdateApplication(12345).run()
    #server_daemon = RuleUpdateApplication()
    #server_daemon.run()
    pass


if __name__ == '__main__':
    main()
