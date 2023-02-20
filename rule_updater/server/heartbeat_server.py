from library.database.fquery import fetchall_query_to_dict, fetchone_query_to_dict
from protocol import rule_update_service_pb2_grpc
from protocol.data import data_pb2
from protocol.heartbeat import heartbeat_pb2
from protocol.heartbeat.heartbeat_pb2 import ServerStatus, HeartbeatResponse, DataUpdateFlag

from rule_updater import RequestCheckMixin


class QmcHeartbeatService(RequestCheckMixin, rule_update_service_pb2_grpc.HeartbeatServiceServicer):

    # 하트비트 Request 처리
    def Heartbeat(self, request, context):
        # Request
        site_id = request.server.site_id
        license_uuid = request.server.license_uuid
        str_type = request.datas.str_type
        data = request.datas.data

        # Response
        response_status = None
        response_site_update_flag = None
        response_license_update_flag = None
        response_versions = data_pb2.DataVersion()

        # 결과값 설정
        query = f"SELECT * FROM server_info WHERE site_id = '{site_id}' AND hardware_key = '{license_uuid}'"
        result_dict = fetchone_query_to_dict(query)
        if result_dict is 0:
            response_status = heartbeat_pb2.ServerStatus.NOTFOUND
            return heartbeat_pb2.HeartbeatResponse(status=response_status,
                                                   site_update_flag=None,
                                                   license_update_flag=None,
                                                   versions=None)
        else:
            response_status = heartbeat_pb2.ServerStatus.REGISTER

        query = f"SELECT * FROM site WHERE id = '{site_id}'"
        result_dict = fetchone_query_to_dict(query)
        if result_dict["update_server_status"] is False:
            response_site_update_flag = heartbeat_pb2.DataUpdateFlag.NONE_FLAG
        else:
            response_site_update_flag = heartbeat_pb2.DataUpdateFlag.UPDATE

        query = f"SELECT * FROM server_license WHERE id = '{license_uuid}' "
        result_dict = fetchone_query_to_dict(query)
        if result_dict["update_server_status"] is False:
            response_license_update_flag = heartbeat_pb2.DataUpdateFlag.NONE_FLAG
        else:
            response_license_update_flag = heartbeat_pb2.DataUpdateFlag.UPDATE

        # 결과값 - 데이터 타입, 버전 입력
        query = f"SELECT * FROM rule_status"
        result_dict = fetchall_query_to_dict(query)
        if len(result_dict) > 0:
            for i in range(len(result_dict)):
                version = data_pb2.DataVersion(type=result_dict[i]["type"],
                                               version=result_dict[i]["version"])
                response_versions.append(version)
        else:
            response_versions = None

        # 최종 결과값 도출 상태, 버전 데이터등..
        response = heartbeat_pb2.HeartbeatResponse(status=response_status,
                                                   site_update_flag=response_site_update_flag,
                                                   license_update_flag=response_license_update_flag,
                                                   versions=response_versions)

        return response
