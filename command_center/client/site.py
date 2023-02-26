import logging

from command_center import ChannelMixin, ResponseRequestMixin
from command_center.library.rpc.convertor import protobuf_to_dict
from command_center.library.rpc.retry import retrying_stub_methods
from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.heartbeat.heartbeat_pb2 import DataUpdateFlag
from command_center.protocol.site import site_pb2
import command_center.library.database as db

logger = logging.getLogger(__name__)


class SiteClientMixin(ChannelMixin, ResponseRequestMixin):

    """
        client가 서버에게 사이트, 서버 정보를 요청하는 함수.
    """
    def GetSite(self):
        """
            전체 사이트 정보 가저와서 업데이트
        """
        with self.get_update_server_channel() as channel:
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
            self._update_server(response_data.site.site_code, response_data.servers)

    def GetServer(self, flag:DataUpdateFlag, server_id=0):
        """
            사이트 정보에 서버 정보만 가저와서 업데이트
            업데이트 정보만 가저오는 Flag 가 존재해야함.
        """
        with self.get_update_server_channel() as channel:
            stub = rule_update_service_pb2_grpc.SiteServiceStub(channel)
            retrying_stub_methods(stub)
            """
                서버에게 단일 서버 정보만 요청한다.
            """
            request_packet = site_pb2.ServerRequest()
            request_packet.server = self.get_request_server()
            """
                Flag 가 Update 면 업데이트된 정보만 가저온다.
            """
            request_packet.update_flag = flag
            """
                server_id 가 - 0 이면 전체 조회
            """
            request_packet.server_id = server_id
            response_data = stub.GetServer(request_packet, timeout=10)
            server = response_data.server

    def _update_site(self, site_info):
        site_dict = protobuf_to_dict(site_info)
        query = """
                UPDATE site
                SET name = '{name}',
                    address = '{address}',
                    tel = '{tel}', 
                    "desc" = '{desc}', 
                    engineer = '{engineer}', 
                    sales = '{sales}' 
                WHERE name = '{name}'
                """.format(**site_dict)
        db.pmdatabase.execute(query)

    def _update_server(self,site_code, servers_info):
        for server in servers_info:
            server_dict = protobuf_to_dict(server)
            server_dict.update(dict(site_code=site_code))
            query = """
                    INSERT INTO site_server_info (site_id,server_id, name, type, version, hostname, ipaddr, hardware_uuid, machine_id) 
                    VALUES((select id from site FROM code='{site_code}'),'{id}', '{name}', '{server_type}', '{version}', '{host_name}', '{ipaddr}', '{hardware_uuid}', '{machine_id}') 
                    ON CONFLICT (hardware_uuid, machine_id, site_id) DO UPDATE 
                    SET server_id = '{id}',
                        name = '{name}',
                        type = '{server_type}'
                    RETURNING id
                    """.format(**server_dict)

            sid = db.pmdatabase.execute(query, returning_id=True)

            server_dict.update(dict(server_info_id=sid))
            query="""
                INSERT INTO site_server_license (server_info_id, name, type, version, uuid,start_date, end_date, raw, reg_user_id, auto_update, expire, update_server_status )
                  VALUES ('license_data')
                  ON CONFLICT (server_info_id) DO UPDATE
                  SET info = '{license_data}' 
                  WHERE server_info_id = '{id}'
                  """.format(**server_dict)
            db.pmdatabase.execute(query)
