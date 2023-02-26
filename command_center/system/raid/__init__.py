#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import os
import time

from command_center.library.AppInterface import SchedulerThreadInterface

from command_center.system.raid.dell_server import DellManager
from command_center.system.raid.mega_raid import MegaRaidManager
from command_center.system.raid.hp_server import HPRaidManager

logger = logging.getLogger(__name__)


class RaidManager(SchedulerThreadInterface):
    is_dell = False
    is_hp = False
    is_other = False

    def set_raid_type(self):
        if os.path.exists('/opt/MegaRAID/perccli/perccli64'):
            self.is_dell = True
        elif os.path.exists('/usr/sbin/ssacli'):
            self.is_hp = True
        else:
            self.is_other = True

    def raid_status_schedule(self):
        if self.is_hp:
            HPRaidManager()
            self.scheduler.every().hours.do(HPRaidManager)
        elif self.is_dell:
            DellManager()
            self.scheduler.every().hours.do(DellManager)
        else:
            MegaRaidManager()
            self.scheduler.every().hours.do(MegaRaidManager)

    def run(self):
        self.set_raid_type()
        self.raid_status_schedule()
        logging.info("Raid Status Run Start")
        while self._exit is False:
            self.run_queue()
            self.scheduler.run_pending()
            time.sleep(1)
        logging.info("Raid Status Run Close")

    def process(self, data):
        pass