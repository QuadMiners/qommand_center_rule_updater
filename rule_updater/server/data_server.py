from protocol import rule_update_service_pb2_grpc
from rule_updater import RequestCheckMixin


class QmcDataService(RequestCheckMixin, rule_update_service_pb2_grpc.DataUpdateServiceServicer):

    def GetVersions(self, request, context):
        """
        VersionType type = 1;       #데이터 버전 타입 확인
        string license_uuid = 2;    #인가된 라이센스인지 체크
        int32 version  = 3;         #클라이언트가 현재 자신의 어떤 버전을 사용중인지 정보 업데이트
        """

        #서버의 버전 정보 내려줌
        status = version_check_packet_pb2.VersionCheckResponse.CHANGE
        packet = version_check_packet_pb2.VersionCheckResponse(status=status,
                                                               license_uuid="1111-1111-1111-1111",
                                                               version=10001)
        return packet

    def GetData(self, request, context):
        pass
        return None

    def UpdateVersion(self, request, context):
        pass
