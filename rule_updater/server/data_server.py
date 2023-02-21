from library.database.fquery import fetchall_query_to_dict, fetchone_query_to_dict
from protocol import rule_update_service_pb2_grpc
from protocol.data import data_pb2
from rule_updater import RequestCheckMixin
import library.database as db

class QmcDataService(RequestCheckMixin, rule_update_service_pb2_grpc.DataUpdateServiceServicer):

    def GetVersions(self, request, context):

        site_id = request.server.site_id
        license_uuid = request.server.license_uuid

        if self.request_check(request.server) == True:
            query = f"SELECT * FROM rule_status "
            result_dict_list = fetchall_query_to_dict(query)

            response = data_pb2.DataVersionResponse()
            for result_dict in result_dict_list:
                version = data_pb2.DataVersion(type=result_dict["type"], version=result_dict["version"])
                response.versions.append(version)

            return response
        else:
            return None


    def GetData(self, request, context):

        type = request.version.type
        version = request.version.version

        if self.request_check(request.server) == True:

            query = f"SELECT * FROM black.rule_status WHERE type = '{type}'"
            result_dict = fetchone_query_to_dict(query)

            response = data_pb2.DataResponse()
            response.versions = result_dict['versions']

            with open(result_dict['filename'], "r") as f:
                data = f.read() # TODO:압축해야한다.

            response.data = data

            return response

    def UpdateVersion(self, request, context):

        type = request.version.type
        version = request.version.version

        if self.request_check(request.server) == True:
            query = f"UPDATE black.rule_status SET target_version = '{version}' " \
                    f"WHERE type = '{type}'"
            fetchone_query_to_dict(query)

        return None


