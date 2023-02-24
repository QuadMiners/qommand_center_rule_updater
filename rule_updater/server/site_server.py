from library.database.fquery import fetchall_query
from protocol import rule_update_service_pb2_grpc
from protocol.site import site_pb2, server_pb2
from rule_updater import RequestCheckMixin

import library.database as db

class QmcSiteService(RequestCheckMixin, rule_update_service_pb2_grpc.SiteServiceServicer):


    def _get_site(self, site_id):

        site_info = None
        print("100")
        query = """
                SELECT name, address, tel, desc, engineer, sales 
                FROM site 
                WHERE site_id = '{site_id}'
                """.format(**dict(site_id=site_id))
        print("200")
        with db.pmdatabase.get_cursor(query) as pcursor:
            pcursor.execute(query)
            row = pcursor.fetchone()
            if pcursor.rowcount > 0:
                site_info = site_pb2.Site(name=row[0],
                                        address=row[1],
                                        tel=row[2],
                                        desc=row[3],
                                        engineer=row[4],
                                        sales=row[5])
        print("300")
        return site_info

    def _get_servers(self, site_id, license_uuid):

        servers_info = None

        query = """
                SELECT id, name, server_type, version, host_name, ipaddr, license_data
                FROM server_info 
                WHERE site_id = '{site_id}'
                """.format(**dict(site_id=site_id))
        with db.pmdatabase.get_cursor(query) as pcursor:
            pcursor.execute(query)
            rows = pcursor.fetchall()
            if pcursor.rowcount > 0:
                for row in rows:
                    server = server_pb2.Server(id=row[0],
                                               name=row[1],
                                               server_type=row[2],
                                               version=row[3],
                                               host_name=row[4],
                                               ipaddr=row[5],
                                               license_data=[row[6]])
                    servers_info.append(server)

        return servers_info

    # 사이트에 대한 정보를 전부 가져온다. Site , Server 정보 모두
    def GetSite(self, request, context):

        print(request)
        print("1")

        site_info = self._get_site(request.server.site_id)
        print(site_info)
        print("2")
        servers_info = self._get_servers(request.server.site_id, request.server.license_uuid)
        print(servers_info)
        print("3")

        return site_pb2.SiteResponse(site = site_info, servers = servers_info)

    # 서버정보 1대 가져온다
    def _get_server(self, site_id, license_uuid):

        server = None

        query = """
                SELECT id, name, server_type, version, host_name, ipaddr, license_data
                FROM server_info 
                WHERE site_id = '{site_id}' 
                AND id = (SELECT server_info_id 
                            FROM license 
                            WHERE license_uuid = '{license_uuid}'
                """.format(**dict(site_id=site_id, license_uuid=license_uuid))
        with db.pmdatabase.get_cursor(query) as pcursor:
            pcursor.execute(query)
            row = pcursor.fetchone()
            if pcursor.rowcount > 0:
                server = server_pb2.Server(id=row[0],
                                           name=row[1],
                                           server_type=row[2],
                                           version=row[3],
                                           host_name=row[4],
                                           ipaddr=row[5],
                                           license_data=row[6])
        return server

    def GetServer(self,request, context):

        response = self._get_server(request.server.site_id, request.server.license_uuid)
        return response


    def UpdateServer(self, request,context):
        request_server = request.server
        id = request_server.id
        name = request_server.name
        server_type = request_server.server_type
        version = request_server.version
        host_name = request_server.host_name
        ipaddr = request_server.ipaddr
        license_data = request_server.license_data

        query = f"""UPDATE server_info
                SET name = '{name}', 
                type = '{server_type}', 
                version = '{version}', 
                hostname = '{host_name}', 
                ipaddr = '{ipaddr}', 
                license_data = decode('{license_data}', 'base64')
                WHERE id = {id};
                """

        result = fetchall_query(query)
        if result is None or 0:
            return None
        else:
            return None

        """
            Site 정보 모두 업데이트 내려줬다고 체크.
        """
        query = f"UPDATE black.site " \
                f"SET update_server_status = True " \
                f"WHERE site_id = '{site_id}'"
        fetchall_query(query)
