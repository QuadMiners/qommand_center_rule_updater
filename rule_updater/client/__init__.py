import time

from quadlibrary.AppInterface import SchedulerThreadInterface
from rule_updater import ChannelMixin


class UpdateClient(ChannelMixin, SchedulerThreadInterface):
    def heartbeat_reg(self):
        self.scheduler.every(self.time_period).seconds.do(self.heartbeat)

    def run(self):
        self.heartbeat_reg()

        while self._exit is False:
            self.scheduler.run_pending()
            time.sleep(1)


