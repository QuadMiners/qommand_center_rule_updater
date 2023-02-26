from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.site import server_pb2
from command_center import RequestCheckMixin
import command_center.library.database as db


class QmcSiteService(RequestCheckMixin, rule_update_service_pb2_grpc.SiteServiceServicer):

    # 사이트에 대한 정보를 전부 가져온다. Site , Server 정보 모두
    def GetSite(self, request, context):

        print("request", request)
        site_info = self._get_site(request.server.site_code)
        site_info = site_pb2.Site(name=row[0],
                                  address=row[1],
                                  tel=row[2],
                                  desc=row[3],
                                  engineer=row[4],
                                  sales=row[5])

        print(site_info)

        servers_info = self._get_all_servers(request.server.site_id)
        print(servers_info)

        return site_pb2.SiteResponse(site = site_info, servers = servers_info)

    def GetServer(self,request, context):
        return self._get_server(request)

    def UpdateServer(self, request,context):
        request_server = request.server
        id = request_server.id
        name = request_server.name
        server_type = request_server.server_type
        version = request_server.version
        host_name = request_server.host_name
        ipaddr = request_server.ipaddr
        license_data = request_server.license_data

        query = f"""UPDATE site_server_info
                SET name = '{name}', 
                type = '{server_type}', 
                version = '{version}', 
                hostname = '{host_name}', 
                ipaddr = '{ipaddr}', 
                license_data = decode('{license_data}', 'base64')
                WHERE id = {id};
                """

        if result is None or 0:
            return None
        else:
            return None

        """
            Site 정보 모두 업데이트 내려줬다고 체크.
        """
        query = f"UPDATE site " \
                f"SET update_server_status = True " \
                f"WHERE site_id = '{site_id}'"

    def _get_all_servers(self, site_code):

        servers_info = list()

        #info license_data
        query = """
                SELECT server_info.id, name, type, version, hostname, ipaddr, info
                FROM site_server_info  as server
                JOIN site_server_license  as license
                ON server.id = license.server_info_id 
                WHERE server.site_id in ( SELECT id FROM site WHERE site_code = '{site_code}' )
                """.format(**dict(site_code=site_code))
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            rows = pcursor.fetchall()
            print(rows)
            if pcursor.rowcount > 0:
                for row in rows:
                    server = server_pb2.Server(id=row[0],
                                               name=row[1],
                                               server_type=row[2],
                                               version=row[3],
                                               host_name=row[4],
                                               ipaddr=row[5],
                                               license_data=str([row[6]]))
                    servers_info.append(server)

        return servers_info

    # 서버정보 1대 가져온다
    def _get_server(self, site_code, server_id):

        servers = list()
        where = ""

        if server_id == 0:
            where = f" AND server_id = {server_id}"

        query = """
                SELECT server_id, name, server_type, version, host_name, ipaddr
                FROM site_server_info 
                WHERE site_id in ( SELECT id FROM site WHERE site_code = '{site_code}' )
                {where}
                """.format(**dict(site_code=site_code, where=where))

        with db.pmdatabase.get_cursor(query) as pcursor:
            pcursor.execute(query)
            row = pcursor.fetchone()
            if pcursor.rowcount > 0:
                servers.append(server_pb2.Server(id=row[0],
                                           name=row[1],
                                           server_type=row[2],
                                           version=row[3],
                                           host_name=row[4],
                                           ipaddr=row[5]))
        return servers
