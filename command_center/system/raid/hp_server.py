#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import datetime
import logging
from oslo_utils import strutils
from proliantutils.hpssa import objects

from command_center.library.AppConfig import gconfig
from command_center import library as db

logger = logging.getLogger(__name__)

"""
hpssacli ctrl all show config -> disk정보 및 raid 구성

hpssacli ctrl all show status -> controller 및 cache의 상태

hpssacli ctrl all show detail -> controller의 모든 상태정보
"""


class HPRaidManager(object):
    def __init__(self, extract_data=False, conn=None):
        self.server_id = gconfig.server_id
        self.hp = objects.Server()
        self.server_prod = gconfig.server_model['manufacturer'].strip()[:16]
        self.now = datetime.datetime.now()
        self.conn = conn

        self.pd_data = self.__get_pd()
        self.ld_data = self.__get_ld()

        if extract_data is False:
            self.__upsert_raid_info_pd()
            self.__upsert_raid_info_ld()

    def __int_value(self, value):
        try:
            return int(value)
        except TypeError:
            return 0

    def __get_pd(self):
        pd_data = self.hp.get_physical_drives()
        data = []

        for pd in pd_data:
            # pd_dict = pd.get_physical_drive_dict()
            state = pd.properties.get('Status').lower()
            if state != 'ok':
                logger.error(f'[RAID HP Physical Drive] status is not ok: {state}')
                state = 'failed'

            if isinstance(pd.parent, objects.RaidArray):
                array = pd.parent.id
                controller = pd.parent.parent.properties.get('Slot')
                # status = 'active'
            else:
                array = 'unassigned'
                controller = pd.parent.properties.get('Slot', 0)    # TODO: unassigned 샘플 데이터가 없어서 확실하지 않음
                # status = 'ready'

            pd_dict = {
                'adapter_id': controller,
                'array': array,
                'device_id': pd.id,
                'port': pd.properties.get('Port'),
                'box': pd.properties.get('Box'),
                'bay': pd.properties.get('Bay'),
                'firmware_state': None,
                'disk_type': pd.disk_type,
                'media_type': pd.interface_type,
                'capacity': strutils.string_to_bytes(pd.properties['Size'].replace(' ', ''), return_int=True),
                'disk_state': state,
                # 'PHY Transfer Rate' = '6.0Gbps' => string_to_bytes() 에 의해 bit 단위로 계산되므로 byte(* 8)로 변환
                'device_speed': strutils.string_to_bytes(pd.properties.get('PHY Transfer Rate').split(',')[0][:-2], return_int=True) * 8,
                'bbu_type': None,
                'bbu_status': None,
            }
            data.append(pd_dict)
        return data

    def __get_ld(self):
        ld_data = self.hp.get_logical_drives()
        data = []
        pattern = re.compile('(/\w*) ([\d\.]+) (\w+) Partition Number (\d+)')

        for ld in ld_data:
            # ld_dict = ld.get_logical_drive_dict()
            state = ld.properties.get('Status').lower()
            if state != 'ok':
                logger.error(f'[RAID HP Logical Drive] status is not ok: {state}')
                state = 'failed'

            mount_points = ld.properties.get('Mount Points')
            mounts = pattern.findall(mount_points)
            for mount_info in mounts:
                (mount, size, size_unit, partition_num) = mount_info
                ld_dict = {
                    'adapter_id': ld.parent.parent.properties.get('Slot'),
                    'array': ld.parent.id,
                    'vd_id': ld.id,
                    'disk_name': ld.properties.get('Disk Name'),
                    'mount_name': mount,
                    'size': strutils.string_to_bytes(size+size_unit, return_int=True),
                    'state': state,
                    'raid_level': ld.raid_level,
                    'default_cache_policy': None,
                    'current_cache_policy': None,
                    'default_access_policy': None,
                    'current_access_policy': None,
                    'disk_cache_policy': ld.properties.get('Caching').lower(),
                }
                data.append(ld_dict)
        return data

    def __upsert_raid_info_pd(self):
        for pd in self.pd_data:
            pd['server_product'] = self.server_prod
            pd['server_id'] = self.server_id
            pd['reg_date'] = self.now
            # pd['capacity'] = int(strutils.string_to_bytes(f'{pd["capacity"]}B', return_int=True) / (1024 * 1024 * 1024))

            query = """
                INSERT INTO server_raidinfo_physical as pd
                (adapter_id, "array", device_id, port, box, bay, disk_type, media_type, capacity, disk_state, device_speed, server_product, server_id, reg_date) VALUES 
                ('{adapter_id}', '{array}', '{device_id}', '{port}', {box}, {bay}, '{disk_type}', '{media_type}', {capacity}, '{disk_state}', {device_speed}, '{server_product}', {server_id}, '{reg_date}') 
                ON CONFLICT (adapter_id, device_id, bay, server_id)
                DO UPDATE SET 
                    adapter_id = excluded.adapter_id,
                    "array" = excluded."array",
                    device_id = excluded.device_id,
                    port = excluded.port,
                    box = excluded.box,
                    bay = excluded.bay,
                    disk_type = excluded.disk_type,
                    media_type = excluded.media_type,
                    capacity = excluded.capacity,
                    disk_state = excluded.disk_state,
                    device_speed = excluded.device_speed,
                    server_product = excluded.server_product,
                    server_id = excluded.server_id,
                    reg_date = excluded.reg_date
                ;""".format(**pd)
            if self.conn:
                self.conn.execute(query)
            else:
                db.pmdatabase.execute(query)

    def __upsert_raid_info_ld(self):
        for ld in self.ld_data:
            ld['server_product'] = self.server_prod
            ld['server_id'] = self.server_id
            ld['reg_date'] = self.now
            # ld['size'] = strutils.string_to_bytes(f'{ld["size"]}GB', return_int=True)

            query = """
                INSERT INTO server_raidinfo_logical as ld
                (adapter_id, "array", vd_id, disk_name, "mount_name", "size", state, raid_level, disk_cache_policy, server_product, server_id, reg_date) VALUES 
                ({adapter_id}, '{array}', {vd_id}, '{disk_name}', '{mount_name}', {size}, '{state}', '{raid_level}', '{disk_cache_policy}', '{server_product}', {server_id}, '{reg_date}') 
                ON CONFLICT (adapter_id, vd_id, "mount_name", server_id)
                DO UPDATE SET 
                    adapter_id = excluded.adapter_id,
                    "array" = excluded."array",
                    vd_id = excluded.vd_id,
                    disk_name = excluded.disk_name,
                    "mount_name" = excluded."mount_name",
                    "size" = excluded."size",
                    state = excluded.state,
                    raid_level = excluded.raid_level,
                    disk_cache_policy = excluded.disk_cache_policy,
                    server_product = excluded.server_product,
                    server_id = excluded.server_id,
                    reg_date = excluded.reg_date
                ;""".format(**ld)

            if self.conn:
                self.conn.execute(query)
            else:
                db.pmdatabase.execute(query)