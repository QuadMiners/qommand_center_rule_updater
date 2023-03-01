
from command_center.protocol import rule_update_service_pb2_grpc
from command_center.protocol.license.license_pb2 import License, LicenseListResponse
from command_center.protocol.site import server_pb2, site_pb2
from command_center import RequestCheckMixin, ServerType
import command_center.library.database as db
from command_center.library.AppConfig import gconfig
from command_center.protocol.site.site_pb2 import Site


class QmcSiteService(RequestCheckMixin, rule_update_service_pb2_grpc.SiteServiceServicer):

    # 사이트에 대한 정보를 전부 가져온다. Site , Server 정보 모두
    def GetSite(self, request, context):
        sites = self._get_site(request.server)
        """
            Site 정보 모두 업데이트 내려줬다고 체크.
        """
        for site in sites:
            query = """UPDATE site SET update_server_status = false WHERE code= '{0}'
                """.format(site.code)
            db.pmdatabase.execute(query)

        return site_pb2.SiteResponse(sites=sites)

    def GetSiteLicense(self, request, context):
        print(request)
        licenses = self._get_license(request)
        return LicenseListResponse(licenses=licenses)

    def GetServer(self,request, context):
        return self._get_server(request)

    def GetServerLicense(self, request, context):
        licenses = self._get_license(request)
        return LicenseListResponse(licenses=licenses)



    def UpdateServer(self, request,context):
        request_server = request.server

        id = request_server.id
        name = request_server.name
        server_type = request_server.server_type
        version = request_server.version
        host_name = request_server.host_name
        ipaddr = request_server.ipaddr

        query = """UPDATE site_server_info 
                        SET name = '{name}', 
                        type = '{server_type}', 
                        version = '{version}', 
                        hostname = '{host_name}', 
                        ipaddr = '{ipaddr}'
                        WHERE hardware_uuid = {hardware_uuid};
                """
        db.pmdatabase.execute(query)

        return
    def _get_license(self, request):
        server_type = request.server_type
        site_code = request.site_code
        licenses = []
        if server_type == ServerType.RELAY:
            """
               update_server_status = true 변경이 일어난 서버만  
            """
            query = """ SELECT license.name, license.type, license.version, license.start_date, license.end_date, license.expire, license.uuid, license.raw, server.hardware_uuid, server.machine_id, server.server_id
                    FROM site_server_license as license
                    JOIN site_server_info as server 
                    ON license.server_info_id = server.id 
                    WHERE server.site_id in ( SELECT site_id FROM relay_server_sites 
                                                                WHERE relayserver_id IN ( SELECT id FROM relay_server 
                                                                                        WHERE site_code = '{0}'
                                                                                        )
                                             )
                    AND update_server_status = true
            """.format(site_code)

        else:
            query = """ 
             SELECT license.name, license.type, license.version, license.start_date, license.end_date, license.expire, license.uuid, license.raw, server.hardware_uuid, server.machine_id, server.server_id
                    FROM site_server_license as license
                    JOIN site_server_info as server 
                    ON license.server_info_id = server.id 
                    WHERE server.site_id in (SELECT id FROM site WHERE code = '{0}') 
            """.format(site_code)

        print(query)
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            rows = pcursor.fetchall()
            for row in rows:
                licenses.append(License(name=row[0], type=row[1], version=row[2], start_date=str(row[3]),
                                         end_date=str(row[4]), expire=row[5], uuid=str(row[6]),
                                         raw=row[7], hardware_uuid=row[8],machine_id=row[9], server_id=row[10]))
        return licenses

    def _get_site(self, request):
        server_type = request.server_type
        site_code = request.site_code

        sites = []
        if server_type == ServerType.RELAY:
            """
               update_server_status = true 변경이 일어난 서버만  
            """
            query = """ SELECT  name, code, address , tel , "desc" , partner_info , distributor, engineer , sales , notification_settings 
                    FROM site WHERE id IN ( SELECT site_id 
                                            FROM relay_server_sites 
                                            WHERE relayserver_id IN ( SELECT id FROM relay_server WHERE site_code = '{0}')
                                        )
                        AND update_server_status = true
            """.format(site_code)
            print(query)
            with db.pmdatabase.get_cursor() as pcursor:
                pcursor.execute(query)
                rows = pcursor.fetchall()
                for row in rows:
                    servers = self._get_all_servers(row[1])
                    sites.append(Site(name=row[0], code=row[1], address=row[2], tel=row[3], desc=row[4], partner_info=row[5], distributor=row[6], engineer=row[7], sales=row[8], notification_settings=str(row[9]), servers=servers))
        else:
            query = """ SELECT  name, code, address , tel , "desc" , partner_info , distributor, engineer , sales , notification_settings FROM site WHERE code = '{0}' """.format(site_code)
            with db.pmdatabase.get_cursor() as pcursor:
                pcursor.execute(query)
                name, code, address, tel, desc, partner_info, distributor, engineer, sales, notification_settings, = pcursor.fetchone()
                servers = self._get_all_servers(code)
                sites.append(Site(name=name, code=code, address=address, tel=tel, desc=desc, partner_info=partner_info, distributor=distributor, engineer=engineer, sales=sales, notification_settings=str(notification_settings), servers=servers))
        return sites
    def _get_all_servers(self, site_code):

        servers_info = list()

        #info license_data
        query = """
                SELECT server_id, name, type, version, hostname, ipaddr, os_ver, hardware_uuid, machine_id
                FROM site_server_info  as server
                WHERE site_id in ( SELECT id FROM site WHERE code = '{site_code}' )
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
                                               hostname=row[4],
                                               ipaddr=row[5],
                                               os_ver=row[6],
                                               hardware_id=row[7],
                                               machine_id=row[8]
                                               )
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
