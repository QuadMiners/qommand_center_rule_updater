import logging
import time

from library.database.fquery import fetchone_query_to_dict
from library.rpc.convertor import protobuf_to_dict
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
        db.pmdatabase.execute(query)

        """
            받아온 서버 데이터 파싱, 업데이트
        """
        for server in response_data.servers:
            server_dict = protobuf_to_dict(server)
            query =""" UPDATE black.server_info
                       SET server_id = '{server_id}',
                            name = '{server_name}',
                            type = '{server_type}', 
                            version = '{server_version}'
                            engineer = '{engineer}'
                            hostname = '{server_host_name}' 
                            ipaddr = '{server_ipaddr}'
                            license_data = '{server_license_data}' 
                        WHERE name = {name}
                    """.format(**server_dict)
            db.pmdatabase.execute(query)

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


