import logging

from google.protobuf.struct_pb2 import Struct

from command_center.library.rpc import query_to_object
from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.data import data_pb2
from command_center import RequestCheckMixin
from command_center.library.AppConfig import gconfig
from command_center.protocol.data.data_pb2 import DataType
import command_center.library.database as db

logger = logging.getLogger(__name__)

class QmcDataService(RequestCheckMixin, rule_update_service_pb2_grpc.DataUpdateServiceServicer):

    def GetVersions(self, request, context):

        site_id = request.server.site_id
        license_uuid = request.server.license_uuid

        if self.request_check(request.server):
            query = "SELECT type, version FROM data_last_version"
            response_versions = list()

            with db.pmdatabase.get_cursor() as pcursor:
                pcursor.execute(query)
                rows = pcursor.fetchall()
                for row in rows:
                    response_versions.append(data_pb2.DataVersion(type=row[0], version=row[1]))

            return data_pb2.DataVersionResponse(versions=response_versions)
        else:
            return data_pb2.DataVersionResponse(versions=list())

    def GetData(self, request, context):
        type = request.version.type
        version = request.version.version
        datas = None

        if self.request_check(request.server):
            if type == DataType.SNORT:
                if gconfig.command_center.model == 'relay':
                    query = "SELECT enabled, raw FROM rule_master_hunt_history WHERE version = {version}".format(version)
                    datas = query_to_object(query, Struct)

        response = data_pb2.DataResponse()
        response.versions = version
        response.data = datas
        return response

    def UpdateVersion(self, request, context):
        """
            해당 사이트의 서버 별로 업데이트 여부
            패치 - 버전
            Rule 버전 - 추후 컬럼 만들어야함.
        """
        type = request.version.type
        version = request.version.version

        if self.request_check(request.server):
            # query = f"UPDATE site_server_info SET target_version = '{version}' " \
            #         f"WHERE type = '{type}'"
            # db.pmdatabase.execute()
            pass

        return None


