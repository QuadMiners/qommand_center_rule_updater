#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ipaddress
import datetime
import logging
import os
from datetime import datetime as dt
import socket

import psutil

from termcolor import cprint, colored

from command_center import DBException
from command_center.command import ToolCommandMixin, print_help_msg
from command_center.command.system.cpu import CpuCommandMixin
from command_center.command.system.crontab import CronTabCommand
from command_center.command.system.disk import DiskCommandMixin
from command_center.command.system.memory import MemoryCommandMixin
from command_center.command.system.network import NetworkConfigMixin
from command_center.command.system.process import NBBProcessMixin
from command_center.command.system.top import MonitorTopCommandMixin
from command_center.library.AppConfig.config import system_model_info
from command_center.library.AppLibrary import model_id, hardware_key
from command_center.library.AppPing import WAIT_TIMEOUT, NUM_PACKETS, PACKET_SIZE, quiet_ping

logger = logging.getLogger(__name__)


class NBBSystemManager(DiskCommandMixin, NetworkConfigMixin, CpuCommandMixin, MemoryCommandMixin, MonitorTopCommandMixin, NBBProcessMixin, ToolCommandMixin):
    intro = colored('NetworkBlackbox System shell.\nType help or ? to list commands.\n', 'yellow')
    prompt = colored('%s (system)# ' % hostname, 'cyan')
    hidden_methods = ['do_exit']

    def help_monitor(self):
        print_help_msg("System Monitoring",
                       usage=["(system)# monitor {top | disk | interface | distribution}"],
                       options_args=["top: Monitoring CPU/Memory",
                                     "\ttop Shortcuts",
                                     "\tc: cmdline on/off",
                                     "\ts: sorting",
                                     "\ta: filtering nbb process",
                                     "\tm:change mode(cpu/memory)",
                                     "disk: Monitoring disk",
                                     "interface: Monitoring NIC IO",
                                     "distribution: Check which daemons are using CPU"])

    def complete_monitor(self, text, line, begidx, endidx):
        params = ["top", "disk", "interface", "distribution"]
        line_split = line.split(' ')

        if len(line_split[1].strip()) > 0:
            return [s for s in params if s.startswith(line_split[1])]
        return params

    def do_monitor(self, args):
        cmd_str, cmd_len, l_filter = self.cmd_parse(args)
        if cmd_len > 0:
            try:
                if cmd_str[0] == 'disk':
                    self.monitor_disk_io(cmd_str, l_filter)
                elif cmd_str[0] == 'interface':
                    self.monitor_interface_io(cmd_str, l_filter)
                elif cmd_str[0] == 'distribution':
                    self.monitor_distribution(cmd_str, l_filter)
                elif cmd_str[0] == 'top':
                    self.monitor_top(cmd_str, l_filter)
            except Exception as b:
                pass
        else:
            self.help_monitor()

    def help_crontab(self):
        print_help_msg("Enter Crobtab Shell",
                       usage=["(system)# crontab"])

    def do_crontab(self, args):
        try:
            CronTabCommand().cmdloop()
        except KeyboardInterrupt:
            pass

    def complete_slot(self, text, line, begidx, endidx):
        params = ["memory", "disk"]
        line_split = line.split(' ')

        if len(line_split[1].strip()) > 0:
            return [s for s in params if s.startswith(line_split[1])]
        return params

    def help_slot(self):
        print_help_msg("Show Slot Info (Disk | Memory)",
                       usage=["(system)# slot {memory | disk}"],
                       options_args=["memory: Show memory bank info",
                                     "disk: Show disk status and size info"])

    def do_slot(self, args):
        cmd_str, cmd_len, l_filter = self.cmd_parse(args)
        if cmd_len > 0:
            if cmd_str[0] == 'disk':
                self.slot_disk(cmd_str, l_filter)
            elif cmd_str[0] == 'memory':
                self.slot_memory(cmd_str, l_filter)
        else:
            self.help_slot()

    def help_who(self):
        print_help_msg("Show SSH Connected User Info",
                       usage=["(system)# who"])

    def do_who(self, args):
        users = psutil.users()
        for user in users:
            proc_name = psutil.Process(user.pid).name() if user.pid else ""
            cprint("%-12s %-10s %-10s %-14s %s" % (
                user.name,
                user.terminal or '-',
                dt.fromtimestamp(user.started).strftime("%Y-%m-%d %H:%M"),
                "(%s)" % user.host if user.host else "",
                proc_name
            ), color='yellow')

    def help_server(self):
        print_help_msg("Show Server Hardware Info",
                       usage=["(system)# server"])

    def do_server(self, args):
        """
        hardware key(uuid)
        """
        try:
            server_info = system_model_info()
            for key, value in server_info.items():
                cprint("{0:15s} | {1}".format(key, value), "green")
            print("")
            cprint("Hardware ID     | {0}".format(hardware_key().replace("'", "")), "green")
            cprint("Machine ID      | {0}".format(model_id()), "green")

        except Exception as e:
            cprint("Hardware KEY Check ERROR {0}".format(e), "red")
            pass

    def help_route(self):
        print_help_msg("Show IP Routing Table",
                       usage=["(system)# route"])

    def do_route(self, args):
        """
            route -a
        """
        for index, line in enumerate( self.exec_shell_command('route', readline=True)):
            if index == 0:
                continue

            line = line.decode('utf-8')
            if index == 1:
                cprint(line, 'green')
            else:
                cprint(line)

    def help_date(self):
        print_help_msg("Set System Date",
                       usage=["(system)# date {datetime}"],
                       options_args=["no option: Show datetime now",
                                     "datetime: YYYY-MM-DD HH24:MI:SS"])

    def do_date(self, args):
        """
            현재 시간
            현재 시간 설정
        """
        cmd_str, cmd_len, _ = self.cmd_parse(args)
        if cmd_len == 1:
            try:
                k_date = datetime.datetime.strptime(cmd_str[0].strip(), '%Y-%m-%d %H:%M:%S')
                os.system("date +%s -s @{0} > /dev/null 2>&1 ".format(k_date.timestamp()))
                os.system("hwclock --systohc")
            except Exception as date_err:
                cprint(date_err , color='red')
        else:
            cprint("Date : {0}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')), 'green')

    def help_lsof(self):
        print_help_msg("View Files Not Returned To The System",
                       usage=["(system)# lsof"])

    def do_lsof(self, args):
        """
        반환안된 file 찾기
        lsof | grep delete
        """
        cmd_str, cmd_len, l_filter = self.cmd_parse(args)

        count = 0
        for index, line in enumerate( self.exec_shell_command('lsof', readline=True)):
            line = line.decode('utf-8')
            if index > 0 and self.filter(line, l_filter):
                continue
            if index == 0:
                cprint(line, 'green')
            else:
                cprint(line)
            count += 1
        cprint("Row Count : {0}".format(count), 'green')

    def help_openport(self):
        print_help_msg("Check Open Port in Destination",
                       usage=["(system)# openport {destination-ip} {destination-port}"])

    def do_openport(self, args):
        cmd_str, cmd_len, _ = self.cmd_parse(args)
        if cmd_str and cmd_len > 0:
            try:
                ipaddress.ip_address(cmd_str[0])
            except ValueError:
                cprint("Address is invalid : %s" % cmd_str[0], color='red')
                return
            except Exception as e:
                cprint("Exception %s " % e, color='red')
                return
            try:
                port = int(cmd_str[1])
                if port not in range(1, 65535):
                    cprint("Port is invalid  : %s " % cmd_str[1], color='red')
                    return
            except IndexError:
                cprint("Port information not entered", color='red')
                return
            except Exception as e:
                cprint("Port is invalid  : %s " % cmd_str[1], color='red')
                return
        else:
            self.help_openport()
            return

        connskt = None
        try:
            connskt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connskt.settimeout(10.0)
            connskt.connect((cmd_str[0], int(cmd_str[1])))
            connskt.shutdown(2)
            cprint("OPEN", color='yellow')
        except Exception as e:
            cprint("NOT OPEN : {0}".format(e), 'red')
        finally:
            if connskt:
                connskt.close()

    def help_ping(self):
        print_help_msg("Check Ping with Target IP",
                       usage=["(system)# ping {IP-Addr}"])

    def do_ping(self, args):
        cmd_str, cmd_len, _ = self.cmd_parse(args)

        if cmd_str and cmd_len > 0:
            try:
                ipaddress.ip_address(cmd_str[0])
            except ValueError:
                cprint("Address is invalid : %s" % cmd_str[0])
                return
            except Exception as e:
                cprint("Exception %s " % e)
                return
        else:
            self.help_ping()
            return

        ping = quiet_ping
        maxtime, mintime, avgtime, loss, fail_cnt = ping(cmd_str[0], timeout=WAIT_TIMEOUT * 1000, count=NUM_PACKETS,
                                                         packet_size=PACKET_SIZE, server=None)

    def help_hostname(self):
        print_help_msg("Change System Hostname",
                       usage=["(system)# {hostname}"],
                       options_args=["hostname: new hostname"])

    def do_hostname(self,args):

        def __show_hostname():
            import socket
            hostname = socket.gethostname()

            cprint("-" * 20 + "Hostname Info" + "-" * 20, "green")
            cprint('    Current Hostname : ', 'green', end=""),
            cprint('%s' % hostname.replace('\n', ''), "yellow")
            cprint("-" * 53, "green")

        __show_hostname()
        params, plen,  _ = self.cmd_parse(args)
        if plen == 1:
            # 설정 후 hostname 보여주기
            set_hostname_cmd = 'hostnamectl set-hostname %s' % params[0] # hostname 변경 cmd
            output = self.exec_shell_command(set_hostname_cmd)  # command 실행
            """
                DB Update
            """
            try:
                import quadlibrary.database as db
                db.pmdatabase.execute("UPDATE qommand_center_info set host_name=%s ", (params[0],))
            except DBException as e:
                pass

            cprint("OK", 'yellow')

            global hostname
            hostname = params[0]
            self.prompt = colored('%s (system)# ' % hostname, 'cyan')