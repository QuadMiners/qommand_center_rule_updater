from library.database.fquery import fetchall_query_to_dict
from protocol import rule_update_service_pb2_grpc
from protocol.license import license_pb2
from rule_updater import RequestCheckMixin


class QmcLicenseService(RequestCheckMixin, rule_update_service_pb2_grpc.LicenseServiceServicer):
    def Register(self, request, context):
        """
        request.type == 1 요청한 데이타 타입 확인 SNORT
        request.license_uuid 알맞은 접속자 확인
        request.version 다운로드 요청한 버전 데이터 가져오기.
        """
        reg_user_name = request.reg_user_name
        reg_user_tel = request.reg_user_tel
        server_type = request.server_type
        hardware_uuid = request.hardware_uuid
        machine_id = request.machine_id

        query = f"SELECT * FROM license_info WHERE hardware_uuid = '{hardware_uuid}' AND machine_id = '{machine_id}'"
        fetchall_query_to_dict(query)

        status = license_pb2.LicenseStatus.APPROVE
        response = license_pb2.LicenseResponse(status=status,
                                               license_data="")

        return response

    def Status(self, request, context):
        hardware_uuid = request.hardware_uuid
        machine_id = request.machine_id

        status = license_pb2.LicenseStatus.APPROVE
        response = license_pb2.LicenseStatus(status=status,
                                             license_data="")
