import grpc
import protocol.rule_update_service_pb2
import protocol.rule_update_service_pb2_grpc

from protocol import rule_update_service_pb2_grpc
from protocol.heartbeat import heartbeat_packet_pb2
from protocol.version import version_check_packet_pb2, version_type_pb2
from protocol.version import version_download_packet_pb2


class QmcHeartbeatService(rule_update_service_pb2_grpc.HeartbeatServiceServicer):

    def __init__(self):
        # self.compress = Compress()
        # self.decompress = Decompress()
        pass

    def Heartbeat(self, request, context):
        """
        string license_uuid = 1;    #인가된 uuid인지 체크 -> QMC_CLIENT_INFO 에 저장 및 업데이트
        string name = 2;            #QMC_CLIENT_INFO 에 저장 및 업데이트
        string type = 3;            #QMC_CLIENT_INFO에 저장 및 업데이트
        bool auto_update = 4;       #QMC_CLIENT_INFO에 저장 및 업데이트
        string url_data = 5;        #QMC_CLIENT_INFO에 저장 및 업데이트
        string user_agent_data = 6; #QMC_CLIENT_INFO에 저장 및 업데이트
        """

        status = heartbeat_packet_pb2.HeartbeatResponse.OK
        packet = heartbeat_packet_pb2.HeartbeatResponse(status=status,
                                                        license_uuid="1111-1111-1111-1111",
                                                        name="master-1234",
                                                        type="relay")
        return packet


class QmcVersionCheckService(rule_update_service_pb2_grpc.VersionCheckServiceServicer):
    def __init__(self):
        pass

    def VersionCheck(self, request, context):
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


class QmcVersionDownloadService(rule_update_service_pb2_grpc.VersionDownloadServiceServicer):
    def __init__(self):
        pass

    def VersionDownload(self, request, context):
        """
        request.type == 1 요청한 데이타 타입 확인 SNORT
        request.license_uuid 알맞은 접속자 확인
        request.version 다운로드 요청한 버전 데이터 가져오기.
        """
        type = version_type_pb2.VersionType.SNORT
        packet = version_download_packet_pb2.VersionDownloadResponse(type=type,
                                                                     license_uuid="1111-1111-1111-1111",
                                                                     version=10001,
                                                                     data='file')
        return packet
