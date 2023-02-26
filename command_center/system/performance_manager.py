#!/usr/bin/env python
# -*- coding: utf-8 -*-
import psutil

from command_center.library.AppConfig import gconfig
from command_center import library as db


class PerformanceManager(object):

    def load_performance_swap(self):
        swap = psutil.swap_memory()
        query = """INSERT INTO memory_performance (date, server_id, type, total, used, free, cached, user_per) 
                            VALUES (now(), {0}, '{1}', {2}, {3}, {4}, {5},{6})""".format(gconfig.server_id, 1, swap.total, swap.used, swap.free, 0, swap.percent)

        db.pmdatabase.execute(query)
        del swap

    def load_performance_memory(self):
        memory = psutil.virtual_memory()
        query = """INSERT INTO memory_performance (date, server_id, type, total, used, free, cached, user_per) 
                            VALUES (now(), {0}, '{1}', {2}, {3}, {4}, {5},{6})""".format(gconfig.server_id, 0 , memory.total, memory.used, memory.free, memory.cached, memory.percent)

        db.pmdatabase.execute(query)
        del memory

    def load_performance_cpu(self):
        cpu = psutil.cpu_times_percent(percpu=False)
        query = """INSERT INTO cpu_performance (date, server_id, "user", system, idle, iowait) 
                            VALUES (now(), {0}, {1}, {2}, {3}, {4})""".format(gconfig.server_id, cpu.user, cpu.system, cpu.idle, cpu.iowait)

        db.pmdatabase.execute(query)
        del cpu

    def load_performance_disk(self):
        """
        """
        query = """INSERT INTO disk_performance (date, server_id, partition, total, used, free, user_per) 
                            VALUES (now(), {0}, '{1}', {2}, {3}, {4},{5})
                """
        for disk in psutil.disk_partitions():
            if disk.mountpoint not in ('/boot', '/boot/efi'):
                obj = psutil.disk_usage(disk.mountpoint)
                r_query = query.format(gconfig.server_id, disk.mountpoint, obj.total, obj.used, obj.free, obj.percent)
                db.pmdatabase.execute(r_query)

