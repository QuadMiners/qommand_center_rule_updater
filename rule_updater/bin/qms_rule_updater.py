import os
import logging

import quadlibrary.AppDefine as app_define
from quadlibrary.AppDaemon import Daemon
from quadlibrary.database import DatabasePoolMixin

from rule_updater.env import get_env_int
from rule_updater.process.heartbeat import RuleUpdateHeartBeatProcess
from rule_updater.process.version_check import RuleUpdateVersionCheckProcess

logger = logging.getLogger(__name__)


class RuleUpdateApplication(Daemon,DatabasePoolMixin):

    heartbeat = None
    version_check = None

    def __init__(self, pid):
        Daemon.__init__(self, pid)

    def run(self, *args, **kwargs):
        logger.info("--- Rule Update Application Start---")
        self.dbconnect()
        app_define.APP_DEBUG = self.debug_mode

        self._start_daemon("Rule Update Daemon Start PID [{0}]".format(os.getpid()))

        self.heartbeat = RuleUpdateHeartBeatProcess(get_env_int('HEARTBEAT_TIME'))
        self.version_check = RuleUpdateVersionCheckProcess(get_env_int('VERSION_CHECK_TIME'))

        while self.daemon_alive:
            pass

        logger.info("--- Rule Update Application Stop ---")


def main():
    pass


if __name__ == '__main__':
    main()