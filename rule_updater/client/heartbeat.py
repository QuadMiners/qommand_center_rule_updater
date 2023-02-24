import logging
import time

import grpc


from library.rpc.retry import retrying_stub_methods, RetriesExceeded
from protocol import rule_update_service_pb2_grpc

from protocol.heartbeat import heartbeat_pb2
from protocol.heartbeat.heartbeat_pb2 import StringData, HeartbeatRequest, ServerStatus, DataUpdateFlag
from protocol.site import server_pb2
from rule_updater import ResponseRequestMixin
from rule_updater.client.data import DataClientMixin
from rule_updater.client.license import LicenseClientMixin
from rule_updater.client.site import SiteClientMixin
from rule_updater.env import get_env_str

logger = logging.getLogger(__name__)


class HeartBeatMixin(DataClientMixin,ResponseRequestMixin,SiteClientMixin,LicenseClientMixin):

    def get_data(self):
        datas = list()
        # StringData(str_type=StringType.USERAGENT, data='MALWARES')

        return datas

    def heartbeat(self):
        try:
            """
                하트비트 Request - 자신의 서버 정보(site_id, license_uuid)를 전송한다.
            """
            channel = self.get_update_server_channel()
            stub = rule_update_service_pb2_grpc.HeartbeatServiceStub(channel)
            retrying_stub_methods(stub)

            request_server = self.get_request_server()
            local_data = self.get_data()
            heartbeat_request_packet = heartbeat_pb2.HeartbeatRequest()
            heartbeat_request_packet.server = request_server
            heartbeat_request_packet.datas = local_data
            #전송후 리턴값 받아옴
            response = stub.Heartbeat(heartbeat_request_packet, timeout=10)

            if response.status == ServerStatus.REGISTER:
                """
                """
                if response.site_update_flag == DataUpdateFlag.UPDATE:
                    """
                        site api  call
                    """
                    self.GetSite()

                if response.license_update_flag == DataUpdateFlag.UPDATE:
                    """
                        license api call
                    """
                    self.Status()

                """
                    check version
                """
                self.check_versions(response.versions)

            elif response.status == ServerStatus.NOTFOUND:
                """
                    Do Nothing
                """
                pass

        except grpc._channel._InactiveRpcError as k:
            logger.error("HeartBeat _InactiveRpcError | Details {0}".format(k))
            return False
        except RetriesExceeded as l:
            logger.error("HeartBeat RetriesExceeded Exception {0}".format(l))
            return False
        except Exception as e:
            logger.error("HeartBeat Exception {0}".format(e))
            return False
        return True
