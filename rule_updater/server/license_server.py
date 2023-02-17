from protocol import rule_update_service_pb2_grpc
from rule_updater import RequestCheckMixin


class QmcLicenseService(RequestCheckMixin, rule_update_service_pb2_grpc.LicenseServiceServicer):
    def Register(self, request, context):
        """
        request.type == 1 요청한 데이타 타입 확인 SNORT
        request.license_uuid 알맞은 접속자 확인
        request.version 다운로드 요청한 버전 데이터 가져오기.
        """
        pass

    def Status(self, request, context):
        pass
