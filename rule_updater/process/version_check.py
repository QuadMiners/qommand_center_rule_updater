import logging
import os
import time

from dotenv import load_dotenv
from quadlibrary import schedule
from quadlibrary.AppInterface import SchedulerThreadInterface

logger = logging.getLogger(__name__)
load_dotenv()


class RuleUpdateVersionCheckProcess(SchedulerThreadInterface):

    def __init__(self, p_time: int):
        super().__init__()
        self.time_period = p_time

    def version_check(self):
        try:
            """
                자신의 서버 Version정보를 데이터베이스에서 읽어와서 
                grpc로 Check Packet 날리는 반복작업 코드 작성 필요.
            """
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

