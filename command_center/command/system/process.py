import collections
import curses
import os
import time
import socket

from psutil._compat import get_terminal_size
from command_center.command.command import hostname

import psutil
from termcolor import cprint

from command_center.command import NBBScreenMixin, cmd_parse, print_help_msg, ValueInput


class NBBProcessMixin(object):
    def monitor_distribution(self, cmd_str, l_filter):
        class ProcessDistributionScreen(NBBScreenMixin):
            cpus_hidden = True
            display_cnt = 10  # try to fit into screen
            cpu_cnt = psutil.cpu_count()
            current_cpu = 0

            def datas(self,interval):
                time.sleep(1)
                # processes
                procs = collections.defaultdict(list)
                for p in psutil.process_iter(['name', 'cpu_num']):
                    procs[p.info['cpu_num']].append(p.info['name'])
                return (procs,)

            def refresh_window(self, procs):
                if self.key == 'n':
                    if self.cpu_cnt > 10:
                        self.current_cpu += 10
                        if self.cpu_cnt == (self.current_cpu - 10):
                            self.current_cpu = 0
                        elif self.cpu_cnt <= self.current_cpu:
                            self.current_cpu = self.current_cpu - 10 + (self.cpu_cnt % 10)
                elif self.key == 'b':
                    if self.current_cpu >= 10:
                        self.current_cpu -= 10

                cpus_percent = psutil.cpu_percent(percpu=True)
                line_width = int(self.width / (self.display_cnt + 2))
                for i in range(self.display_cnt):
                    if self.cpu_cnt > (i + self.current_cpu):
                        line = "CPU %-6i" % (i + self.current_cpu)
                        self.stdscr.addstr(self.lineno, line_width + (i*line_width), line, 0)

                self.lineno +=1
                empty_line = " " * self.width
                self.stdscr.addstr(self.lineno, 0, empty_line, curses.A_REVERSE)
                self.lineno +=1
                for i in range(self.display_cnt + self.current_cpu):
                    if i >= self.cpu_cnt:
                        break

                    line = "%-10s" % cpus_percent.pop(0)
                    if i >= self.current_cpu:
                        self.stdscr.addstr(self.lineno, line_width + ((i-self.current_cpu)*line_width), line, 0)

                self.lineno += 1
                self.stdscr.addstr(self.lineno, 0, empty_line, curses.A_REVERSE)
                self.lineno += 1

                while True:
                    for num in range(self.display_cnt + self.current_cpu):
                        if num >= self.cpu_cnt:
                            break
                        try:
                            pname = procs[num].pop()
                        except IndexError:
                            pname = ""
                        if num >= self.current_cpu:
                            line = "%-10s" % pname[:10]
                            self.stdscr.addstr(self.lineno, line_width + ((num-self.current_cpu)*line_width), line, 0)
                    self.lineno += 1
                    if self.lineno >= get_terminal_size()[1]:
                        break

                self.lineno = 1
        try:
            curses.wrapper(ProcessDistributionScreen().initscreen, title="CPU Distribution Screen")
        except (KeyboardInterrupt, SystemExit):
            pass

    def help_process(self):
        print_help_msg("Show All Running Processes with PID",
                       usage=["(system)# process"],
                       filter_opt=["grep", "exclude"])

    def do_process(self, args):
        cmd_str, cmd_len,  l_filter = cmd_parse(args)

        templ = "%-6s %-6s %-100s"
        cprint(templ % ('PID', 'PPID', 'ProcessName'), 'green')

        proc_names = self.process_list()

        for key, value in proc_names.items():
            if value['name'] == 'sshd':
                continue
            line = templ % (key, value['ppid'], '%-20s | %s' % (value['name'], value['org_name']))
            if self.filter(line, l_filter):
                continue

            cprint(line.replace("\n", ''))

    def process_list(self):
        ret = {}
        for p in psutil.process_iter(['pid', 'ppid', 'name', 'cmdline']):
            process_name = " ".join(p.cmdline())
            ret[p.info['pid']] = process_name
            ret[p.info['pid']] = dict(name=p.name(), org_name=process_name, ppid=p.ppid())
        return ret

    def help_killproc(self):
        print_help_msg("Process Kill Command",
                       usage=["(system)# killproc {process name}"],
                       options_args=["process name: Process name to kill"])

    def do_killproc(self, args):
        cmd_str, cmd_len,  _ = cmd_parse(args)
        templ = "%-6s %-6s %-100s"
        if cmd_len == 1:
            cprint(templ % ('PID', 'PPID', 'ProcessName'), 'green')
            proc_names = self.process_list()
            kill_process = []

            for key, value in proc_names.items():
                if value['org_name'].find(cmd_str[0]) >= 0:
                    cprint(templ % (key, value['ppid'], '%-20s | %s' % (value['name'], value['org_name'])))
                    kill_process.append(key)
            if len(kill_process) > 0:
                select_pid = ValueInput("Select Process PID or ALL # ")
                if select_pid is None or select_pid in ('exit', 'quit'):
                    return
                try:
                    pids = list(filter(lambda e: isinstance(e, int), select_pid.strip().split(',')))
                    if select_pid.lower() == 'all':
                        print("kill -9 {0}".format(" ".join(['%d' % pid for pid in kill_process])))
                        os.system("kill -9 {0}".format(" ".join(['%d' % pid for pid in kill_process])))
                    elif len(pids) > 0:
                        print("kill -9 {0}".format(select_pid))
                        os.system("kill -9 {0}".format(select_pid))
                except Exception as k:
                    cprint("PID Exception : {0}".format(k))
        else:
            self.help_killproc()
