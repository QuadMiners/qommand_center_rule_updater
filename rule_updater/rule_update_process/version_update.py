import logging
import time

from quadlibrary import schedule
from quadlibrary.AppInterface import SchedulerThreadInterface

logger = logging.getLogger(__name__)


class VersionUpdateProcess(SchedulerThreadInterface):

    def __init__(self, p_time: int):
        super().__init__()
        self.time_period = p_time

    def version_update(self):
        try:

            # if download...
            # - download
            # - parsing & merged
            # - create file

            pass
        except Exception as k:
            logger.error("Heartbeat Schedule Exception: {0}".format(k))

    def process(self, data):
        pass

    def run(self):
        self.scheduler.every(self.time_period).seconds.do(self.version_check)

        while self._exit is False:
            self.scheduler.run_pending()
            time.sleep(1)


