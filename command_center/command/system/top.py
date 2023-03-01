
import curses
from enum import Enum
import platform
import re

import psutil

from command_center.command import NBBScreenMixin


class MonitorTopCommandMixin(object):
    def monitor_top(self, cmd_str, l_filter):
        try:
            curses.wrapper(Monitoring(mode="Cpu").initscreen)
        except (KeyboardInterrupt, SystemExit):
            pass


class Monitoring(NBBScreenMixin):
    class SortType(Enum):
        CPU_DESC = 0
        CPU_ASC = 1
        MEM_DESC = 2
        MEM_ASC = 3

        def __str__(self):
            return self._name_.lower()
    options = {
        "cmdline": False,
        "sort": SortType.CPU_DESC,
        "nbb_application": False,
        "mode": "Cpu",
    }
    cpu_info = None
    memory = {
        "virtual": None,
        "swap": None,
        "info": None,
    }

    def initscreen(self, stdscr, *args, **kwargs):
        kwargs["title"] = self.options["mode"] + " Monitoring"
        super().initscreen(stdscr, *args, **kwargs)

    def __init__(self, mode="Cpu"):
        super().__init__()
        self.options["mode"] = mode
        from command_center.command.system.cpu import get_cpu_info
        self.cpu_info = get_cpu_info()
        self.memory["virtual"] = psutil.virtual_memory()
        self.memory["swap"] = psutil.swap_memory()
        self.options["sort"] = self.SortType.CPU_DESC if self.options['mode']=="Cpu" else self.SortType.MEM_DESC

    def datas(self, interval):
        cpu_times_percent = psutil.cpu_times_percent(interval=interval)
        return (cpu_times_percent, None)

    def refresh_window(self, cpu_times_percent, temp):
        from command_center.command.system.cpu import get_process_list, get_psmon_conf, regex_ps_list
        from command_center.library.AppLibrary import convert_size
        span = 2
        process_list = get_process_list(True)
        node_name = platform.node()
        self.print_line("")
        self.print_line("     Node : " + node_name)
        if self.options["mode"] == "Cpu":
            # cpu 정보 출력
            cpu_info = self.cpu_info

            cpu_name = cpu_info["brand_raw"]
            core_count = str(cpu_info["count"])
            self.print_line("      CPU : " + cpu_name)
            self.print_line("    Cores : " + core_count)

            cpu_times_percent = cpu_times_percent._asdict()
            cpu_times_print_str = "Cpu Usage : "
            for key, value in cpu_times_percent.items():
                cpu_times_print_str += str(re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), key, 1)) + " (" + str(value) + "%)" + ', '
            cpu_times_print_str = cpu_times_print_str[:len(cpu_times_print_str)-2]
            self.print_line(cpu_times_print_str)
        elif self.options["mode"] == "Memory":
            virtual_memory = psutil.virtual_memory()
            memory_fields = virtual_memory._fields
            memory_info_str = ""
            memory_info_str += "Total "+convert_size(virtual_memory.total)+" - " if 'total' in memory_fields else ""
            memory_info_str += "Used "+convert_size(virtual_memory.used) if 'used' in memory_fields else ""
            memory_info_str += ", Free "+convert_size(virtual_memory.free) if 'free' in memory_fields else ""
            memory_info_str += ", Cached "+convert_size(virtual_memory.cached) if 'cached' in memory_fields else ""
            memory_info_str += ", Shared "+convert_size(virtual_memory.shared) if 'shared' in memory_fields else ""
            memory_info_str += ", Buffers "+convert_size(virtual_memory.buffers) if 'buffers' in memory_fields else ""
            memory_info_str += ", Available "+convert_size(virtual_memory.available) if 'available' in memory_fields else ""
            self.print_line("    Info : " + memory_info_str)
        self.print_line("  Options : " + ", ".join([k + " (" + str(v) + ")" for k, v in self.options.items()]))
        self.print_line("")
        self.print_line(f"{'Pid':^5}" + (" "*span)+f"{'Cpu(%)':^6}" + (" "*span)+f"{'Mem(%)':^6}" + (" "*span)+f"{'Mem':^10}" + (" "*span)+f"{'Name':^15}", True)

        psmon_list = []
        try:
            for ps in get_psmon_conf():
                psmon_list.append(ps['name'])
        except:
            pass
        if len(psmon_list) == 0:
            application_regex = re.compile(r'{0}'.format("|".join(regex_ps_list)))
        else:
            application_regex = re.compile(r'{0}|{1}'.format("|".join(regex_ps_list), "|".join(psmon_list)))
        
        process_list = []
        for p in psutil.process_iter(['pid', 'name']):
            try:
                if self.options['nbb_application'] == True and application_regex.match(p.name()) is None:
                    continue
                data = {
                    "name": p.name(),
                    "pid": p.pid,
                    "cpu_percent": p.cpu_percent(),
                    "memory_percent": round(p.memory_percent(), 1),
                    "cmdline": p.cmdline(),
                    "memory": p.memory_info().rss
                }
                process_list.append(data)
            except psutil.NoSuchProcess:
                continue
            except psutil.ZombieProcess:
                continue
        ps_list = []
        if self.options["sort"] == self.SortType.CPU_DESC or self.options["sort"] == self.SortType.MEM_DESC:
            if self.options["sort"] == self.SortType.CPU_DESC:
                sort_lambda = lambda x: (x['cpu_percent'], x['memory_percent'], x['memory'], x['name'])
            else:
                sort_lambda = lambda x: (x['memory_percent'], x['memory'], x['cpu_percent'], x['name'])
            ps_list = sorted(process_list, key=sort_lambda, reverse=True)
        else:
            if self.options["sort"] == self.SortType.CPU_ASC:
                sort_lambda = lambda x: (x['cpu_percent'], x['memory_percent'], x['memory'], x['name'])
            else:
                sort_lambda = lambda x: (x['memory_percent'], x['memory'], x['cpu_percent'], x['name'])
            ps_list = sorted(process_list, key=sort_lambda)
        for p in ps_list:
            pid = f"{str(p['pid']):>5}"
            cpu_percent = (" "*span)+"{:>6}".format(str(p['cpu_percent']) + "%")
            memory_percent = (" "*span)+"{:>6}".format(str(p['memory_percent']) + "%")
            name = (" "*span) + (f"{p['name'][:15]:<15}" if self.options["cmdline"] == True else f"{p['name']:<15}")
            cmdline = (" "*span) + " ".join(p['cmdline']) if self.options["cmdline"] == True else ""
            memory = (" "*span)+f"{convert_size(p['memory']):>10}"
            self.print_line(pid + cpu_percent + memory_percent + memory + name + cmdline)
        self.lineno = 1

    def key_event(self):
        # 키 이벤트
        key = self.key
        if key == "c":
            # cmdline 표시 옵션
            self.options["cmdline"] = False if self.options["cmdline"] else True
        elif key == "s":
            # 정렬 조건 변경 옵션
            self.options["sort"] = self.SortType.CPU_DESC if self.options["sort"].value == self.SortType.MEM_ASC.value else self.SortType._value2member_map_[self.options["sort"].value + 1]
        elif key == "a":
            # 어플리케이션만 표시 옵션
            self.options['nbb_application'] = False if self.options['nbb_application'] else True
        elif key == "m":
            # 모니터링 모드 변경
            self.options['mode'] = "Memory" if self.options['mode']=="Cpu" else "Cpu"
            self.options["sort"] = self.SortType.CPU_DESC if self.options['mode']=="Cpu" else self.SortType.MEM_DESC
            self.maintitle = self.options['mode'] + " Monitoring"