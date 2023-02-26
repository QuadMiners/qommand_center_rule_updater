import sys
import logging
import time
import grpc

from command_center.library.qredis.redis_server import RedisMixin
from command_center.protocol import rule_update_service_pb2_grpc
from concurrent import futures
from optparse import OptionParser

from command_center.library.AppDaemon import Daemon
from command_center.library.database import DatabasePoolMixin

from command_center import ChannelMixin

import command_center.library.AppDefine as app_define
from command_center.server.data_server import QmcDataService
from command_center.server.heartbeat_server import QmcHeartbeatService
from command_center.server.license_server import QmcLicenseService
from command_center.server.site_server import QmcSiteService

logger = logging.getLogger(__name__)


class RuleUpdateApplication(Daemon, ChannelMixin,RedisMixin, DatabasePoolMixin):
    main_server = None
    def update_server(self):
        from command_center.library.AppConfig import gconfig

        site_service = QmcSiteService()
        license_service = QmcLicenseService()
        hb_service = QmcHeartbeatService()
        data_service = QmcDataService()

        self.main_server = grpc.server(futures.ThreadPoolExecutor(max_workers=100), options=[('grpc.max_receive_message_length', 2147483647)],compression=grpc.Compression.Gzip)

        rule_update_service_pb2_grpc.add_HeartbeatServiceServicer_to_server(hb_service, self.main_server )
        rule_update_service_pb2_grpc.add_DataUpdateServiceServicer_to_server(data_service, self.main_server )
        rule_update_service_pb2_grpc.add_LicenseServiceServicer_to_server(license_service, self.main_server )
        rule_update_service_pb2_grpc.add_SiteServiceServicer_to_server(site_service, self.main_server )

        #if gconfig.command_center.model == 'relay':
        self.main_server.add_insecure_port('0.0.0.0:{0}'.format(app_define.QMC_SERVER_PORT))
        self.main_server.start()

    def run(self, *args, **kwargs):

        logger.info("--- Rule Update Application Start---")
        print("--- Rule Update Application Start---")
        self.dbconnect()
        self.redis_connect()
        app_define.APP_DEBUG = self.debug_mode

        from command_center.library.AppConfig import gconfig
        self.update_server()

        while self.daemon_alive:
            try:
                if gconfig.command_center.model in ('relay'):
                    self.heartbeat()
                time.sleep(10)
            except Exception as hb:
                logger.error("Heartbeat error: {0}".format(hb))

        self.main_server.stop()
        logger.info("--- Rule Update Application Stop ---")


def main():
    usage = """usage:  """
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--debug", dest="debug", action="store_true", help="디버깅 옵션 정보 ", default=False)
    parser.add_option("-v", "--version", dest="version", action="store_true", help="Version 정보", default=False)

    (options, args) = parser.parse_args()

    if options.version:
        return

    application = RuleUpdateApplication("/var/run/quadminers/updateserver.pid")

    if len(sys.argv) >= 2:
        if 'start' == sys.argv[1]:
            application.start(debug=options.debug)
        elif 'stop' == sys.argv[1]:
            application.stop()
        elif 'restart' == sys.argv[1]:
            application.restart()
        else:
            print("usage: %s start|stop|restart" % sys.argv[0])
            sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)



if __name__ == '__main__':
    main()
