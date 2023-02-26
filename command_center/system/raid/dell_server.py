# !/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import re
from megacli import MegaCLI
from command_center.library.AppConfig import gconfig
from command_center import library as db

logger = logging.getLogger(__name__)


class DellManager(object):
    progress_regex = re.compile("(?P<progress>\d+)%")

    def __init__(self, extract_data=False, conn=None):
        self.server_id = gconfig.server_id
        self.mega = MegaCLI(cli_path='/opt/MegaRAID/perccli/perccli64')
        self.server_prod = gconfig.server_model['manufacturer'].strip()[:16]    # DB에서 해당 필드값의 길이가 varchar(16)
        self.now = datetime.datetime.now()
        self.conn = conn

        try:
            self.pd_data = self.__get_pd()
            self.ld_data = self.__get_ld()

            if extract_data is False:
                self.__upsert_raid_info_pd()
                self.__upsert_raid_info_ld()
        except Exception as er:
            logger.error("Dell Raid Check Exception  | {0}".format(er))

    def __int_value(self, value):
        # port_linkspeed가 "unknown"인 경우가 있었음
        if isinstance(value, str) or value is None:
            return 0
        else:
            return int(value)

    def __get_disk_name(self, vid):
        import subprocess
        command = f'ls -l /dev/disk/by-path/ | grep -E "scsi-[0-9]:[0-9]:{vid}:[0-9] "'
        ret = None
        try:
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = p.communicate()

            if error != b'':
                logger.error("[RAID Dell Physical Drive] Get Device Name Excute Error msg | {}".format(error))

            ret = output.decode('utf-8').strip().split(' ')[-1].replace('../../', '/dev/')

        except OSError as e:
            logger.error("[RAID Dell Physical Drive] Get Device Name Export OSError | {}".format(e))

        except subprocess.SubprocessError as e:
            logger.error("[RAID Dell Physical Drive] Get Device Name Subprocess Error | {}".format(e))

        return ret

    def __get_pd(self):
        pd_data = self.mega.physicaldrives()
        try:
            bbu_data = self.mega.bbu()
        except:
            bbu_data = None
        data = []

        for pd in pd_data:
            bbu = None
            if bbu_data:
                bbu = list(filter(lambda b: b['adapter_id'] == pd['adapter_id'], bbu_data))[0]
            state = pd['port_status'].lower()
            firmware_state = pd['firmware_state'].lower()
            enclosure_id = pd['enclosure_id']
            slot_number = pd['slot_number']
            adapter_id = pd['adapter_id']

            if state == 'active':
                state = 'ok'  # 정상 상태일 때 state = OK
            else:
                logger.error(f'[RAID Dell Physical Drive] status is not ok: {state}')
                if state == 'degraded':
                    state = 'failed'

            if pd['media_type'] == 'hard disk device':
                media_type = 'hdd'
            else:
                media_type = 'ssd'

            # rebuild 중이면
            if firmware_state == 'rebuild':
                progress = self.__get_rebuild_progress(enclosure_id, slot_number, adapter_id)

                # 진행도를 읽어오지 못했을 경우 '?'로 처리
                if not progress:
                    progress = '?'


                # formatting
                firmware_state += ' ({}%)'.format(progress)
            # 이전 상태가 rebuild였다면 92003 history를 남김
            elif firmware_state.startswith('online'):
                get_prev_state_query = """
                    select id
                    from server_raidinfo_physical 
                    where firmware_state like 'rebuild%'
                        and device_id = '{0}' and adapter_id = {1} and bay = {2} and server_id = {3}
                """.format(pd['device_id'], adapter_id, slot_number, self.server_id)

                result = []

                if self.conn:
                    result = self.conn.execute(get_prev_state_query, returning_id=True, ret_list=True)
                else:
                    result = db.pmdatabase.execute(get_prev_state_query, returning_id=True, ret_list=True)

            data.append({
                'adapter_id': adapter_id,
                'array': None,
                'device_id': pd['device_id'],
                'port': None,
                'box': None,
                'bay': slot_number,
                'firmware_state': firmware_state,
                'disk_type': pd['pd_type'],
                'media_type': media_type,
                'capacity': int(pd["raw_size"]),
                'disk_state': state,
                'device_speed': self.__int_value(pd['device_speed']),
                'bbu_type': bbu['batterytype'] if bbu else None,
                'bbu_status': bbu['battery_state'].lower() if bbu else None,
            })
        return data

    def __get_ld(self):
        ld_data = self.mega.logicaldrives()
        data = []

        for ld in ld_data:
            state = ld['state'].lower()

            if state == 'optimal':
                state = 'ok'  # 정상 상태일 때 state = OK
            else:
                logger.error(f'[RAID Dell Logical Drive] status is not ok: {state}')
                # state = 'failed'

            data.append({
                'adapter_id': ld.get('adapter_id', '-'),
                'array': None,
                'vd_id': str(ld['id']),
                'disk_name': self.__get_disk_name(ld['id']),
                'mount_name': '/' + ld.get('name', ''),
                'size': int(ld["size"]),
                'state': state,
                'raid_level': str(ld['raid_level']),
                # 'number_of_drives': ld['number_of_drives'],
                'default_cache_policy': ld['default_cache_policy'],
                'current_cache_policy': ld['current_cache_policy'],
                'default_access_policy': ld['default_access_policy'],
                'current_access_policy': ld['current_access_policy'],
                'disk_cache_policy': ld['disk_cache_policy'].replace("'", ""),
            })
        return data

    def __upsert_raid_info_pd(self):
        for pd in self.pd_data:
            pd['server_product'] = self.server_prod
            pd['server_id'] = self.server_id
            pd['reg_date'] = self.now
            # pd['capacity'] = int(strutils.string_to_bytes(f'{pd["capacity"]}B', return_int=True) / (1024 * 1024 * 1024))

            query = """
                INSERT INTO server_raidinfo_physical as pd
                (adapter_id, device_id, bay, firmware_state, disk_type, media_type, capacity, disk_state, device_speed, bbu_type, bbu_status, server_product, server_id, reg_date) VALUES 
                ('{adapter_id}', '{device_id}', {bay}, '{firmware_state}', '{disk_type}', '{media_type}', {capacity}, '{disk_state}', {device_speed}, '{bbu_type}', '{bbu_status}', '{server_product}', {server_id}, '{reg_date}') 
                ON CONFLICT (adapter_id, device_id, bay, server_id)
                DO UPDATE SET 
                    adapter_id = excluded.adapter_id,
                    device_id = excluded.device_id,
                    bay = excluded.bay,
                    firmware_state = excluded.firmware_state,
                    disk_type = excluded.disk_type,
                    media_type = excluded.media_type,
                    capacity = excluded.capacity,
                    disk_state = excluded.disk_state,
                    device_speed = excluded.device_speed,
                    bbu_type = excluded.bbu_type,
                    bbu_status = excluded.bbu_status,
                    server_product = excluded.server_product,
                    server_id = excluded.server_id,
                    reg_date = excluded.reg_date
                ;""".format(**pd)

            if self.conn:
                self.conn.execute(query)
            else:
                db.pmdatabase.execute(query)

                if pd['disk_state'] != 'ok' or (pd['bbu_status'] and pd['bbu_status'] == 'degraded') or pd['firmware_state'] == 'failed':
                    self.history_error(92000, **dict(server_id=gconfig.server_id, disk=f'physical drive {pd["device_id"]}', status=f'{pd["disk_state"]}(battery: {pd["bbu_status"]}, firmware: {pd["firmware_state"]})'))

    def __upsert_raid_info_ld(self):
        for ld in self.ld_data:
            ld['server_product'] = self.server_prod
            ld['server_id'] = self.server_id
            ld['reg_date'] = self.now
            # ld['size'] = int(strutils.string_to_bytes(f'{ld["size"]}B', return_int=True) / (1024 * 1024 * 1024))

            query = """
                INSERT INTO server_raidinfo_logical as ld
                (adapter_id, vd_id, disk_name, "mount_name", "size", state, raid_level, default_cache_policy, current_cache_policy, default_access_policy, current_access_policy, disk_cache_policy, server_product, server_id, reg_date) VALUES 
                ({adapter_id}, {vd_id}, '{disk_name}', '{mount_name}', {size}, '{state}', '{raid_level}', '{default_cache_policy}', '{current_cache_policy}', '{default_access_policy}', '{current_access_policy}', '{disk_cache_policy}', '{server_product}', {server_id}, '{reg_date}') 
                ON CONFLICT (adapter_id, vd_id, mount_name, server_id)
                DO UPDATE SET 
                    adapter_id = excluded.adapter_id,
                    vd_id = excluded.vd_id,
                    disk_name = excluded.disk_name,
                    "mount_name" = excluded."mount_name",
                    "size" = excluded."size",
                    state = excluded.state,
                    raid_level = excluded.raid_level,
                    default_cache_policy = excluded.default_cache_policy,
                    current_cache_policy = excluded.current_cache_policy,
                    default_access_policy = excluded.default_access_policy,
                    current_access_policy = excluded.current_access_policy,
                    disk_cache_policy = excluded.disk_cache_policy,
                    server_product = excluded.server_product,
                    server_id = excluded.server_id,
                    reg_date = excluded.reg_date
                ;""".format(**ld)

            if self.conn:
                self.conn.execute(query)
            else:
                db.pmdatabase.execute(query)

                if ld['state'] != 'ok':
                    self.history_error(92000, **dict(server_id=gconfig.server_id, disk=f'logical drive {ld["vd_id"]}', status=ld['state']))

    def __get_rebuild_progress(self, enclosure_id, slot_number, adapter_id):
        cmd = "-PDRbld -ShowProg -PhysDrv[{enclosure}:{slot}] -a{adapter}"
        
        result = "\n".join(self.mega.execute(cmd.format(
                                            enclosure=enclosure_id,
                                            slot=slot_number,
                                            adapter=adapter_id
                                            )))

        search = self.progress_regex.search(result) # get rebuilding progress in result

        if search:
            # get progress
            progress = search.groupdict()['progress']
            return progress
        else:
            logger.error("can't get rebuilding progress / disk info : [{0}:{1}]".format(enclosure_id, slot_number))
            return False


if __name__ == '__main__':
    import pcapbox_library.database as db

    db.global_db_connect()

    a = DellManager(extract_data=True)
