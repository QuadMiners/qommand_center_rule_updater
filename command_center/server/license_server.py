import random

from quadlibrary.AppObject import QObject

from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.license import license_pb2
from command_center import RequestCheckMixin
from command_center.server import SiteMixin
import command_center.library.database as db


class QmcLicenseService(SiteMixin, RequestCheckMixin, rule_update_service_pb2_grpc.LicenseServiceServicer):

    def Register(self, request, context):
        return self._license_response(request, reg=True)

    def Status(self, request, context):
        return self._license_response(request)

    def _license_response(self, request, reg=False):
        raw_license = None
        approval_user = None
        approval_contents = None
        if reg:
            check_result = self._register_server_check(request.server.hardware_uuid, request.server.machine_id)
        else:
            check_result = self._register_server_check(request.hardware_uuid, request.machine_id)
        if check_result.approve_type is None:
            if reg:
                site_info = self._register_server(request)
                if site_info is None:
                    approve_type = license_pb2.LicenseStatus.SITE_NONE
                    """
                        Site 가 없음.
                    """
                else:
                    approve_type = license_pb2.LicenseStatus.WAIT
        elif check_result.approve_type == 'confirm':
            # 컴펌됨.
            approve_type = license_pb2.LicenseStatus.CONFIRM
            if reg:
                raw_license = self._license_raw(request.server.hardware_uuid, request.server.machine_id)
            else:
                raw_license = self._license_raw(request.hardware_uuid, request.machine_id)
        elif check_result.approve_type == 'wait':
            approve_type = license_pb2.LicenseStatus.WAIT
        elif check_result.approve_type == 'reject':
            approve_type = license_pb2.LicenseStatus.REJECT
            approval_user = check_result.approve_user_id
            approval_contents = check_result.content

        print(license_pb2.LicenseResponse(status=approve_type, license_data=raw_license, approval_user=approval_user,approval_contents=approval_contents ))
        return license_pb2.LicenseResponse(status=approve_type, license_data=raw_license, approval_user=approval_user,approval_contents=approval_contents )

    def _register_server_check(self, hardware_uuid, machine_id):
        """
            등록되어있는 사이트 라이센스가 있는지 확인

            - 결제 되면 서버마다 1개의 정보가 있을것으로 확신한다.
            - 갱신은 없다.

        """
        approve_type=None
        content=None
        approval_user=None
        approval_time = None

        query = """
                SELECT approve_type, content, approval_user_id, approval_time 
                FROM site_license_approve
                WHERE server_info_id in (
                        SELECT id FROM site_server_info 
                        WHERE hardware_uuid = '{hardware_uuid}' 
                            AND machine_id = '{machine_id}'
                            AND delete_flag = 'N'
                    )
                AND delete = False
                """.format(**dict(hardware_uuid=hardware_uuid, machine_id=machine_id))

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                approve_type, content, approval_user, approval_time, = pcursor.fetchone()

        return QObject(dict(approve_type=approve_type, content=content, approval_user=approval_user, approval_time=approval_time))

    def _register_server(self,request):
        """
            서버 등록
        """
        server = request.server
        site_info = self.get_site(request.site_code)
        if site_info:
            query = """
                     INSERT INTO site_server_info (server_id,  site_id, type, name, hostname, ipaddr, version, os_ver, reg_user_id, reg_date, delete_flag, ssh_connection_info ,bps, hardware_uuid, machine_id, server_roll_type)
                         VALUES({0}, {1}, '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', 2, now(), 'N', '', 1, '{8}', '{9}', 'nbb')
                         ON CONFLICT (hardware_uuid,machine_id, site_id)  DO UPDATE SET site_id = excluded.site_id 
                         RETURNING id
                 """.format(random.randrange(100, 9000, 3) % 100 * 100, site_info.id, server.type, site_info.name,
                            server.hostname, server.ipaddr, server.version, server.os_ver, server.hardware_uuid, server.machine_id)

            s_id = db.pmdatabase.execute(query, returning_id=True)

            """
                 id | approve_type | content | request_time | approval_time | delete | approval_user_id | request_user_id | server_info_id
            """
            query_approve = """
                        INSERT INTO site_license_approve( server_info_id, approve_type, request_user, request_time, delete)
                        VALUES({0}, 'wait', '{1}', now(),False)
                    """.format(s_id, '{0}({1})'.format(request.reg_user_name, request.reg_user_tel))
            db.pmdatabase.execute(query_approve)

        return site_info

    def _license_raw(self, hardware_uuid, machine_id):

        license_data = None

        query = """ 
                SELECT raw FROM site_server_license as license 
                JOIN (SELECT id FROM site_server_info WHERE hardware_uuid = '{hardware_uuid}' 
                        AND machine_id = '{machine_id}' ) as server
                ON license.server_info_id = server.id
                WHERE license.expire is False
                """.format(**dict(hardware_uuid=hardware_uuid,
                                  machine_id=machine_id))

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                license_data, = pcursor.fetchone()
        print(license_data)

        return license_data
