import curses
import os
import time

from termcolor import cprint
import psutil

from command_center.command import print_help_msg, NBBScreenMixin
from command_center.library.AppLibrary import convert_size


class DiskCommandMixin(object):
    def help_disk(self):
        print_help_msg("Show Current Disk Status",
                       usage=["(system)# disk"])

    def do_disk(self, args):
        """
        disk performance status
        """

        cprint("  %10s   |    %10s   |    %10s   |    %10s   |    %9s    |  %10s |  %5s  |" % ( "device", "partition", "total", "used", "free", "Use %", "Type"), 'yellow')
        for disk in psutil.disk_partitions(all=False):
            mount = disk.mountpoint
            use = psutil.disk_usage(mount)
            cprint("%-14s | %-15s | %15s | %15s | %15s | %10s%% | %8s |" % (disk.device,
                                                                            mount,
                                                                            convert_size(use.total),
                                                                            convert_size(use.used),
                                                                            convert_size(use.free),
                                                                            use.percent,
                                                                            disk.fstype), 'green')

    def monitor_disk_io(self, cmd_str, l_filter):
        class ProcessDistributionScreen(NBBScreenMixin):
            cpus_hidden = True
            display_cnt = 10  # try to fit into screen
            o_disk = dict()

            def datas(self, interval):
                """Calculate IO usage by comparing IO statics before and
                after the interval.
                Return a tuple including all currently running processes
                sorted by IO activity and total disks I/O activity.
                """
                # first get a list of all processes and disk io counters
                procs = [p for p in psutil.process_iter()]
                for p in procs[:]:
                    try:
                        p._before = p.io_counters()
                    except psutil.Error:
                        procs.remove(p)
                        continue
                disks_before = psutil.disk_io_counters()

                # sleep some time
                time.sleep(interval)

                # then retrieve the same info again
                for p in procs[:]:
                    with p.oneshot():
                        try:
                            p._after = p.io_counters()
                            p._cmdline = ' '.join(p.cmdline())
                            if not p._cmdline:
                                p._cmdline = p.name()
                            p._username = p.username()
                        except (psutil.NoSuchProcess, psutil.ZombieProcess):
                            procs.remove(p)
                disks_after = psutil.disk_io_counters()

                # finally calculate results by comparing data before and
                # after the interval
                for p in procs:
                    p._read_per_sec = p._after.read_bytes - p._before.read_bytes
                    p._write_per_sec = p._after.write_bytes - p._before.write_bytes
                    p._total = p._read_per_sec + p._write_per_sec

                disks_read_per_sec = disks_after.read_bytes - disks_before.read_bytes
                disks_write_per_sec = disks_after.write_bytes - disks_before.write_bytes

                # sort processes by total disk IO so that the more intensive
                # ones get listed first
                processes = sorted(procs, key=lambda p: p._total, reverse=True)

                return (processes, disks_read_per_sec, disks_write_per_sec)

            def refresh_window(self,processes, disks_read_per_sec, disks_write_per_sec):
                display = []

                for disk in psutil.disk_partitions():
                    device = disk.device.split("/")[-1]

                    d_io = psutil.disk_io_counters(perdisk=True)[disk.device.split("/")[-1]]

                    if self.o_disk.get(device, None):
                        d_write = d_io.write_bytes - self.o_disk[device].write_bytes
                        d_read = d_io.read_bytes - self.o_disk[device].read_bytes
                        display.append("%-20s | %-20s | %13s/s | %15s/s " % (disk.device,
                                                                             disk.mountpoint,
                                                                             convert_size(d_read),
                                                                             convert_size(d_write)))
                    self.o_disk[device] = d_io

                line = "     %10s      |      %10s      |   %10s   |   %10s   |" % ( 'device', 'partition', 'read', 'write')
                self.print_line(line, highlight=True)
                for d in display:
                    self.print_line(d)
                self.print_line("")

                """Print results on screen by using curses."""
                templ = "%-5s %-7s %11s %11s  %s"

                disks_tot = "Total DISK READ: %s | Total DISK WRITE: %s" \
                            % (convert_size(disks_read_per_sec), convert_size(disks_write_per_sec))
                self.print_line(disks_tot, highlight=True)
                self.print_line("")

                header = templ % ("PID", "USER", "DISK READ", "DISK WRITE", "COMMAND")
                self.print_line(header, highlight=True)

                for p in processes:
                    line = templ % (
                        p.pid,
                        p._username[:7],
                        convert_size(p._read_per_sec),
                        convert_size(p._write_per_sec),
                        p._cmdline)
                    try:
                        self.print_line(line)
                    except curses.error:
                        break
                self.lineno = 1

        try:
            curses.wrapper(ProcessDistributionScreen().initscreen, title="DISK IO ")
        except (KeyboardInterrupt, SystemExit):
            pass

    def complete_raidcard(self, text, line, begidx, endidx):
        params = ["logical", "physical", "status"]
        line_split = line.split(' ')

        if len(line_split[1].strip()) > 0:
            return [s for s in params if s.startswith(line_split[1])]
        return params

    def help_raidcard(self):
        print_help_msg("Show RAID Info",
                       usage=["(system)# raidcard",
                              "(system)# raidcard {physical | logical | status}"],
                       options_args=["no option : show all",
                                     "physical : show physical info",
                                     "logical : show logical info",
                                     "status : show drives info that have issue"])

    def do_raidcard(self, args):

        """
        Raid All Print
            1. physical disk print
                system) raidcard physical
            2. logical  disk print
                system) raidcard logical
            3. issue disk print
                system) raidcard status
            4. all print
                system) raidcard
        """
        try:
            k_disk = self.get_raid()
        except:
            cprint('RAIDcard Not Found', 'red')
            return

        cmd_str, cmd_len, l_filter = self.cmd_parse(args)
        if cmd_str and cmd_str[0] == 'physical':
            self.__print_data(k_disk.pd_data, "physical")
        elif cmd_str and cmd_str[0] == 'logical':
            self.__print_data(k_disk.ld_data, "logical")
        elif cmd_str and cmd_str[0] == 'status': # raidcard status
            issue_data = self.__get_issue_disk(k_disk.pd_data)
            self.__print_data(issue_data, "status")
        else:
            self.__print_data(k_disk.pd_data, "physical")
            self.__print_data(k_disk.ld_data, "logical")

    def __get_issue_disk(self, p_data : list) -> list:
        result = []

        for disk_data in p_data:
            # online이 아닌 data 추출
            if not disk_data['firmware_state'].startswith('online') or disk_data['disk_state'] != 'ok':
                result.append(disk_data)

        return result

    def get_raid(self):
        from command_center.system.raid import HPRaidManager, MegaRaidManager, DellManager
        if os.path.exists('/usr/sbin/ssacli'):
            k_disk = HPRaidManager(extract_data=True)
        elif os.path.exists('/opt/MegaRAID/perccli/perccli64'):
            k_disk = DellManager(extract_data=True)
        else:
            k_disk = MegaRaidManager(extract_data=True)
        return k_disk

    def __print_data(self, p_data, p_type):

        pd_color_item = ["firmware_state", "disk_state", "bbu_status", "state"]
        normal_state = ["ok", "optimal", "online, spun up", "online, spun down"]

        if p_type == "physical":
            cprint("\n[ Physical Information]\n", "cyan")
        elif p_type == "logical":
            cprint("\n[ Logical Information]\n", "cyan")
        elif p_type == "status":
            if not p_data:
                cprint("There is no issue in disks\n", "green")
                return
            cprint("\n[ Issue Disk Information]\n", "cyan") 

        for order, value in enumerate(p_data):
            if p_type == "physical":
                cprint('Disk Number : {} '.format(order), "yellow")
            elif p_type == "logical":
                cprint('Drive Number : {}'.format(order), "yellow")
            elif p_type == "status":
                cprint('Issue Disk Number : {}'.format(order), "yellow")

            for key, value in value.items():
                if value is None:
                    continue

                if key in pd_color_item and value in normal_state:  
                    cprint(" "*4 + "{:<23} : {}".format(key, value), "green")  
                elif key in pd_color_item and value not in normal_state:
                    cprint(" "*4 + "{:<23} : {}".format(key, value), "red")
                elif key in ['size', 'capacity']:
                    cprint(" "*4 + "{:<23} : {}".format(key, convert_size(value)))
                elif key == 'device_speed':
                    cprint(" "*4 + "{:<23} : {}".format(key, convert_size(value, bit=True)))
                elif key == 'raid_level':
                    cprint(" "*4 + "{:<23} : ".format(key), end="")
                    cprint("Raid {}".format(value), "yellow")
                else:
                    cprint(" "*4 + "{:<23} : {}".format(key, value))
            cprint("------------------------------------------------------ ")

    def slot_disk(self, cmd_str, l_filter):
        """
        Slot Print
        """
        from tabulate import tabulate

        k_disk = self.get_raid()
        pd_data = k_disk.pd_data
        disk_list = []
        for data in pd_data:
            disk_list.append([data['device_id'], convert_size(data['capacity']), data['disk_state']])
        slot = tabulate(disk_list, headers=("ID", "Capacity", "Status"), tablefmt="fancy_grid")
        cprint("")
        cprint(slot, 'green')
