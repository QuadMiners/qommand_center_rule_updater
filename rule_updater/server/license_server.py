from library.database.fquery import fetchall_query_to_dict, fetchall_query, fetchone_query_to_dict
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

        query = f"SELECT * FROM site_license_status_approve " \
                f"WHERE server_info_id = (" \
                    f"SELECT id FROM server_info " \
                    f"WHERE hardware_key = '{hardware_uuid}' AND machine_id = '{machine_id}'" \
                f")"
        result_dict = fetchone_query_to_dict(query)

        if result_dict['approve_type'] == "confirm":
            status = license_pb2.LicenseStatus.APPROVE
            response = license_pb2.LicenseStatus(status=status,
                                                 license_data="무엇을 보내야하나?")
        else:
            return None

        """
            Site 정보 모두 업데이트 내려줬다고 체크. server_info_id 에서 join하여 검색
        """
        query = f"UPDATE black.server_license " \
                f"SET update_server_status = True " \
                f"WHERE server_info_id = (" \
                    f"SELECT id FROM server_info " \
                    f"WHERE hardware_key = '{hardware_uuid}' AND machine_id = '{machine_id}'" \
                f")"

        fetchall_query(query)

        return response
