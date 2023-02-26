import logging

from command_center.library.rpc.retry import retrying_stub_methods
from command_center.protocol import rule_update_service_pb2_grpc

from command_center.protocol.data.data_pb2 import DataVersion, DataRequest, DataVersionRequest, DataType
from command_center import ResponseRequestMixin

from command_center.library.rule.parser import parse
import command_center.library.database as db

logger = logging.getLogger(__name__)


class DataClientMixin(ResponseRequestMixin):
    """"""
    """
        1. 타겟의 버전 정보를 요청한다.
        2. 타겟의 버전 정보들을 받아오면 check_version을 수행한다.
    """
    def GetVersions(self):

        try:
            channel = self.get_update_server_channel()
            stub = rule_update_service_pb2_grpc.DataUpdateServiceStub(channel)
            retrying_stub_methods(stub)

            request_server = self.get_request_server()
            response_data = stub.GetVersions(DataVersionRequest(server=request_server), timeout=10)
            self.check_versions(response_data.versions)

        except Exception as k:
            logger.error("Heartbeat Schedule Exception: {0}".format(k))

    """
        1. 자신의 마지막 버전과 받아온 버전(parameter versions값)을 비교한다.
        2. 비교해서 자신의 버전이 더 낮다면 버전 업그레이드를 위해 GetData를 호출한다.
        3. 버전 요청시에 last_version 보다 한단계 높은 버전을(+1) 받아온다.
        4. 버전 차이가 난다면 계속 해서 +1 버전 업하면 받아온다.
    """
    def check_versions(self, versions):
        """
            daemon load 할때 기본값으로 각 데이터 version 들고 비교
        """
        for data_version in versions:
            """
                version 체크 다르면 api 호출해서 업그레이드 
            """
            query = "SELECT version FROM data_last_verions WHERE type = {0}".format(data_version.type)
            version = None
            with db.pmdatabase.get_cursor() as pcursor:
                pcursor.execute(query)
                version, = pcursor.fetchone()
            if data_version.type == DataType.SNORT:
                if version < data_version.version:
                    self.GetData(data_version.type, version=version + 1)

    """
        1. 필요한 데이터 타입의 버전을 요청한다.
        2. 서버로 부터 버전 데이터를 받는다.
        3. 알맞게 업데이트 한다. __update_data_version
    """
    def GetData(self, type, version):
        channel = self.get_update_server_channel()

        request_server = self.get_request_server()
        data_version = DataVersion(type=type, version=version)

        stub = rule_update_service_pb2_grpc.DataUpdateServiceStub(channel)
        retrying_stub_methods(stub)
        response_data = stub.GetData(DataRequest(server=request_server, version=data_version), timeout=10)

        self.__update_data_version(response_data.version, response_data.data)

        """
        1. 자신의 업데이트가 완료되면 업데이트가 완료되었다고 전송한다.
        2. 
        3. 전송값은 데이터 타입과 업데이트한 last_version이 될것.
        """

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

        """
            파일을 받아와서 우선 저장한다.
        """
        with open(type+"_"+last_version, "w") as f:
            f.write(data)

        f = open(type+"_"+last_version, "r")
        for line in f.readlines():
            rule = parse(line)
            #추가 해야함...
            """
                받은 version data 처리.. 
                1.  Release된 파일을 받아온다. 
                2.  파싱후 master_hunt의 status_id를 가지고 조인하여 rule_status 테이블에서 status=release 인것과 머징한다.
                3.  머징 기준은 받아온 파일이 우선시 된다. 즉, update와 insert만 이루어진다.
                4.  그후 master_hunt의 table에 데이터를 넣는다.
                5.  master_hunt 테이블 작업이 완료되면 자신의 data_last_version table을 업데이트 해준다.
                6.  그후 UpdateVersion을 호출한다.
                
                execution_type = QMCD 을 추가해야한다.
                master_hunt DB에 넣어야한다.
            """
        f.close()

        """
            master_hunt의 과정이 끝나면 data_last_version에 해당 타입과 버전 번호를 업데이트한다.
            그 후 UpdateVersion을 호출하여 서버에 알린다.
        """
        query = f"UPDATE black.data_last_verions " \
                f"SET version = '{last_version}' " \
                f"WHERE type = '{type}'"

        result_dict = fetchone_query_to_dict(query)

        self.UpdateVersion(type, last_version)




