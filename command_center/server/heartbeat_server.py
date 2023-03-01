from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.data import data_pb2
from command_center.protocol.heartbeat import heartbeat_pb2

from command_center import RequestCheckMixin, ServerType
import command_center.library.database as db


class QmcHeartbeatService(RequestCheckMixin, rule_update_service_pb2_grpc.HeartbeatServiceServicer):

    def _save_request_data(self, data):
        pass

    def _site_relay(self, site_code):

        query = """SELECT count(*) FROM site 
                        WHERE id in ( SELECT site_id 
                                      FROM relay_server_sites 
                                      WHERE relayserver_id IN ( SELECT id 
                                                                FROM relay_server WHERE site_code = '{0}'
                                                                )
                                    )
                        AND update_server_status = true
                """.format(site_code)
        update_server_status = 0
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            update_server_status, = pcursor.fetchone()
        return update_server_status > 0 and True or False

    def _license_relay(self, site_code):
        query = """SELECT count(*) FROM site_server_license 
                    WHERE server_info_id in ( SELECT id FROM site_server_info 
                                              WHERE site_id in ( SELECT site_id FROM relay_server_sites 
                                                                WHERE relayserver_id IN ( SELECT id FROM relay_server 
                                                                                        WHERE site_code = '{0}'
                                                                                        )
                                                                )
                                             )
                    AND update_server_status = true
                """.format(site_code)

        update_server_status = 0

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            update_server_status, = pcursor.fetchone()
        return update_server_status > 0 and True or False


    def _site_nbb(self, site_code):

        query = "SELECT update_server_status FROM site WHERE code = '{0}'".format(site_code)
        update_server_status = False
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                update_server_status, = pcursor.fetchone()
        return update_server_status

    def _license_nbb(self, site_code, hardware_uuid):
        update_server_status = None
        auto_update = None
        expires = None
        """
            마지막 License 가 있는지 업데이트 되었는지 확인
            마지막 내용만 업데이트하고 만약 가저가지 않았더라도 전부 가저간걸로 한다.
            update_server_status = True 로 변경  
        """
        query = """
                SELECT update_server_status FROM site_server_license
                WHERE server_info_id in ( SELECT id FROM site_server_info WHERE site_id in ( SELECT id FROM site WHERE site_code = '{site_code}' and hardware_uuid = '{server_uuid}'))
                ORDER BY id desc limit 1
                """.format(**dict(site_code=site_code, hardware_uuid=hardware_uuid))

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                update_server_status, = pcursor.fetchone()

        return update_server_status

    def _data_version(self):
        query = "SELECT data_type, version FROM data_last_versions"
        response_versions = list()

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            rows = pcursor.fetchall()
            for row in rows:
                response_versions.append(data_pb2.DataVersion(type=row[0], version=row[1]))

        return response_versions

    # 하트비트 Request 처리
    def Heartbeat(self, request, context):
        # Request
        self._save_request_data( request.datas)

        # Response
        response_status = None
        response_site_update_flag = None
        response_license_update_flag = None
        response_versions = None
        # 결과값 설정

        if self.request_check(request.server) is False:
            response_status = heartbeat_pb2.ServerStatus.NOTFOUND
        else:
            response_status = heartbeat_pb2.ServerStatus.REGISTER
            if request.server.server_type == ServerType.RELAY:
                update_server_status = self._site_relay(request.server.site_code)
                response_site_update_flag = (update_server_status and heartbeat_pb2.DataUpdateFlag.UPDATE or heartbeat_pb2.DataUpdateFlag.NONE_FLAG)
                update_licese_status = self._license_relay(request.server.site_code)
                response_license_update_flag = (update_licese_status and heartbeat_pb2.DataUpdateFlag.UPDATE or heartbeat_pb2.DataUpdateFlag.NONE_FLAG)
            else:
                update_server_status = self._site_nbb(request.server.site_code)
                response_site_update_flag = (update_server_status and heartbeat_pb2.DataUpdateFlag.UPDATE or heartbeat_pb2.DataUpdateFlag.NONE_FLAG)
                update_licese_status = self._license_nbb(request.server.site_code, request.server.hardware_uuid)
                response_license_update_flag = (update_licese_status and heartbeat_pb2.DataUpdateFlag.UPDATE or heartbeat_pb2.DataUpdateFlag.NONE_FLAG)
            response_versions = self._data_version()
            self.update_heatbeat_status(request)

            # 최종 결과값 도출 - 상태, 버전 데이터등..
        return heartbeat_pb2.HeartbeatResponse(status=response_status,
                                               site_update_flag=response_site_update_flag,
                                               license_update_flag=response_license_update_flag,
                                               versions=response_versions)
