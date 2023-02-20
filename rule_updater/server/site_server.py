from library.database.fquery import fetchall_query_to_dict, fetchall_query, fetchone_query_to_dict
from protocol import rule_update_service_pb2_grpc
from protocol.site import site_pb2, server_pb2
from rule_updater import RequestCheckMixin


class QmcSiteService(RequestCheckMixin, rule_update_service_pb2_grpc.SiteServiceServicer):

    # 사이트에 대한 정보를 전부 가져온다. Site , Server 정보 모두
    def GetSite(self, request, context):

        request_server = request.server
        site_id = request_server.site_id
        license_uuid = request_server.license_uuid

        response = site_pb2.SiteResponse()

        query = f"SELECT * FROM site_info WHERE site_id = '{site_id}' AND license_uuid = '{license_uuid}'"
        result_dict = fetchone_query_to_dict(query)
        site = site_pb2.Site(name=result_dict["type"],
                             address=result_dict["version"],
                             tel=result_dict["tel"],
                             desc=result_dict["desc"],
                             engineer=result_dict["engineer"],
                             sales=result_dict["sales"])
        response.site = site

        query = f"SELECT * FROM server_info WHERE site_id = '{site_id}' AND license_uuid = '{license_uuid}'"
        result_dict = fetchall_query_to_dict(query)
        for i in range(len(result_dict)):
            server = server_pb2.Server( id=result_dict[i]["id"],
                                        name=result_dict[i]["name"],
                                        server_type=result_dict[i]["server_type"],
                                        version=result_dict[i]["version"],
                                        host_name=result_dict[i]["host_name"],
                                        ipaddr=result_dict[i]["ipaddr"],
                                        license_data=result_dict[i]["license_data"])
            response.servers.append(server)

        return response

    # 서버정보 1대 가져온다
    def GetServer(self,request, context):
        request_server = request.server
        site_id = request_server.site_id
        license_uuid = request_server.license_uuid

        query = f"SELECT * FROM server_info WHERE site_id = '{site_id}' AND license_uuid = '{license_uuid}'"
        result_dict = fetchone_query_to_dict(query)
        server = server_pb2.Server(id=result_dict["id"],
                                   name=result_dict["name"],
                                   server_type=result_dict["server_type"],
                                   version=result_dict["version"],
                                   host_name=result_dict["host_name"],
                                   ipaddr=result_dict["ipaddr"],
                                   license_data=result_dict["license_data"])
        response = server_pb2.ServerResponse()
        response.server = server

        return response

    # 서버정보가 업데이트되면 License 에 일부 정보를 업데이트 한다.
    """ 리퀘스트 정보
    message Server{
      int64 id = 1;
      string name = 2;
      string server_type = 3;
      string version = 4;
      string host_name= 5;
      string ipaddr = 6;
    
      string license_data = 7; /* base64 encoded string */
    }
    """
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
                SET name = '{name}', server_type = '{server_type}', version = '{version}',
                host_name = '{host_name}', ipaddr = '{ipaddr}', 
                license_data = decode('{license_data}', 'base64')
                WHERE id = {id};
                """

        result = fetchall_query(query)

        return None
