#!/usr/bin/env python
# -*- coding: utf-8 -*-
import getpass
import socket
import enum
import logging
import os
import signal
import subprocess
import time
from optparse import OptionParser
import command_center.library.AppDefine as app_define
from command_center.command.data import SyncDataMixin

from command_center.library.AppLibrary import pm_logging

from termcolor import cprint, colored

from command_center import DBException
from command_center.command import ToolCommandMixin, print_help_msg

pm_logging("command")

logger = logging.getLogger(__name__)


class CommandMode(enum.Enum):
    ADMIN = 1
    USER = 2
    SHELL = 3


mode = CommandMode.USER
hostname = socket.gethostname()


class LogoutException(Exception):
    pass


class NetworkBlackBoxCommand(SyncDataMixin, ToolCommandMixin):
    intro = colored('Welcome to the NetworkBlackBox Shell.\nType help or ? to list commands.\n', 'yellow')
    prompt = colored('%s > ' % hostname, 'cyan')
    hidden_methods = ['do_enable']

    def __init__(self, completekey='tab', stdin=None, stdout=None):
        super(NetworkBlackBoxCommand, self).__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        try:
            import command_center.library.database as db
            db.global_db_connect()
        except DBException:
            cprint("Database Connection Error", color='red')
            cprint("\n changes to database connection ipaddress", color='red')
            cprint("> config\n (config)# managerserver {ipaddress}", color='yellow')

    def help_license(self):
        print_help_msg("Enter RelayServer License Shell",
                       usage=["license"])

    def do_license(self, arg):
        from command_center.command.license.license import LicenseCommand
        LicenseCommand().cmdloop()

    def help_sync_data(self):
        print_help_msg("Data Sync ",
                       usage=["sync_data  snort"])

    def complete_sync_data(self, text, line, begidx, endidx):
        params = ["snort", ]
        line_split = line.split(' ')

        if len(line_split[1].strip()) > 0:
            return [s for s in params if s.startswith(line_split[1])]
        return params

    def do_sync_data(self,args):
        cmd_str, cmd_len, l_filter = self.cmd_parse(args)
        if cmd_len > 0:
            if cmd_str[0] == 'snort':
                self.data_snort()
        else:
            self.help_sync_data()


    def do_system(self, arg):
        """
            NetworkBlackbox System Command
        """
        try:
            from command_center.command.system import NBBSystemManager
            NBBSystemManager().cmdloop()
        except KeyboardInterrupt:
            pass

    def help_exit(self):
        """
        """
        cprint("Exit")

    def do_exit(self, *args):
        return True

    def help_logout(self):
        print_help_msg("Logout from nbb_command",
                       usage=["logout"])

    def do_logout(self, *args):
        raise LogoutException

    def help_nbb(self):
        print_help_msg("Enter NetworkBlackbox Service Managerment Shell",
                       usage=["nbb"])

def main():
    usage = """usage:  """
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--debug", dest="debug", action="store_true", help="디버깅 옵션 정보 ", default=False)
    parser.add_option("-v", "--version", dest="version", action="store_true", help="Version 정보", default=False)
    (options, args) = parser.parse_args()

    if options.debug:
        app_define.APP_DEBUG = True

    """
        DB가 접속 안되면 Manager.conf 파일에 psql IP 정보를 업데이트해야됨. 
    """
    while mode != CommandMode.SHELL:
        try:
            expot = NetworkBlackBoxCommand()
            expot.cmdloop(intro="""
          _  _ ___ _______      _____  ___ _  __  ___ _      _   ___ _  _____  _____  __
         | \| | __|_   _\ \    / / _ \| _ | |/ / | _ | |    /_\ / __| |/ | _ )/ _ \ \/ /
         | .` | _|  | |  \ \/\/ | (_) |   | ' <  | _ | |__ / _ | (__| ' <| _ | (_) >  < 
         |_|\_|___| |_|   \_/\_/ \___/|_|_|_|\_\ |___|____/_/ \_\___|_|\_|___/\___/_/\_\\

            """)
        except LogoutException:
            break
        except KeyboardInterrupt:
            exit(0)
            break
        # except Exception as e:
        #     cprint('Error Occurred!\nRestart nbb_command', 'red')

        # except Exception as e:
        #     logger.error('NetworkBlackbox Command Error | {0}'.format(e))
        #     cprint('NetworkBlackbox Command Error | {0}'.format(str(e)), 'red')

    if not options.debug and mode != CommandMode.SHELL:
        """
            Shell 모드가 아니면 Logout
        """

        def runcmd(*args):
            cmd = subprocess.Popen(args, stdout=subprocess.PIPE, universal_newlines=True)
            return cmd.communicate()[0]

        tty = runcmd('tty').strip()
        for line in runcmd('ps', '-o', 'pid,sess', '-t', tty).split('\n'):
            if line:
                pid, sess = line.split()
                if pid == sess:
                    os.kill(int(pid), signal.SIGHUP)
                    time.sleep(5.0)
                    os.kill(int(pid), signal.SIGKILL)
        # Logout 기능
        # db.pmdatabase.execute(""" INSERT INTO """)


if __name__ == '__main__':
    main()
