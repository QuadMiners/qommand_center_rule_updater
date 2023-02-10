import logging
import os
import time

from quadlibrary import schedule
from quadlibrary.AppInterface import SchedulerThreadInterface

logger = logging.getLogger(__name__)


class RuleUpdateHeartBeatProcess(SchedulerThreadInterface):

    def __init__(self, p_time: int):
        super().__init__()
        self.time_period = p_time

    def heartbeat(self):
        try:
            """
                자신의 서버정보를 데이터베이스에서 읽어와서 
                grpc로 하트비트 날리는 반복작업 코드 작성 필요.
            """
            pass
        except Exception as k:
            logger.error("Heartbeat Schedule Exception: {0}".format(k))

    def process(self, data):
        pass

    def run(self):
        self.scheduler.every(self.time_period).seconds.do(self.heartbeat)

        while self._exit is False:
            self.scheduler.run_pending()
            time.sleep(1)



