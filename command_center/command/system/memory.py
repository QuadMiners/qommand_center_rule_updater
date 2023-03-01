from functools import lru_cache
import platform
import subprocess

import psutil
from termcolor import cprint

from tabulate import tabulate

from command_center.command import print_help_msg
from command_center.command.system.cpu import get_process_list, print_process_tree


@lru_cache(maxsize=2048)
def get_memory_info():
    # lshw -short -C memory 명령어를 이용한 리눅스 Memory 정보 가져오기
    try:
        p = subprocess.Popen(["lshw -short -C memory"], stdout=subprocess.PIPE, shell=True)
        result = p.communicate()[0].decode("utf-8").split('\n')
        total_info = list(filter(lambda x:'System Memory' in x, result))[0].split()
        hw_path = total_info[0]
        total_memory = total_info[2]
        bank_info_list = list(filter(lambda x:hw_path in x and x.split()[0]!=hw_path, result))
    except:
        return None
    return {
        "hw_path": hw_path,
        "total_memory": total_memory,
        "bank_info_list" : bank_info_list,
    }


class MemoryCommandMixin(object):
    def help_memory(self):
        print_help_msg("Show Memory Status of the Current Process",
                       usage=["(system)# memory"],
                       filter_opt=["more", "limit"])

    def do_memory(self, args):
        """
            show memory | <more|limit> 10
        """
        # Options
        more_flag = False

        params, plen, l_filter = self.cmd_parse(args)

        limit = 10
        if l_filter:
            more_flag = True if l_filter[0] == 'more' else False
            if len(l_filter) == 2 and l_filter[0] in ['more', 'limit']:
                limit = int(l_filter[1])

        from command_center.library.AppLibrary import convert_size

        node_name = platform.node()
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
        
        cprint("")
        cprint("\t" + "[*] This is a show your cpu information", 'yellow')
        cprint("")
        cprint("\t   Node : " + node_name)
        cprint("\t   Info : {0}".format(memory_info_str))
        cprint("")
        cprint("\tOptions : more(" + str(more_flag) + "), limit(" + str(limit) + ")")
        cprint("")

        ps_list = sorted(get_process_list(more_flag), key=lambda x: (x['memory_usage'], x['cpu_usage']), reverse=True)[:limit]
        print_process_tree(ps_list)
        print("")

    def slot_memory(self, cmd_str, l_filter):
        memory_info = get_memory_info()
        table_list = []
        cprint("")
        cprint("[*] This is a show your memory slot information", 'yellow')
        cprint("")
        cprint("\tHareware Path : {0}".format(memory_info["hw_path"]), 'cyan')
        cprint("\t Total Memory : {0}".format(memory_info["total_memory"]), 'cyan')
        cprint("")
        for info in memory_info['bank_info_list']:
            info_split = info.split()
            hw_path = info_split[0][-1]
            description = " ".join(info_split[2:])
            table_list.append([hw_path, description])
        if len(table_list) > 8:
            half_index = int(len(table_list) / 2)
            for idx in range(0, half_index):
                table_list[idx] += table_list[idx+half_index]
            table_list = table_list[:half_index]
        slot = tabulate(table_list, tablefmt="fancy_grid")
        cprint(slot, 'green')
