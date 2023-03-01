import grpc
import contextlib
import logging

from command_center.library.database import DBException

import command_center.library.database as db
from command_center.library.AppConfig import gconfig
from command_center.protocol.site.server_pb2 import ServerType

logger = logging.getLogger(__name__)


class RequestCheckMixin():
    def request_check(self, request):
        cnt = 0
        if request.server_type == ServerType.RELAY:
            query = """
                    SELECT count(*) FROM relay_server
                    WHERE site_code = '{site_code}' AND hardware_uuid = '{hardware_uuid}'
                    """.format(**dict(site_code=request.site_code, hardware_uuid=request.hardware_uuid))
        elif request.server_type == ServerType.NBB:
            query = """
                    SELECT count(*) FROM site_server_license
                    WHERE server_info_id in ( SELECT id FROM site_server_info WHERE site_id in ( SELECT id FROM site WHERE site_code = '{site_code}' and hardware_uuid = '{server_uuid}' ))
                    """.format(**dict(site_code=request.site_code, hardware_uuid=request.hardware_uuid))

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            cnt, = pcursor.fetchone()
        return cnt
    def update_heatbeat_status(self, request):
        if request.server_type == ServerType.RELAY:
            query = """
                    UPDATE relay_server SET last_heartbeat = now() WHERE site_code = '{site_code}' AND hardware_uuid = '{hardware_uuid}'
                    """.format(**dict(site_code=request.site_code, hardware_uuid=request.hardware_uuid))
        elif request.server_type == ServerType.NBB:
            pass

