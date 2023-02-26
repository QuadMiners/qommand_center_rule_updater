import time

from command_center.library.AppInterface import SchedulerThreadInterface
from command_center import ChannelMixin


class NBBUpdateClient(ChannelMixin, SchedulerThreadInterface):
    def heartbeat_reg(self):
        self.scheduler.every(self.time_period).seconds.do(self.heartbeat)

    def run(self):
        self.heartbeat_reg()

        while self._exit is False:
            self.scheduler.run_pending()
            time.sleep(1)


