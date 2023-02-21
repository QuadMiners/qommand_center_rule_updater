import logging
import time

from library.database.fquery import fetchall_query_to_dict, fetchone_query_to_dict
from library.rpc.retry import retrying_stub_methods
from protocol import rule_update_service_pb2_grpc

from protocol.data.data_pb2 import DataVersion, DataRequest, DataVersionRequest, DataType
from rule_updater import ResponseRequestMixin

logger = logging.getLogger(__name__)


class DataClientMixin(ResponseRequestMixin):

    def GetVersions(self):
        try:
            """
                자신의 서버 Version정보를 데이터베이스에서 읽어와서
                grpc로 Check Packet 날리는 반복작업 코드 작성 필요.
            """
            channel = self.get_update_server_channel()
            request_server = self.get_request_server()

            stub = rule_update_service_pb2_grpc.DataUpdateServiceStub(channel)
            retrying_stub_methods(stub)

            response_data = stub.GetVersions(DataVersionRequest(server=request_server), timeout=10)
            self.check_versions(response_data.versions)

        except Exception as k:
            logger.error("Heartbeat Schedule Exception: {0}".format(k))

    def check_versions(self, versions):
        """
            daemon load 할때 기본값으로 각 데이터 version 들고 비교
        """
        for data_version in versions:
            if data_version.type == DataType.SNORT:
                """
                    version 체크 다르면 api 호출해서 업그레이드 
                """
                query = "SELECT * FROM black.data_last_verions WHERE type = 'SNORT'"
                result_dict = fetchone_query_to_dict(query)

                if result_dict['version'] < data_version.version:
                    self.GetData(data_version.type, version=result_dict['version'] + 1)


    def GetData(self, type, version):
        channel = self.get_update_server_channel()

        request_server = self.get_request_server()
        data_version = DataVersion(type=type, version=version)

        stub = rule_update_service_pb2_grpc.DataUpdateServiceStub(channel)
        retrying_stub_methods(stub)
        response_data = stub.GetData(DataRequest(server=request_server, version=data_version), timeout=10)

        self.__update_data_version(response_data.version, response_data.data)

    def UpdateVersion(self, type, version):
        """
            서버 반영이 완료되면 전송함.
        """
        channel = self.get_update_server_channel()

        request_server = self.get_request_server()
        data_version = DataVersion(type=type, version=version)

        stub = rule_update_service_pb2_grpc.DataUpdateServiceStub(channel)
        retrying_stub_methods(stub)
        stub.UpdateVersion(DataRequest(server=request_server, version=data_version), timeout=10)


    def __update_data_version(self, data_version, data):
        type = data_version.type
        version = data_version.version
        last_version = version + 1

        query = f"UPDATE black.data_last_verions SET version = '{last_version}' WHERE type = '{type}'"
        result_dict = fetchone_query_to_dict(query)

        if result_dict is not None and result_dict != 0:
            # 정상 처리됨
            pass

        """
        받은 version data 처리.. Release된 파일을 받아온것.. 파싱후 DB에 넣어야한다.
        """





