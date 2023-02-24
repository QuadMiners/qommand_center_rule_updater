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
                    "desc" = '{desc}', 
                    engineer = '{engineer}', 
                    sales = '{sales}' 
                WHERE name = '{name}'
                """.format(**site_dict)
        db.pmdatabase.execute(query)

    def _update_server(self, servers_info):
        for server in servers_info:
            server_dict = protobuf_to_dict(server)

            query = """
                    INSERT INTO black.server_info 
                    (id, name, type, version, hostname, ipaddr) 
                    VALUES('{id}', '{name}', '{server_type}', '{version}', '{host_name}', '{ipaddr}') 
                    ON CONFLICT (id) DO UPDATE 
                    SET id = '{id}',
                        name = '{name}',
                        type = '{server_type}', 
                        version = '{version}', 
                        hostname = '{host_name}', 
                        ipaddr = '{ipaddr}' 
                    WHERE black.server_info.id = '{id}'
                    """.format(**server_dict)
            db.pmdatabase.execute(query)

            query="""
                  INSERT INTO black.license 
                  (info) 
                  VALUES ('license_data')
                  ON CONFLICT (server_info_id) DO UPDATE
                  SET info = '{license_data}' 
                  WHERE server_info_id = '{id}'
                  """.format(**server_dict)
            db.pmdatabase.execute(query)

    def GetSite(self):
        channel = self.get_update_server_channel()
        stub = rule_update_service_pb2_grpc.SiteServiceStub(channel)
        retrying_stub_methods(stub)

        """
            서버에게 요청 response_data에 값 받아옴
        """
        request_server = self.get_request_server()
        response_data = stub.GetSite(site_pb2.SiteRequest(server=request_server), timeout=10)

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
        request_packet.server_id = self.get_server_id()
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
