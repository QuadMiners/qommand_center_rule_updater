import logging
import time

from command_center import ResponseRequestMixin

logger = logging.getLogger(__name__)


class NBBSiteMixin(ResponseRequestMixin):

    def GetSite(self):
        try:
            pass
        except Exception as k:
            logger.error("Heartbeat Schedule Exception: {0}".format(k))

    def GetServer(self, data):
        pass

    def UpdateServer(self):
        query = """
            SELECT id , name, server FROM site_server_info 
            """
