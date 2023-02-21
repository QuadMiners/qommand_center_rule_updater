import logging
import time

from library.database.fquery import fetchone_query_to_dict
from library.rpc.retry import retrying_stub_methods
from protocol import rule_update_service_pb2_grpc
from protocol.site import site_pb2
from rule_updater import ResponseRequestMixin

logger = logging.getLogger(__name__)


class SiteClientMixin(ResponseRequestMixin):

    """
        client가 서버에게 사이트, 서버 정보를 요청하는 함수.
    """
    def GetSite(self):
        channel = self.get_update_server_channel()
        stub = rule_update_service_pb2_grpc.SiteServiceStub(channel)
        retrying_stub_methods(stub)

        """
            서버에게 요청 response_data에 값 받아옴
        """
        request_packet = site_pb2.SiteRequest()
        request_packet.server = self.get_request_server()
        response_data = stub.GetSite(request_packet, timeout=10)

        """
            받아온 사이트 데이터 파싱, 업데이트
        """
        site_info = response_data.site
        name = site_info.name
        address = site_info.address
        tel = site_info.tel
        desc = site_info.desc
        engineer = site_info.engineer
        sales = site_info.sales

        query = f"UPDATE black.site SET name = '{name}', " \
                f"address = '{address}', " \
                f"tel = '{tel}', " \
                f"desc = '{desc}' " \
                f"engineer = '{engineer}' " \
                f"sales = '{sales}' " \
                f"WHERE name = {name}"

        result = fetchone_query_to_dict(query)

        """
            받아온 서버 데이터 파싱, 업데이트
        """
        for server in response_data.servers:
            server_id = server.id
            server_name = server.name
            server_type = server.type
            server_version = server.version
            server_host_name = server.host_name
            server_ipaddr = server.ipaddr
            server_license_data = server.license_data

            query = f"UPDATE black.server_info SET server_id = '{server_id}', " \
                    f"name = '{server_name}', " \
                    f"type = '{server_type}', " \
                    f"version = '{server_version}' " \
                    f"engineer = '{engineer}' " \
                    f"hostname = '{server_host_name}' " \
                    f"ipaddr = '{server_ipaddr}' " \
                    f"license_data = '{server_license_data}' " \
                    f"WHERE name = {name}"

            result = fetchone_query_to_dict(query)


    def GetServer(self, data):
        channel = self.get_update_server_channel()
        stub = rule_update_service_pb2_grpc.SiteServiceStub(channel)
        retrying_stub_methods(stub)

        """
            서버에게 단일 서버 정보만 요청한다.
        """
        request_packet = site_pb2.ServerRequest()
        request_packet.server = self.get_request_server()
        request_packet.server_id = None
        response_data = stub.GetSite(request_packet, timeout=10)
        server = response_data.server

    def UpdateServer(self):
        self.scheduler.every(self.time_period).seconds.do(self.version_check)

        while self._exit is False:
            self.scheduler.run_pending()
            time.sleep(1)


