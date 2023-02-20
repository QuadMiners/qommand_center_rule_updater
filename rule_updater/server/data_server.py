from library.database.fquery import fetchall_query_to_dict
from protocol import rule_update_service_pb2_grpc
from protocol.data import data_pb2
from rule_updater import RequestCheckMixin
import library.database as db

class QmcDataService(RequestCheckMixin, rule_update_service_pb2_grpc.DataUpdateServiceServicer):

    def GetVersions(self, request, context):

        site_id = request.server.site_id
        license_uuid = request.server.license_uuid

        query = f"SELECT * FROM server_info WHERE site_id = '{site_id}' AND license_uuid = '{license_uuid}'"
        result_dict = fetchall_query_to_dict(query)

        response = data_pb2.DataVersionResponse()
        for i in range(len(result_dict)):
            version = data_pb2.DataVersion(type=result_dict[i]["type"], version=result_dict[i]["version"])
            response.versions.append(version)

        return response

    def GetData(self, request, context):
        request_server = request.server
        site_id = request_server.site_id
        license_uuid = request_server.license_uuid

        data_version = request.version
        data_type = data_version.type
        data_version = data_version.version

        response = data_pb2.DataResponse()
        response.versions = ""
        response.data = ""

        return None

    def UpdateVersion(self, request, context):
        pass
