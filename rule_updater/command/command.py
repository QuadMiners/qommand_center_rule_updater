import os
import signal
import socket
import subprocess
import time
from optparse import OptionParser

from quadlibrary.database import DBException
from termcolor import cprint, colored
from quadlibrary.command import ToolCommandMixin

from rule_updater.command.system.system import SystemManager

hostname = socket.gethostname()


class LogoutException(Exception):
    pass


class QMSCommand(ToolCommandMixin):
    intro = colored('Welcome to the NetworkBlackBox Shell.\nType help or ? to list commands.\n', 'yellow')
    prompt = colored('%s > ' % hostname, 'cyan')
    hidden_methods = ['do_enable']

    def __init__(self, completekey='tab', stdin=None, stdout=None):
        super(QMSCommand, self).__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        try:
            import quadlibrary.database as db
            # db.global_db_connect(contents=False)
        except DBException:
            cprint("Database Connection Error", color='red')
            cprint("\n changes to database connection ipaddress", color='red')
            cprint("> config\n (config)# managerserver {ipaddress}", color='yellow')

    def do_system(self, arg):
        """
            QMS System Command
        """
        try:
            from rule_updater.command.system import system
            SystemManager().cmdloop()
        except KeyboardInterrupt:
            pass

    def do_logout(self, *args):
        raise LogoutException


def main(app_define=None):
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
    while 1:  # mode != CommandMode.SHELL:
        try:
            expot = QMSCommand()
            expot.cmdloop(intro="""

            QMS Command

            """)
        except LogoutException:
            break
        except KeyboardInterrupt:
            exit(0)
            break
        # except Exception as e:
        #     logger.error('NetworkBlackbox Command Error | {0}'.format(e))
        #     cprint('NetworkBlackbox Command Error | {0}'.format(str(e)), 'red')

    if not options.debug:  # and mode != CommandMode.SHELL:
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
