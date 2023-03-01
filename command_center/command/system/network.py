import atexit
import curses
import ipaddress
import os
import re
import signal
import socket
import time

import netifaces
import psutil
from termcolor import cprint, colored
import command_center.library.AppDefine as app_define
from command_center.command import ValueInput, print_help_msg, NBBScreenMixin, ToolCommandMixin
from command_center.library.AppLibrary import is_valid_ipv4_address, convert_size



"""
Prifix 
"""
NET_INFO_FILEPATH_PREFIX = "/etc/sysconfig/network-scripts/ifcfg"

"""
Bonding File
"""
bondfile = "/etc/modprobe.d/bonding.conf"


NIC_CONFIG="""
TYPE=Ethernet
#PROXY_METHOD=none
#BROWSER_ONLY=no
BOOTPROTO=static
DEFROUTE=yes
IPV4_FAILURE_FATAL=no
IPV6INIT=no
NAME={nic_name}
UUID={uuid}
DEVICE={nic_name}
ONBOOT=yes
IPADDR={ipaddr}
NETMASK={netmask}
"""

BOND_NIC_CONFIG="""
DEVICE={nic_name}
BOOTPROTO=none
ONBOOT=yes
IPADDR={ipaddr}
NETMASK={netmask}
BONDING_OPTS="mode=1 miimon=100"
USERCTL=no 

#{nic_1}|{nic_2}
"""

BOND_REAL_NIC_CONFIG="""
DEVICE={nic_name}
BOOTPROTO=none
ONBOOT=YES
HWADDR=00:00:00:00:00:00
MASTER={bond_nic}
SLAVE=yes 
USERCTL=no
"""


def nicinfo(iface):
    allAddrs = netifaces.ifaddresses(iface)
    ipaddr = "-"

    for family in allAddrs:
        addrs = allAddrs[family]
        fam_name = netifaces.address_families[family]
        if fam_name == "AF_INET":
            for addr in addrs:
                ipaddr = addr['addr']
    return "{0} ( {1} )".format(iface, ipaddr)

def bonding_nic():
    ret = []
    if os.path.exists(bondfile):
        with open(bondfile) as fd:
            lines = fd.readlines()
            for line in lines:
                k_line = line.strip()
                if len(k_line) > 0 and k_line[0] != '#':
                    value = k_line.split()[1].strip()
                    ret.append(value)
    return ret


"""
Gateway 적용을 할 수 있는 기능을 추가로 만들어야한다.
# interface eth1 eth2 bond3 
if ) #ip address  IP  NETMASK 
# ip default-gateway 192.168.10.10
"""

class NetworkIPAddress(ToolCommandMixin):
    prompt = colored('%s (system > ip)# ' % hostname, 'cyan')
    param = {}
    bond_config = False
    """
        Bonding 의 경우 nic_1 , nic_2 가 모두 존재 할때이다.
    """
    def __init__(self, nic_name, nic_1=None, nic_2=None, completekey='tab', stdin=None, stdout=None):
        super(NetworkIPAddress, self).__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        self.param['nic_name'] = nic_name
        self.param['nic_1'] = nic_1
        self.param['nic_2'] = nic_2

        if nic_1 and nic_2:
            self.bond_config = True

    def help_ip(self):
        print_help_msg("Set IP Configuration",
                       usage=["(system > ip)# ip address {ip-address} {netmask}"],
                       options_args=["ip-address : IP address to change",
                                     "netmask: netmask to change"])

    def complete_ip(self, text, line, begidx, endidx):
        options = ['address']
        if not text:
            return options
        else:
            return list(filter(lambda x: text in x, options))

    def do_ip(self, args):

        cmd_str, cmd_len , _ = self.cmd_parse(args)

        if cmd_len != 3 or cmd_str[0] not in ['address']:
            self.help_ip()
            return

        if is_valid_ipv4_address(cmd_str[1].strip()) is False:
            cprint("ipaddress invalid :  {0}".format(cmd_str[1]))
            return

        if is_valid_ipv4_address(cmd_str[2].strip()) is False:
            cprint("netmask invalid :  {0}".format(cmd_str[2]))
            return
        self.param['ipaddr'] = cmd_str[1]
        self.param['netmask'] = cmd_str[2]
        self.set_network_interface()

        if app_define.APP_DEBUG is False:
            self.network_restart()

    def load_nic_info(self, nic_name):

        filename = "{0}-{1}".format(NET_INFO_FILEPATH_PREFIX, nic_name)

        # 추출을 위한 정규표현식
        match = re.compile("UUID=(?P<uuid>.*?)$")
        match_ip = re.compile("IPADDR=(?P<ipaddr>.*?)$")
        match_mask = re.compile("NETMASK=(?P<netmask>.*?)$")
        match_gw = re.compile("GATEWAY=(?P<gateway>.*?)$")

        # 파일을 한 라인씩 읽어들여 기존 정보를 찾음
        with open(filename, 'r') as fd:
            while True:
                line = fd.readline()

                search = match.search(line)
                search_ip = match_ip.search(line)
                search_mask = match_mask.search(line)
                search_gw = match_gw.search(line)

                # 네트워크 정보 찾으면 저장
                if search:
                    self.param['uuid'] = search.groupdict().get('uuid')

                if search_ip:
                    self.param['ipaddr'] = search_ip.groupdict().get('ipaddr')

                if search_mask:
                    self.param['netmask'] = search_mask.groupdict().get('netmask')

                if search_gw:
                    self.param['gateway'] = search_gw.groupdict().get('gateway')

                if not line:
                    break

    def set_network_interface(self):
        filename = "{0}-{1}".format(NET_INFO_FILEPATH_PREFIX, self.param['nic_name']) # 실경로
        org_filename = "{0}-{1}_org".format(NET_INFO_FILEPATH_PREFIX, self.param['nic_name']) # 실경로
        bond = False

        if self.param['nic_name'] in bonding_nic():
            bond = True

        if app_define.APP_DEBUG:
            try:
                os.makedirs('./test/network-scripts')
            except FileExistsError:
                pass
            filename = "./test/network-scripts/ifcfg-{0}".format(self.param['nic_name'])

        if self.bond_config is False or bond is False:
            self.load_nic_info(self.param['nic_name'])

        if not os.path.exists(org_filename):
            if bond is False:
                os.system("cp -f {0} {1}".format(filename, org_filename))

        with open(filename, 'w') as fd:
            if self.bond_config is True or bond is True:
                """
                    Bonding 설정과 , NIC 에 설정과 두가지 설정은 같은 동작을 해야됨.
                """
                fd.write(BOND_NIC_CONFIG.format(**self.param))
            else:
                fd.write(NIC_CONFIG.format(**self.param))

        if self.bond_config is True:
            self.set_bonding()

        if app_define.APP_DEBUG:
            with open(filename) as fd:
                print(fd.read())

    def set_bonding(self):
        """
            Bonding 을 진행
        """
        try:
            try:
                os.makedirs("/".join(bondfile.split('/')[:-1]))
            except FileExistsError:
                pass

            with open(bondfile, 'a') as fd:
                fd.write("alias {0} bonding\n".format(self.param['nic_name']))
        except Exception as k:
            cprint("ERROR : {0}".format(k), color='red')
            return

        self.bond_nic_config(self.param['nic_1'], self.param['nic_name'])
        self.bond_nic_config(self.param['nic_2'], self.param['nic_name'])

    def bond_nic_config(self, ethname, bondnic):
        filename = "{0}-{1}".format(NET_INFO_FILEPATH_PREFIX, ethname) # 실경로
        if app_define.APP_DEBUG:
            filename = "./test/network-scripts/ifcfg-{0}".format(ethname)
        try:
            with open(filename, 'w') as fd:
                fd.write(BOND_REAL_NIC_CONFIG.format(**dict(nic_name=ethname, bond_nic=bondnic)))
        except Exception as k:
            cprint("ERROR : {0}".format(k))

        if app_define.APP_DEBUG:
            with open(filename) as fd:
                print(fd.read())

    def network_restart(self):
        if app_define.APP_DEBUG:
            """DEBUG 이면 return"""
            return

        self.exec_shell_command("nbb_manager stop")
        self.exec_shell_command('rmmod bonding')
        self.exec_shell_command('systemctl restart network')
        cprint("OK", 'yellow')
        """
            license 데몬 재기동  ,DB 에 IP 정보 업데이트 해야되서 재기동해야함.
        """
        with open('/var/run/quadminers/license.pid') as fd:
            license_pid = fd.read()
            os.killpg(os.getpgid(int(license_pid)), signal.SIGKILL)


class NetworkIPBondingAddress(NetworkIPAddress):

    def get_bond_config_nic(self):
        filename = "{0}-{1}".format(NET_INFO_FILEPATH_PREFIX, self.param['nic_name'])

    def help_failback(self):
        print_help_msg("FailBack - Bonding  NIC Active",
                       usage=["(system > ip)# failback {bonding-active-nic}"])

    def do_failback(self, args):
        "ifenslave -c bond0  eth0"

    def help_remove(self):
        print_help_msg("Remove Bonding NIC",
                       usage=["(system > ip)# remove {bondname}"],
                       options_args=["bondname: bondname to remove"])

    def do_remove(self, args):
        #삭제  remove <nic bonding name >
        cmd_str, cmd_len, _ = self.cmd_parse(args)
        bondnic = bonding_nic()

        if self.param['nic_name'] not in bondnic:
            cprint("non-existent nic < {0} > ".format(cmd_str[0]), 'red')
            return

        try:
            choice_input = ValueInput("Are you sure you want to delete the settings? (Y/N")
            if choice_input and choice_input.strip().lower() == 'y':
                write = []

                if os.path.exists(bondfile):
                    with open(bondfile) as fd:
                        lines = fd.readlines()
                        for line in lines:
                            k_line = line.strip()
                            if len(k_line) > 0 and k_line[0] != '#':
                                s_line = k_line.split()
                                if s_line[1].strip() == cmd_str[0].strip():
                                    continue
                                write.append(line)

                    with open(bondfile, 'w') as fd:
                        fd.write("\n".join(write))
                """
                    제외 하고 __ 파일을 원복 시키기 
                """
                filename = "{0}-{1}".format(NET_INFO_FILEPATH_PREFIX, p_args[0]) # 실경로
                if app_define.APP_DEBUG:
                    filename = "./test/network-scripts/ifcfg-{0}".format(p_args[0])
                    cprint(filename)

                if os.path.exists(filename):
                    try:
                        with open(filename) as fd:
                            for line in fd.readlines():
                                if line[0] == '#':
                                    nics = line[1:].split('|')
                                    for nic in nics:
                                        org_file = "{0}-{1}".format(NET_INFO_FILEPATH_PREFIX, nic.strip())  # 실경로
                                        backup_file = "{0}-{1}_org".format(NET_INFO_FILEPATH_PREFIX, nic.strip())  # 실경로
                                        if app_define.APP_DEBUG:
                                            print(f'cp -f {backup_file} {org_file}')
                                        else:
                                            os.system(f'cp -f {backup_file} {org_file}')
                    except Exception as k:
                        cprint('ERROR : {0}'.format(k))
                else:
                    cprint('Not Found Original File : {0}'.format(filename), color='yellow')
        except Exception:
            pass


class NetworkConfigMixin(object):
    """
        interface nic
        bonding nic
    """
    param = dict()
    ethernet = [iface for iface in netifaces.interfaces()]

    def complete_interface(self, text, line, begidx, endidx):
        if not text:
            return self.ethernet
        else:
            return list(filter(lambda x: text in x, self.ethernet))

    def help_interface(self):
        print_help_msg("Network Interface Configuration",
                       usage=["(system)# interface",
                              "(system)# interface {nic}"],
                       options_args=["no option: Show current NIC info, Filter option available",
                                     "nic: Enter nic setting shell"],
                       filter_opt=["grep", "exclude"])

    def do_interface(self, args):
        cmd_str, cmd_len, l_filter = self.cmd_parse(args)

        if cmd_len == 1:
            if cmd_str[0] not in self.ethernet:
                cprint(" non-existent nic  < {0} > ".format(cmd_str[0]), 'red')
                return
            if cmd_str[0] in bonding_nic():
                NetworkIPBondingAddress(cmd_str[0]).cmdloop()
            else:
                NetworkIPAddress(cmd_str[0]).cmdloop()
        else:
            af_map = {
                socket.AF_INET: 'IPv4',
                socket.AF_INET6: 'IPv6',
                psutil.AF_LINK: 'MAC',
            }

            duplex_map = {
                psutil.NIC_DUPLEX_FULL: "full",
                psutil.NIC_DUPLEX_HALF: "half",
                psutil.NIC_DUPLEX_UNKNOWN: "none",
            }

            stats = psutil.net_if_stats()
            for nic, addrs in psutil.net_if_addrs().items():
                if nic == 'lo':
                    continue

                if self.filter(nic, l_filter):
                    continue

                cprint("%s:" % (nic), 'yellow')
                if nic in stats:
                    st = stats[nic]
                    cprint("    stats          : ", color='yellow', end='')
                    cprint("speed=%sMB, duplex=%s, mtu=%s, up=%s" % (
                        st.speed, duplex_map[st.duplex], st.mtu,
                        "yes" if st.isup else "no"), color='green')

                for addr in addrs:
                    cprint("    %-4s" % af_map.get(addr.family, addr.family), color='yellow', end="")
                    cprint(" address   : %s" % addr.address, color='green')
                    if addr.broadcast:
                        cprint("         broadcast : %s" % addr.broadcast, 'green')
                    if addr.netmask:
                        cprint("         netmask   : %s" % addr.netmask, 'green')
                    if addr.ptp:
                        cprint("      p2p       : %s" % addr.ptp, 'green')

        if cmd_len != 1:
            self.help_interface()
            return

    def complete_bonding(self, text, line, begidx, endidx):
        if not text:
            return self.ethernet
        else:
            return list(filter(lambda x: text in x, self.ethernet))

    def help_bonding(self):
        print_help_msg("Set Bonding Command",
                       usage=["(system)# bonding {nic1} {nic2} {bondname}"],
                       options_args=["nic1: first NIC",
                                     "nic2: second NIC",
                                     "bondname: Bond Name"])

    def do_bonding(self, args):
        cmd_str, cmd_len, _ = self.cmd_parse(args)

        if cmd_len != 3:
            self.help_bonding()
            return

        if cmd_str[0] not in self.ethernet:
            cprint(" non-existent nic  < {0} > ".format(cmd_str[0]), 'red')
            return

        if cmd_str[1] not in self.ethernet:
            cprint(" non-existent nic < {0} > ".format(cmd_str[1]), 'red')
            return
        if cmd_str[2] in self.ethernet:
            cprint(" non-existent bond nic name < {0} > ".format(cmd_str[2]), 'red')
            return

        """
            IP 를 입력 받는다.
        """
        self.param['nic_1'] = cmd_str[0]
        self.param['nic_2'] = cmd_str[1]
        NetworkIPAddress(cmd_str[2], nic_1=cmd_str[0], nic_2=cmd_str[1]).cmdloop()

        self.ethernet = [iface for iface in netifaces.interfaces()]

    def help_ip(self):
        print_help_msg("Set Gateway or Nameserver Configuration Command",
                       usage=["(system)# ip { default-gateway | name-server } {ipaddr}"],
                       options_args=["default-gateway | name-server : Choose what to change",
                                     "ipaddr: IP-Address to change"])

    def do_ip(self, args):
        options = ['default-gateway', 'name-server']

        cmd_str, cmd_len, _ = self.cmd_parse(args)

        if cmd_len == 2 and cmd_str[0] in options:
            option = cmd_str[0]
            if option == 'default-gateway':
                try:
                    value = cmd_str[1]
                    try:
                        ipaddress.ip_address(value)
                    except ValueError:
                        cprint(f"The entered value type of {value} is invalid  ", "red")
                        return

                    filename = '/etc/sysconfig/network'
                    if app_define.APP_DEBUG:
                        filename = './network'

                    with open(filename, 'w') as fd:
                        fd.write("NETWORKING=yes\nGATEWAY={0}\n".format(value))

                    if app_define.APP_DEBUG is False:
                        self.exec_shell_command('systemctl restart network')

                    cprint("OK", 'yellow')
                except Exception as e:
                    cprint("Default Gateway Exception : {0}".format(e), 'red')
                    pass
            elif option == 'name-server':
                try:
                    value = cmd_str[1]
                    try:
                        ipaddress.ip_address(value)
                    except ValueError:
                        cprint(f"The entered value type of {value} is invalid  ", "red")
                        return

                    with open('/etc/resolv.conf', 'w') as fd:
                        fd.write('nameserver {0}'.format(value))
                    cprint("OK", 'yellow')
                except Exception as e:
                    cprint("Nameserver Exception : {0}".format(e), 'red')
                    pass
            else:
                cprint("Failed", 'red')
        else:
            self.help_ip()

    def help_netstat(self):
        print_help_msg("Print Currently Open Port Information and Listen Information",
                       usage=["(system)# netstat"],
                       filter_opt=["grep", "exclude"])

    def do_netstat(self, args):
        AD = "-"

        cmd_str, cmd_len, l_filter = self.cmd_parse(args)
        AF_INET6 = getattr(socket, 'AF_INET6', object())
        proto_map = {
            (socket.AF_INET, socket.SOCK_STREAM): 'tcp',
            (AF_INET6, socket.SOCK_STREAM): 'tcp6',
            (socket.AF_INET, socket.SOCK_DGRAM): 'udp',
            (AF_INET6, socket.SOCK_DGRAM): 'udp6',
        }
        templ = "%-5s %-30s %-30s %-13s %-6s %s"

        cprint(templ % ("Proto", "Local address", "Remote address", "Status", "PID", "Program name"), color='green')
        proc_names = {}
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            process_name = " ".join(p.cmdline())
            proc_names[p.info['pid']] = process_name

        for c in psutil.net_connections(kind='inet'):
            laddr = "%s:%s" % (c.laddr)
            raddr = ""
            if c.raddr:
                raddr = "%s:%s" % (c.raddr)

            name = proc_names.get(c.pid, '?') or ''
            if name in 'sshd':
                continue

            line = templ % (
                proto_map[(c.family, c.type)],
                laddr,
                raddr or AD,
                c.status,
                c.pid or AD,
                name,
                )

            # 전체 라인 필터링
            if self.filter(line, l_filter):
                continue

            print(line)

    def help_traceroute(self):
        print_help_msg("Show Destination Packet Route Info",
                       usage=["(system)# traceroute {host}"],
                       options_args=["host: Hostname or IP-Address"])

    def do_traceroute(self, args):
        """
            traceroute
        """
        from command_center.command.system.tool.traceroute import echo_three

        cmd_str, cmd_len, _ = self.cmd_parse(args)

        if cmd_len != 1:
            self.help_traceroute()
            return

        try:
            host = socket.gethostbyname(cmd_str[0])
            timeout = 3
            max_tries = 20

            cprint('TraceRoute to ' + cmd_str[0] + ' (' + host + '), ' + str(max_tries) + ' hops max.', 'green')

            try:
                # Loop until we hit the maximum number of hops, or until we reach the
                # final destination host:
                for x in range(1, max_tries + 1):
                    (line, destination_reached) = echo_three(host, x, timeout)
                    print(line)
                    if destination_reached:
                        break
            except Exception as err:
                cprint("TraceRoute Error : {0}".format(err), 'red')
            except KeyboardInterrupt as ke:
                pass
        except socket.gaierror as e:
            cprint('Name or Service not known : {0}'.format(cmd_str[0]), 'red')

    def monitor_interface_io(self, cmd_str, l_filter):
        """
            Network 사용량 모니터링
        """
        class NetworkPerformance(NBBScreenMixin):

            def datas(self,interval):
                tot_before = psutil.net_io_counters()
                pnic_before = psutil.net_io_counters(pernic=True)
                time.sleep(interval)
                tot_after = psutil.net_io_counters()
                pnic_after = psutil.net_io_counters(pernic=True)
                return (tot_before, tot_after, pnic_before, pnic_after)

            def refresh_window(self, tot_before, tot_after, pnic_before, pnic_after):

                # totals
                self.print_line("total bytes:           sent: %-10s   received: %s" % ( convert_size(tot_after.bytes_sent),
                                                                                           convert_size(tot_after.bytes_recv)) )
                self.print_line("total packets:         sent: %-10s   received: %s" % (tot_after.packets_sent,
                                                                                            tot_after.packets_recv))

                # per-network interface details: let's sort network interfaces so
                # that the ones which generated more traffic are shown first
                self.print_line( "")
                nic_names = list(pnic_after.keys())
                nic_names.sort(key=lambda x: sum(pnic_after[x]), reverse=True)

                for index, name in enumerate(nic_names):
                    if name in ('lo','lo0'):
                        continue

                    stats_before = pnic_before[name]
                    stats_after = pnic_after[name]
                    templ = "%-15s %15s %15s"
                    self.print_line(templ % (name, "TOTAL", "PER-SEC"), highlight=True)
                    self.print_line(templ % (
                        "bytes-sent",
                        convert_size(stats_after.bytes_sent),
                        convert_size(
                            stats_after.bytes_sent - stats_before.bytes_sent) + '/s',
                    ))
                    self.print_line(templ % (
                        "bytes-recv",
                        convert_size(stats_after.bytes_recv),
                        convert_size(
                            stats_after.bytes_recv - stats_before.bytes_recv) + '/s',
                    ))
                    self.print_line(templ % (
                        "pkts-sent",
                        stats_after.packets_sent,
                        stats_after.packets_sent - stats_before.packets_sent,
                    ))
                    self.print_line(templ % (
                        "pkts-recv",
                        stats_after.packets_recv,
                        stats_after.packets_recv - stats_before.packets_recv,
                    ))
                    self.print_line("")
                    if self.lineno < (self.height-4):
                        break
                self.lineno = 1
        try:
            curses.wrapper(NetworkPerformance().initscreen, title="Network Traffic Monitoring")
        except (KeyboardInterrupt, SystemExit):
            pass

