import logging

from termcolor import cprint

from command_center.client import ClientRequestMixin
from command_center.client.data_insert.snort import SnortMixin
from command_center.library.rpc.retry import retrying_stub_methods
from command_center.protocol import rule_update_service_pb2_grpc

from command_center.protocol.data.data_pb2 import DataVersion, DataRequest, DataVersionRequest, DataType, DataLevel
import command_center.library.database as db

logger = logging.getLogger(__name__)


class DataClientMixin(SnortMixin,ClientRequestMixin):
    """"""
    """
        1. 타겟의 버전 정보를 요청한다.
        2. 타겟의 버전 정보들을 받아오면 check_version을 수행한다.
    """
    def GetVersions(self):

        try:
            with self.get_command_center_channel() as channel:
                stub = rule_update_service_pb2_grpc.DataUpdateServiceStub(channel)
                retrying_stub_methods(stub)
                request_server = self.get_request_server()
                response_data = stub.GetVersions(DataVersionRequest(server=request_server), timeout=10)
                self.check_versions(response_data.versions)

        except Exception as k:
            logger.error("Heartbeat Schedule Exception: {0}".format(k))

    def GetData(self, data_type, version, level=DataLevel.L_UPDATE):
        get_version = None
        status = None
        with self.get_command_center_channel() as channel:
            request_server = self.get_request_server()
            data_version = DataVersion(type=data_type, version=version)
            stub = rule_update_service_pb2_grpc.DataUpdateServiceStub(channel)
            retrying_stub_methods(stub)
            response_data = stub.GetData(DataRequest(level=level,server=request_server, version=data_version), timeout=10)

            status, get_version = self.__update_data_version(data_type,response_data, level)

        return status, get_version

    def UpdateVersion(self, type, version):
        """
            서버 반영이 완료되면 전송함.
        """
        with self.get_command_center_channel() as channel:
            stub = rule_update_service_pb2_grpc.DataUpdateServiceStub(channel)
            retrying_stub_methods(stub)

            request_server = self.get_request_server()
            data_version = DataVersion(type=type, version=version)
            stub.UpdateVersion(DataRequest(server=request_server, version=data_version), timeout=10)

    def __update_data_version(self, data_type, request, data_level):
        version = request.version
        status = request.status
        datas = request.datas

        if status:
            if data_type == DataType.SNORT:
                status_id = self.status_insert(version.version, status)
                self.snort_insert(status_id, version.version, datas, data_level)
            """
                처음 Sync 되는 경우 데이터가 version 정보가 없으므로 추가작업 없으려고 upsert 로 만듬.
            """
            query = """INSERT INTO data_last_versions(version, data_type)
                        VALUES({0}, {1})
                       ON CONFLICT (data_type) 
                       DO UPDATE SET version= excluded.version, data_type= excluded.data_type
                    """.format(version.version, version.type)
            db.pmdatabase.execute(query)
        else:
            status = None

        return status, version.version

    """
        1. 자신의 마지막 버전과 받아온 버전(parameter versions값)을 비교한다.
        2. 비교해서 자신의 버전이 더 낮다면 버전 업그레이드를 위해 GetData를 호출한다.
        3. 버전 요청시에 last_version 보다 한단계 높은 버전을(+1) 받아온다.
        4. 버전 차이가 난다면 계속 해서 +1 버전 업하면 받아온다.
    """

    def _update_data(self, data_type, version, update_level):
        while True:
            status, version = self.GetData(data_type, version, level=update_level)
            if status:
                """ 최초 이후에는 업데이트된 정보만 가져온다. """
                if update_level == DataLevel.L_ALL:
                    update_level = DataLevel.L_UPDATE
                cprint("Version Upgrade Success : {0}".format(version), "yellow")
                version = version + 1
            else:
                break

    def check_versions(self, versions):
        """
            daemon load 할때 기본값으로 각 데이터 version 들고 비교
        """
        for data_version in versions:
            """
                version 체크 다르면 api 호출해서 업그레이드 
            """
            query = "SELECT version FROM data_last_verions WHERE type = {0}".format(data_version.type)
            version = 0
            with db.pmdatabase.get_cursor() as pcursor:
                pcursor.execute(query)
                if pcursor.rowcount > 0:
                    version, = pcursor.fetchone()
                    
            if data_version.type == DataType.SNORT:
                if version < data_version.version:
                    level = (version and DataLevel.L_UPDATE or DataLevel.L_ALL)
                    self._update_data(data_version.type, version=version, update_level=level)





