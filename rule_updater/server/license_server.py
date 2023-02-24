from library.rpc.convertor import protobuf_to_dict
from protocol import rule_update_service_pb2_grpc
from protocol.license import license_pb2
from rule_updater import RequestCheckMixin

import library.database as db

class QmcLicenseService(RequestCheckMixin, rule_update_service_pb2_grpc.LicenseServiceServicer):

    def _register(self, license_regist_info):

        server_info_id = None
        approve_type = None

        query = """
                SELECT id FROM server_info \
                WHERE server_info.hardware_uuid = '{hardware_uuid}' AND server_info.machine_id = '{machine_id}'
                """.format(**dict(hardware_uuid=license_regist_info['hardware_uuid'],
                                  machine_id=license_regist_info['machine_id']))
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            row = pcursor.fetchone()
            if row is not None:
                #이미 정보가 있을때
                approve_type = license_pb2.LicenseStatus.DUPLICATE
            else:
                # 새로운 하드웨어, 머신 아이디로 라이센스 요청
                approve_type = license_pb2.LicenseStatus.WAITING

        return license_pb2.LicenseResponse(status=approve_type,
                                           license_data=None)

    def Register(self, request, context):

        response = self._register(protobuf_to_dict(request))

        return response

    def _license_status(self, hardware_uuid, machine_id):

        approve = None
        license_data = None

        print(hardware_uuid)
        print(machine_id)

        query = """ 
                SELECT approve_type, raw FROM black.site_license_approve 
                JOIN server_license
                ON site_license_approve.server_info_id = server_license.server_info_id
                WHERE site_license_approve.server_info_id = (SELECT id 
                                                            FROM server_info 
                                                            WHERE hardware_key = '{hardware_uuid}' 
                                                            AND machine_id = '{machine_id}' )
                """.format(**dict(hardware_uuid=hardware_uuid,
                                          machine_id=machine_id))
        print("0")
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                row = pcursor.fetchone()
                approve = row[0]
                license_data = row[1]

        print("1")
        print(approve, license_data)
        print("2")

        if approve == "confirm":
            response = license_pb2.LicenseResponse(status=license_pb2.LicenseStatus.APPROVE,
                                                 license_data=license_data)
        else:
            response = None

        return response

    def Status(self, request, context):
        return self._license_status(request.hardware_uuid, request.machine_id)


