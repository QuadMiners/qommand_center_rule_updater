import logging
import time

from rule_updater import ResponseRequestMixin

logger = logging.getLogger(__name__)


class SiteClinetMixin(ResponseRequestMixin):

    def GetSite(self):
        try:

            # if download...
            # - download
            # - parsing & merged
            # - create file

            pass
        except Exception as k:
            logger.error("Heartbeat Schedule Exception: {0}".format(k))

    def GetServer(self, data):
        pass

    def UpdateServer(self):
        self.scheduler.every(self.time_period).seconds.do(self.version_check)

        while self._exit is False:
            self.scheduler.run_pending()
            time.sleep(1)


