import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import logging

from library.rpc.convertor import protobuf_to_dict
from library.rpc.retry import retrying_stub_methods
from protocol import rule_update_service_pb2_grpc
from protocol.site import site_pb2
from rule_updater import ResponseRequestMixin, ChannelMixin

logger = logging.getLogger(__name__)

import library.database as db

class SiteClientMixin(ChannelMixin, ResponseRequestMixin):

    """
        client가 서버에게 사이트, 서버 정보를 요청하는 함수.
    """

    def _update_site(self, site_info):
        site_dict = protobuf_to_dict(site_info)
        query = """ 
                UPDATE black.site
                SET name = '{name}',
                    address = '{address}',
                    tel = '{tel}', 
                    desc = '{desc}'
                    engineer = '{engineer}'
                    sales = '{sales}' 
                WHERE name = {name}
                """.format(**site_dict)
        db.pmdatabase.execute(query)

    def _update_server(self, servers_info):
        for server in servers_info:
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

        print(response_data.site)
        print(response_data.servers)

        """
            받아온 사이트 데이터 파싱, 업데이트
        """
        self._update_site(response_data.site)

        """
            받아온 서버 데이터 파싱, 업데이트
        """
        self._update_server(response_data.servers)


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


"""
Test Code
"""
def main():
    a = SiteClientMixin()
    a.GetSite()


if __name__ == '__main__':
    main()
