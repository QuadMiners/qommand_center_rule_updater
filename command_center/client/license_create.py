#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import json
import os
import shlex
import subprocess
import shutil

license_value = """
#################################################
## QuadMiners License Config ##
#################################################
# DPI Rule : Company Code _ Device Type _ Number

Creator Name :	 {user_name}
Site Name :		{site_name}
HW KEY :		{hardware_key}
MACHINE ID :       {machine_id}
# HW 정보 설정
SERVER ID :		{server_id}
MODEL :			{model}
SERVER TYPE :	{server_type}

# Server  TYPE
#	allinone : All-In-One
#	manager : Manager
#	managernode : ManagerNode
#	node : Node
#	nodesensor : NodeSensor
#	sensor : Sensor
#	control : Control


# License Type
# POC : POC License (No Tech Support and Update)
# BMT : BMT License (No Tech Support and Update)
# Product : 운영라이센스

License Type :      {license_type}
License Version :	{license_version}

Start Day :			{start_date}
End Day :			{end_date}



HDD Total : {hdd}
# Store 사이즈 : 단위 TB

BPS Type : {bps}

"""


# 124a125e75ae4eadb07361ef034b3aa6
# 4c4c4544-004b-4b10-804e-b1c04f594258

def convert_surfix_to_byte(num, surfix="B", convert_type="TB"):
    # 기본 B -> TB 변환
    surfix = surfix.upper()
    type_dict = {
        "TB": (1024 ** 4),
        "GB": (1024 ** 3),
        "MB": (1024 ** 2),
        "KB": (1024 ** 1),
        "B": 1,
    }
    return (num * type_dict[surfix]) / type_dict[convert_type]


class CreateLicense(object):
    license_file = None
    def __init__(self, v_dict):
        if v_dict['server_type'] in ('allinone', 'control'):
            v_dict['model'] = v_dict['server_type']
        else:
            v_dict['model'] = 'expand'

        format_dict = dict()
        format_dict['user_name'] = v_dict['user_name']
        format_dict['site_name'] = v_dict['site_name']
        format_dict['model'] = v_dict['model']
        format_dict['server_id'] = v_dict['server_id']
        format_dict['server_type'] = v_dict['server_type']
        format_dict['license_type'] = v_dict['license_type']
        format_dict['license_version'] = v_dict['license_version']
        format_dict['start_date'] = v_dict['start_date']
        format_dict['end_date'] = v_dict['end_date']

        format_dict['hardware_key'] = v_dict['hardware_info']['hardware_key']
        format_dict['machine_id'] = v_dict['hardware_info']['machine_id']
        format_dict['hdd'] = v_dict['hardware_info']['hdd']
        format_dict['bps'] = v_dict['hardware_info']['bps']
        print(format_dict)
        value = license_value.format(**format_dict)

        self.conf_file = self.get_file_name(v_dict)
        self._create_config_file(v_dict, value)
        self.license_file_create(v_dict)

    def filename_buffer(self):
        buffer =  None
        with open(self.license_file, "r") as fd:
            buffer = base64.b64encode(fd.read().encode('utf-'))
        return buffer

    def _create_config_file(self, v_dict, value):
        with open(self.get_file_name(v_dict), "wb") as fd:
            fd.write(value.encode('utf-8'))

    def get_file_name(self, v_dict):
        return "/data/license/{0}.conf".format(v_dict['server_id'])

    def license_file_name(self, v_dict):
        try:
            os.mkdir("/data/license/{0}".format(v_dict['site_code']))
        except Exception:
            pass
        self.license_file = "/data/license/{0}/{1}.license".format(v_dict['site_code'], v_dict['server_id'])

        return "/data/license/{0}/{1}.license".format(v_dict['site_code'], v_dict['server_id'])

    def license_file_create(self, v_dict):
        print("/opt/command_center/bin/nbb_licensegenerator -f {0} -k /opt/command_center/pam/license_private_unencrypted.pem -o {1} > /dev/null 2>&1".format(self.get_file_name(v_dict), self.license_file_name(v_dict)))
        args = shlex.split("/opt/command_center/bin/nbb_licensegenerator -f {0} -k /opt/command_center/pam/license_private_unencrypted.pem -o {1} > /dev/null 2>&1".format(
                self.get_file_name(v_dict), self.license_file_name(v_dict)))
        try:
            p = subprocess.Popen(args)
            p_status = p.wait()
        except OSError as e:
            print("Export OSError FileName >> {0} ".format(e))
        except subprocess.SubprocessError as e:
            print("Export SubProcessError  FileName >> {0} ".format(e))

    def __del__(self):
        os.remove(self.conf_file)