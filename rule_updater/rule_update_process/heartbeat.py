import logging
import os
import time

import grpc
from quadlibrary import schedule
from quadlibrary.AppInterface import SchedulerThreadInterface

from protocol import rule_update_service_pb2_grpc
from rule_updater.env import get_env_int, get_env_str
from rule_updater.gRPC.client import QmsUpdateClient

logger = logging.getLogger(__name__)


class HeartBeatProcess(SchedulerThreadInterface):

    def __init__(self, p_time: int):
        super().__init__()
        self.time_period = p_time

    def heartbeat(self):
        try:
            """
                자신의 서버정보를 데이터베이스에서 읽어와서 
                grpc로 하트비트 날리는 반복작업 코드 작성 필요.
            """
            channel = grpc.insecure_channel("127.0.0.1:50051",
                                            options=[('grpc.max_receive_message_length',
                                                      get_env_str('MAX_MESSAGE_LENGTH'))])
            send_packet_stub = rule_update_service_pb2_grpc.HeartbeatServiceStub(channel)
            client = QmsUpdateClient()
            result = client.do_heartbeat(send_packet_stub)

            """
            result 값 db에 저장.
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



