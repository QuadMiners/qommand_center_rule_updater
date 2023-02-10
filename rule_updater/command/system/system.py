import curses
import socket

from quadlibrary.command import ToolCommandMixin
from termcolor import colored, cprint

hostname = socket.gethostname()



def monitor_top(cmd_str, l_filter):
    try:
        print("Hello")
    except (KeyboardInterrupt, SystemExit):
        pass

def monitor_disk_io(cmd_str, l_filter):
    print("Monitor disk")


class SystemManager(ToolCommandMixin):
    intro = colored('System shell.\nType help or ? to list commands.\n', 'yellow')
    prompt = colored('%s (system)# ' % hostname, 'cyan')

    def help_monitor(self):
        cprint("Monitor Proces", "green")

    def do_system(self, args):
        print("hello")

    def do_monitor(self, args):
        cmd_str, cmd_len, l_filter = self.cmd_parse(args)
        if cmd_len > 0:
            try:
                if cmd_str[0] == 'disk':
                    self.monitor_disk_io(cmd_str, l_filter)

                elif cmd_str[0] == 'top':
                    self.monitor_top(cmd_str, l_filter)
            except Exception as b:
                pass
        else:
            self.help_monitor()
