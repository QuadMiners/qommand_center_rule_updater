from library.database.fquery import fetchall_query_to_dict, fetchone_query_to_dict
from protocol import rule_update_service_pb2_grpc
from protocol.data import data_pb2
from protocol.heartbeat import heartbeat_pb2
from protocol.heartbeat.heartbeat_pb2 import ServerStatus, HeartbeatResponse, DataUpdateFlag
import library.database as db

from rule_updater import RequestCheckMixin


class QmcHeartbeatService(RequestCheckMixin, rule_update_service_pb2_grpc.HeartbeatServiceServicer):
    def _site(self, site_id):
        query = f"SELECT update_server_status FROM site WHERE id = '{site_id}'"
        update_server_status = False
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                update_server_status = pcursor.fetchone()
        return update_server_status

    def _data_version(self):
        query = "SELECT type, version FROM data_version"
        response_versions = list()

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            rows = pcursor.fetchall()
            for row in rows:
                response_versions.append(data_pb2.DataVersion(type=row[0], version=row[1]))

        return response_versions

    def _data_license(self):
        query = "SELECT type, version FROM site_license"
        response_versions = data_pb2.DataVersion()

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            rows = pcursor.fetchall()
            for row in rows:
                response_versions.append(data_pb2.DataVersion(type=row[0], version=row[1]))

        return response_versions

    # 하트비트 Request 처리
    def Heartbeat(self, request, context):
        # Request
        data = request.datas.data
        # 나중에


        # Response
        response_status = None
        response_site_update_flag = None
        response_license_update_flag = None
        response_versions = None
        # 결과값 설정

        if self.request_check(request.server) == False:
            response_status = heartbeat_pb2.ServerStatus.NOTFOUND
        else:
            response_status = heartbeat_pb2.ServerStatus.REGISTER

            update_server_status = self._site(request.server.site_id)
            response_site_update_flag = ( update_server_status is False and heartbeat_pb2.DataUpdateFlag.NONE_FLAG or heartbeat_pb2.DataUpdateFlag.UPDATE )

            update_licese_status = self._license(request.server.site_id)
            response_license_update_flag = ( update_licese_status is False and heartbeat_pb2.DataUpdateFlag.NONE_FLAG or heartbeat_pb2.DataUpdateFlag.UPDATE )
            response_versions = self._data_version()

            # 최종 결과값 도출 - 상태, 버전 데이터등..
        return heartbeat_pb2.HeartbeatResponse(status=response_status,
                                                   site_update_flag=response_site_update_flag,
                                                   license_update_flag=response_license_update_flag,
                                                   versions=response_versions)
