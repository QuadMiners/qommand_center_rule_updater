#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import logging
import time
import asyncio
import re
import subprocess
import psutil
import cpuinfo

from pcapbox_app.system.hardware.memory import get_memory_info
from pcapbox_app.system.hardware_manager import HardwareManager
from pcapbox_app.system.raid import HPRaidManager, MegaRaidManager, DellManager
from pcapbox_library.AppConfig import gconfig
from pcapbox_library.AppInterface import SchedulerThreadInterface
from pcapbox_library.AppObject import QObject
from pcapbox_library.database import DBException,  FPgsql

from pcapbox_app.system import EHardwareInfo
from pcapbox_app.system.performance_manager import PerformanceManager
from pcapbox_app.system.ntp_manager import NTPManager

logger = logging.getLogger(__name__)


class DMIDecode:
    """Wrapper over DMIParse which runs dmidecode locally"""

    handle_re = re.compile("^Handle\\s+(.+),\\s+DMI\\s+type\\s+(\\d+),\\s+(\\d+)\\s+bytes$")
    in_block_re = re.compile("^\\t\\t(.+)$")
    record_re = re.compile("\\t(.+):\\s+(.+)$")
    record2_re = re.compile("\\t(.+):$")

    def __init__(self, command):
        self.dmidecode = command

    def dmidecode_parse(self, buffer):  # noqa: C901
        data = {}
        #  Each record is separated by double newlines
        split_output = buffer.split("\n\n")

        for record in split_output:
            record_element = record.splitlines()

            #  Entries with less than 3 lines are incomplete / inactive
            #  skip them
            if len(record_element) < 3:
                continue

            handle_data = DMIDecode.handle_re.findall(record_element[0])

            if not handle_data:
                continue
            handle_data = handle_data[0]

            dmi_handle = handle_data[0]

            data[dmi_handle] = {}
            data[dmi_handle]["DMIType"] = int(handle_data[1])
            data[dmi_handle]["DMISize"] = int(handle_data[2])

            #  Okay, we know 2nd line == name
            data[dmi_handle]["DMIName"] = record_element[1]

            in_block_elemet = ""
            in_block_list = ""

            #  Loop over the rest of the record, gathering values
            for i in range(2, len(record_element), 1):
                if i >= len(record_element):
                    break
                #  Check whether we are inside a \t\t block
                if in_block_elemet != "":

                    in_block_data = self.in_block_re.findall(record_element[1])

                    if in_block_data:
                        if not in_block_list:
                            in_block_list = in_block_data[0][0]
                        else:
                            in_block_list = in_block_list + "\t\t"
                            +in_block_data[0][1]

                        data[dmi_handle][in_block_elemet] = in_block_list
                        continue
                    else:
                        # We are out of the \t\t block; reset it again, and let
                        # the parsing continue
                        in_block_elemet = ""

                record_data = DMIDecode.record_re.findall(record_element[i])

                #  Is this the line containing handle identifier, type, size?
                if record_data:
                    data[dmi_handle][record_data[0][0]] = record_data[0][1]
                    continue

                #  Didn't findall regular entry, maybe an array of data?
                record_data2 = DMIDecode.record2_re.findall(record_element[i])

                if record_data2:
                    #  This is an array of data - let the loop know we are
                    #  inside an array block
                    in_block_elemet = record_data2[0][0]
                    continue
        return data

    def run_command(self):
        # let subprocess merge stderr with stdout
        proc = subprocess.Popen(self.dmidecode, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode > 0:
            raise RuntimeError("{} failed with an error:\n{}".format(self.dmidecode, stdout.decode()))
        else:
            return self.dmidecode_parse(stdout.decode())


def upsert_hardware_info(type, obj):
    try:
        str_query="INSERT INTO hardware_information as hw (server_id, type, info, last_date) VALUES ({0}, '{1}', '{2}', now()) " \
                    "ON CONFLICT (server_id,type)" \
                    "DO UPDATE SET info ='{2}', last_date =now() WHERE hw.type='{1}';".format( gconfig.server_id, type, str(obj))

        instance = FPgsql(gconfig.database_config)
        instance.execute(str_query)
    except DBException as e:
        logger.error("Error (Insert_HW_Info_Table) [%s] " % e)


async def load_cpu():
    info_datas = cpuinfo.get_cpu_info()
    cpu = QObject()
    cpu["cpu_model"] = info_datas.get("brand", info_datas.get('brand_raw', None))
    cpu["socket_cnt"] = -1
    cpu["cache"] = info_datas["l2_cache_size"]
    cpu["process_cnt"] = psutil.cpu_count()
    cpu["thread_cnt"] = int(psutil.cpu_count() / psutil.cpu_count(logical=True))

    upsert_hardware_info(EHardwareInfo.cpu.value, cpu)

    return cpu


def load_memory():
    memory = QObject()
    memory["memory_total"] = psutil.virtual_memory().total
    memory["swap_total"] = psutil.swap_memory().total
    memory['slot'] = []
    memory_info = get_memory_info()
    for info in memory_info['bank_info_list']:
        info_split = info.split()
        hw_path = info_split[0].split("/")[-1]
        description = " ".join(info_split[2:])
        memory['slot'].append(dict(number=hw_path, info=description))
    upsert_hardware_info(EHardwareInfo.memory.value, memory)
    return memory


def load_disk():
    disk = QObject()

    for partition in psutil.disk_partitions(all=False):
        if 'boot' in partition.mountpoint:
            continue

        disk_use = psutil.disk_usage(partition.mountpoint)

        disk[partition.mountpoint] = dict(device=partition.device,
                                          mountpoint=partition.mountpoint,
                                          fstype=partition.fstype,
                                          partition_size=disk_use.total)
    upsert_hardware_info(EHardwareInfo.disk.value, disk)

    instance = FPgsql(gconfig.database_config)
    if os.path.exists('/usr/sbin/ssacli'):
        HPRaidManager(conn=instance)
    elif os.path.exists('/opt/MegaRAID/perccli/perccli64'):
        DellManager(conn=instance)
    else:
        MegaRaidManager(conn=instance)

    return disk


def load_network():
    network = QObject()

    net_info_list = psutil.net_if_addrs()
    net_stat_list = psutil.net_if_stats()

    for net_if_name in net_info_list.keys():

        network[net_if_name] = dict()
        snic_list = net_info_list[net_if_name]

        for snic_instance in snic_list:
            if snic_instance.family == 2:
                network[net_if_name]["ipaddr"] = snic_instance.address
                network[net_if_name]["netmask"] = snic_instance.netmask
                network[net_if_name]["broadcast"] = snic_instance.broadcast
            elif snic_instance.family == 17:
                network[net_if_name]["mac"] = snic_instance.address
        # stats
        snic_stat = net_stat_list[net_if_name]
        network[net_if_name]['isup'] = 'Yes' if snic_stat.isup else 'No'
        network[net_if_name]['duplex'] = {1: 'half', 2: 'full'}.get(snic_stat.duplex.value, 'unknown')
        network[net_if_name]['speed'] = snic_stat.speed
        network[net_if_name]['mtu'] = snic_stat.mtu

    upsert_hardware_info(EHardwareInfo.network.value, network)
    return network


class HardwarePerformanceManager(SchedulerThreadInterface):

    def hw_performance_schedule(self):

        def realtime(data):
            try:
                data.load_performance_swap()
                data.load_performance_memory()
                data.load_performance_cpu()
            except Exception as e:
                logger.error("Realtime Performance Exception {0}".format(e))

        def disk(data):
            try:
                data.load_performance_disk()
            except Exception as e:
                logger.error("Realtime Disk Performance Exception {0}".format(e))

        h_m = PerformanceManager()
        self.scheduler.every(10).seconds.do(realtime, data=h_m)
        self.scheduler.every().minutes.do(disk, data=h_m)

    def ntp_schedule(self):

        def ntpupdate(data):
            try:
                data.process()
            except Exception as e:
                logger.error("NTP Update Exception : {0}".format(e))

        ntp = NTPManager()
        self.scheduler.every().day.at("03:00").do(ntpupdate, data=ntp)
        logger.info("NTP reg schedule")

    def run(self):

        self.hw_performance_schedule()
        self.ntp_schedule()
        logger.info("Hardware Performance Run Start")
        while self._exit is False:
            self.run_queue()
            self.scheduler.run_pending()
            time.sleep(1)
        logger.info("Hardware Performance Run Close")
