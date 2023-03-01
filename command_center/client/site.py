import logging

from command_center.client import ClientRequestMixin
from command_center.library.rpc.convertor import protobuf_to_dict
from command_center.library.rpc.retry import retrying_stub_methods
from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.heartbeat.heartbeat_pb2 import DataUpdateFlag
from command_center.protocol.site import site_pb2
import command_center.library.database as db

logger = logging.getLogger(__name__)


class SiteClientMixin(ClientRequestMixin):

    """
        client가 서버에게 사이트, 서버 정보를 요청하는 함수.
    """
    def GetSite(self):
        """
            전체 사이트 정보 가저와서 업데이트
        """
        with self.get_command_center_channel() as channel:
            stub = rule_update_service_pb2_grpc.SiteServiceStub(channel)
            retrying_stub_methods(stub)

            """
                서버에게 요청 response_data에 값 받아옴
            """
            request_server = self.get_request_server()
            response_data = stub.GetSite(site_pb2.SiteRequest(server=request_server), timeout=10)

            print(response_data.sites)

            """
                받아온 사이트 데이터 파싱, 업데이트
            """
            self._update_site(response_data.sites)

    def GetSiteLicense(self):
        with self.get_command_center_channel() as channel:
            stub = rule_update_service_pb2_grpc.SiteServiceStub(channel)
            retrying_stub_methods(stub)

            """ 서버에게 요청 response_data에 값 받아옴 """
            request_server = self.get_request_server()

            response_data = stub.GetSiteLicense(request_server, timeout=10)
            print(response_data)

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

    def _update_site(self, sites):
        for site in sites:
            site_dict = protobuf_to_dict(site)
            print(site_dict)
            query = """
            INSERT INTO site (name, address, tel, "desc",partner_info,distributor,engineer,sales,update_server_status,notification_settings, delete,code,created_user_id)
            VALUES ('{name}','{address}','{tel}', '{desc}','{partner_info}', '{distributor}', '{engineer}', '{sales}', false, '{{}}', false, '{code}', 1)
            ON CONFLICT (code)
             DO UPDATE SET
                name= excluded.name,
                address= excluded.address,
                tel = excluded.tel,
                "desc" = excluded.desc,
                engineer = excluded.engineer
                    """.format(**site_dict)
            print(query)
            db.pmdatabase.execute(query)
            print(query)
            """
                받아온 서버 데이터 파싱, 업데이트
            """
            self._update_server(site.code, site.servers)

    def _update_server(self,site_code, servers_info):
        for server in servers_info:
            server_dict = protobuf_to_dict(server)
            server_dict.update(dict(site_code=site_code))
            query = """
                    INSERT INTO site_server_info (site_id,server_id, name, type, version, hostname, ipaddr, hardware_uuid, machine_id, os_ver) 
                    VALUES((select id from site FROM code='{site_code}'),'{id}', '{name}', '{server_type}', '{version}', '{host_name}', '{ipaddr}', '{hardware_uuid}', '{machine_id}', '{os_ver}') 
                    ON CONFLICT (hardware_uuid, machine_id, site_id) DO UPDATE 
                    SET server_id =excluded.server_id,
                        name = excluded.name,
                        type = excluded.type,
                        os_ver = excluded.os_ver
                    RETURNING id
                    """.format(**server_dict)
            sid = db.pmdatabase.execute(query, returning_id=True)
