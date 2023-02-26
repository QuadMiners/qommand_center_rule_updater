#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from command_center.library.AppConfig import gconfig

from command_center.system.raid.mega_raid import MegaRaidManager
from command_center.system.raid.hp_server import HPRaidManager

logger = logging.getLogger(__name__)


class HardwareManager(object):
    """
        hierarchy 에서 정보 1시간에 1번씩 정보 업데이트 시켜줌.
    """
    is_dell = False
    is_hp = False

    def set_raid_type(self):
        manufacturer = gconfig.server_model['manufacturer'].strip()
        if manufacturer in ('Dell Inc.', 'Dell'):
            self.is_dell = True
        elif manufacturer in ('HP', 'HPE'):
            self.is_hp = True
        else:
            self.is_dell = True

    def raid_status_schedule(self):
        try:
            if self.is_hp:
                HPRaidManager()
            else:
                MegaRaidManager()
        except Exception as e:
            logger.error("Raid Card Management Exception : {0}".format(e))

    def hardware_check(self):
        logging.info("Raid Status Run Start")
        try:
            self.set_raid_type()
            self.raid_status_schedule()
        except Exception as e:
            logger.error("Hardware Check Exception : {0}".format(e))
        logging.info("Raid Status Run Close")
