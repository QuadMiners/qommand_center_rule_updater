from protocol import rule_update_service_pb2_grpc
from protocol.heartbeat.heartbeat_pb2 import ServerStatus, HeartbeatResponse, DataUpdateFlag

from rule_updater import RequestCheckMixin


class QmcHeartbeatService(RequestCheckMixin, rule_update_service_pb2_grpc.HeartbeatServiceServicer):

    def Heartbeat(self, request, context):
        """
        string license_uuid = 1;    #인가된 uuid인지 체크 -> QMC_CLIENT_INFO 에 저장 및 업데이트
        string name = 2;            #QMC_CLIENT_INFO 에 저장 및 업데이트
        string type = 3;            #QMC_CLIENT_INFO에 저장 및 업데이트
        bool auto_update = 4;       #QMC_CLIENT_INFO에 저장 및 업데이트
        string url_data = 5;        #QMC_CLIENT_INFO에 저장 및 업데이트
        string user_agent_data = 6; #QMC_CLIENT_INFO에 저장 및 업데이트
        """

        request_server = request.server
        versions = list()
        if self.request_check(request_server):
            status = ServerStatus.REGISTER
        else:
            status = ServerStatus.NOTFOUND

        return HeartbeatResponse(status=status, site_update_flag=DataUpdateFlag.NONE, license_update_flag=DataUpdateFlag.NONE, versions=versions)

