import logging

import grpc

from command_center.library.rpc.retry import retrying_stub_methods, RetriesExceeded
from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.heartbeat.heartbeat_pb2 import HeartbeatRequest, ServerStatus, DataUpdateFlag
from command_center import ResponseRequestMixin
from command_center.client.data import DataClientMixin

logger = logging.getLogger(__name__)


class HeartBeatMixin(DataClientMixin, ResponseRequestMixin):

    def get_data(self):
        datas = list()
        # StringData(str_type=StringType.USERAGENT, data='MALWARES')

        return datas

    def heartbeat(self):
        try:
            """
                자신의 서버정보를 데이터베이스에서 읽어와서 
                grpc로 하트비트 날리는 반복작업 코드 작성 필요.
            """
            channel = self.get_update_server_channel()
            stub = rule_update_service_pb2_grpc.HeartbeatServiceStub(channel)
            retrying_stub_methods(stub)

            request_server = self.get_request_server()
            local_data = self.get_data()
            response = stub.HeartbeatInfo(HeartbeatRequest(server=request_server, datas=local_data), timeout=10)

            if response.status == ServerStatus.REGISTER:
                """
                """
                if response.site_update_flag == DataUpdateFlag.UPDATE:
                    """
                        site api  call
                    """
                    pass

                if response.license_update_flag == DataUpdateFlag.UPDATE:
                    """
                        license api call
                    """
                    pass

                self.check_versions(response.versions)

            elif response.status == ServerStatus.NOTFOUND:
                """
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
