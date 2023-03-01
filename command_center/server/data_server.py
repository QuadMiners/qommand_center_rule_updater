import logging

from google.protobuf.struct_pb2 import Struct
from termcolor import cprint

from command_center.library.rpc import query_to_object
from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.data import data_pb2
from command_center import RequestCheckMixin
from command_center.library.AppConfig import gconfig
from command_center.protocol.data.data_pb2 import DataType, DataVersion, DataLevel
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
        data_level = request.level
        type = request.version.type
        version = request.version.version
        status = None
        datas = list()

        min_version = (gconfig.command_center.model == 'relay' and 200000 or 100000)
        if self.request_check(request.server):
            if type == DataType.SNORT:
                if version == 0:
                    """ 초기 정보 가저올때 전체 업데이트를 위해서 이렇게 하면 전체 가져오기
                        relay 서버의 경우 200000 번부터 시작인걸 요청하는곳 (NBB) 에게 줘야한다.
                     """
                    status_query = "SELECT  * FROM rule_status WHERE state in ('ARCHIVE', 'RELEASE') AND version >= {0} ORDER BY id limit 1".format(min_version)
                else:
                    status_query = "SELECT  * FROM rule_status WHERE version = {0} AND state in ('ARCHIVE', 'RELEASE')".format(version)
                cprint(status_query, 'green')
                status_value = query_to_object(status_query, Struct)
                if len(status_value) > 0:
                    status = status_value[0]
                    version = status['version']
                    print(data_level)
                    if data_level == DataLevel.L_ALL:
                        query = "SELECT * FROM rule_master_hunt_history WHERE version = {0}".format(version)
                    else:
                        """ eq 이 아닌것들만 가져온다. """
                        query = "SELECT * FROM rule_master_hunt_history WHERE version = {0} AND merge_code != 1 ".format(version)
                    cprint(query, 'green')
                    datas = query_to_object(query, Struct)

        return data_pb2.DataResponse(version=DataVersion(type=type, version=int(version)), status=status, datas=datas)

    def UpdateVersion(self, request, context):
        """
            해당 사이트의 서버 별로 업데이트 여부
            패치 - 버전
            Rule 버전 - 추후 컬럼 만들어야함.
        """
        type = request.version.type
        version = request.version.version

        if self.request_check(request.server):
            pass

        return None


