from functools import lru_cache
from termcolor import cprint, colored
import cpuinfo, platform, os, psutil, re, curses
from command_center.command import print_help_msg
from command_center.command.system.top import Monitoring

regex_ps_list = [
    'nginx',
    'redis-server',
    'uwsgi',
    'php-fpm',
    'celery',
]

def get_psmon_conf():
    from quadlibrary.AppConfig import gconfig
    # psmon.conf 파일에서 프로세스 목록 불러오기
    home_path = gconfig.get_home
    psmon_conf = os.path.join(home_path, "conf/psmon.conf")

    if os.path.exists(psmon_conf) is False:
        pass

    with open(os.path.join(home_path, "conf/psmon.conf"), "r", encoding="utf-8") as fd:
        for line in fd.readlines():
            if line[0] == '#':
                continue
            l_split = line.split("|")
            if len(l_split) >= 3:
                yield dict(btype=l_split[0].strip(), name=l_split[1].strip(), param=l_split[2].strip())

def get_parent_pid_list():
    # 프로세스 이름으로 가져온 pid들의 parent pid 병합
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
    # pid 중복제거를 위해 set을 사용
    process_list = set()
    # 부모 프로세스 이름, PID값 가져오기
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            processName = proc.info['name']
            if application_regex.match(processName):
                temp = proc
                while temp is not None:
                    if temp.parent().pid == 1 or temp.parent() == None:
                        process_list.add(temp.pid)
                    temp = temp.parent()
        except:
            pass
    return process_list


def get_children_list(process_list, level, interval=0.01):
    # 자식 프로세스 리스트 가져 오기
    lst = []
    level += 1
    for proc in process_list:
        if len(proc.children()) == 0:
            children = []
        else:
            children = get_children_list(proc.children(), level)
        lst.append({
            'pid': proc.pid,
            'name': proc.name(),
            'cpu_usage': proc.cpu_percent(interval=interval),
            'memory_usage': round(proc.memory_info()[0] /2.**30, 2),
            'memory_usage_rss': proc.memory_info().rss,
            'level': level,
            'children': children,
        })
    return lst


def get_all_process_list(process_list, more_flag=False):
    # 자식 프로세스 정보 가져오기
    all_process = []
    for pid in process_list:
        try:
            level = 0
            proc = psutil.Process(pid)
            children = []
            if more_flag == True:
                children = get_children_list(proc.children(), level)
            name = proc.name()
            if level == 0 and len(children) != 0:
                cpu_usage = 0
                for ps in children:
                    cpu_usage += ps['cpu_usage']

                memory_usage = 0
                for ps in children:
                    memory_usage += ps['memory_usage']

                memory_usage_rss = 0
                for ps in children:
                    memory_usage_rss += ps['memory_usage_rss']
            else:
                cpu_usage = proc.cpu_percent(interval=0.01)
                memory_usage_rss = proc.memory_info().rss
                memory_usage = round(proc.memory_info()[0] /2.**30, 2)
            all_process.append({
                'pid': pid,
                'name': name,
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'memory_usage_rss': memory_usage_rss,
                'level': level,
                'children': children,
            })
        except psutil.NoSuchProcess:
            continue
        except psutil.ZombieProcess:
            continue
    return all_process

def get_process_list(more_flag=False):
    # 부모 프로세스, 자식 프로세스 list in dict 형식으로 가져옴
    process_list = get_parent_pid_list()
    all_process = get_all_process_list(process_list, more_flag)
    return all_process

def print_process_tree(ps_list, root_last=True, print_func=cprint):
    from quadlibrary.AppLibrary import convert_size
    # 프로세스 리스트를 tree 형식으로 출력 해줌.
    ps_list_cnt = len(ps_list) - 1
    for idx, proc in enumerate(ps_list):
        name = proc['name']
        level = proc['level']
        pid = str(proc['pid'])
        cpu_usage = str(round(proc['cpu_usage'], 1)) + '%'
        memory_usage = str(round(proc['memory_usage'], 1)) + '%'
        memory_usage_rss = convert_size(proc['memory_usage_rss'])

        # Process Name Print
        proc_name_str = ""
        if level == 0 or root_last:
            proc_name_str += '\t' + ('   ' * level)
        else:
            proc_name_str += '\t|' + ('   ' * level)
        if idx==len(ps_list)-1:
            proc_name_str += '└─ '
        else:
            proc_name_str += '├─ '
        if print_func == cprint:
            proc_name_str = colored(proc_name_str, 'green') + colored(name + ' (' + pid + ')', color='green', attrs=['bold'])
        else:
            proc_name_str = proc_name_str + name + ' (' + pid + ')'
        print_func(proc_name_str)

        # Tree Print
        tree_str = ""
        if (level==0 and idx==ps_list_cnt) or root_last:
            tree_str += '\t' + ('   ' * level)
        else:
            tree_str += '\t|' + ('   ' * level)
        if idx!=ps_list_cnt:
            tree_str += '|'
        else:
            tree_str += ' '

        if print_func == cprint:
            tree_str = colored(tree_str, 'green')

        attribute_str_list = []
        # 두 줄 출력 버전
        # if print_func == cprint:
        #     attribute_str_list.append(colored('  ├─ CPU    : ' + cpu_usage, 'yellow'))
        #     attribute_str_list.append(colored('  └─ Memory : ' + memory_usage, 'yellow'))
        # else:
        #     attribute_str_list.append('  ├─ CPU    : ' + cpu_usage)
        #     attribute_str_list.append('  └─ Memory : ' + memory_usage)
        # 한 줄 출력 버전
        if print_func == cprint:
            attribute_str_list.append(colored('  └─ CPU ('+cpu_usage+'), Memory '+memory_usage_rss+' ('+memory_usage+')', 'yellow'))
        else:
            attribute_str_list.append('  └─ CPU ('+cpu_usage+'), Memory '+memory_usage_rss+' ('+memory_usage+')')

        for attr_str in attribute_str_list:
            print_func(tree_str + attr_str)

        if proc['children'] is not None:
            if level == 0:
                print_process_tree(proc['children'], True if idx==ps_list_cnt else False, print_func)
            else:
                print_process_tree(proc['children'], root_last, print_func)
        
        if level == 0 and idx != ps_list_cnt:
            if print_func == cprint:
                print_func('\t|', 'green')
            else:
                print_func('\t|')


@lru_cache(maxsize=2048)
def get_cpu_info():
    return cpuinfo.get_cpu_info()


class CpuCommandMixin(object):
    def help_cpu(self):
        print_help_msg("Show CPU Status INFO of Current Process",
                       usage=["(system)# cpu"],
                       filter_opt=["more", "limit"])

    def do_cpu(self, args):
        """
            show cpu | <more|limit> 10
        """

        cmd_str, cmd_len, l_filter = self.cmd_parse(args)

        # Options
        more_flag = False
        limit = 10
        if l_filter:
            more_flag = True if l_filter[0] == 'more' else False
            if len(l_filter) == 2 and l_filter[0] in ['more', 'limit']:
                limit = int(l_filter[1])

        cpu_info = get_cpu_info()
        cpu_name = cpu_info["brand_raw"]
        core_count = str(cpu_info["count"])
        node_name = platform.node()

        cprint("")
        cprint("\t" + "[*] This is a show your cpu information", 'yellow')
        cprint("")
        cprint("\t   Node : " + node_name)
        cprint("\t    CPU : " + cpu_name)
        cprint("\t  Cores : " + core_count)
        cprint("")
        cprint("\tOptions : more(" + str(more_flag) + "), limit(" + str(limit) + ")")
        cprint("")

        ps_list = sorted(get_process_list(more_flag), key=lambda x: (x['cpu_usage'], x['memory_usage']), reverse=True)[:limit]
        print_process_tree(ps_list)
        print("")
