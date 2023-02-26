import unittest
import uuid

import command_center.library.database as db


sid = None
class TestCaseMixin(unittest.TestCase):
    def insert_site(self):
        query = """
            INSERT INTO site (name , code, address, tel, update_server_status ,delete, created_user_id)
                VALUES('Coway', 'coway', '-', '-',  False, False, 1)
                ON CONFLICT (code) DO UPDATE set delete = False
                RETURNING id
            """
        site_id = db.pmdatabase.execute(query, returning_id=True)
        self.insert_server(site_id)

    def insert_server(self, site_id):
        query = """
            INSERT INTO site_server_info (server_id,  site_id, type, name, hostname, ipaddr, version, os_ver, reg_user_id, reg_date, delete_flag, ssh_connection_info ,bps, hardware_uuid, machine_id, server_roll_type)
                VALUES(1000, {0}, 'allinone', '코웨이 Allinone', 'host', '192.168.30.20', 'nbb3.3.5', 'redhat8.4', 2, now(), 'N', '', 1, '{1}', '{2}', 'nbb')
                ON CONFLICT (hardware_uuid, machine_id, site_id)  DO  UPDATE set server_roll_type = 'nbb'
                RETURNING id
            """.format(site_id, '03000200-0400-0500-0006-000700080009', '35ba7a676fd149868bf8447d1ca4c3c7')
        print(query)
        global sid
        sid = db.pmdatabase.execute(query, returning_id=True)

    def insert_license(self, data_dict, license_raw):
        db.pmdatabase.execute("delete from site_server_license")
        global sid
        query = """
            INSERT INTO site_server_license (server_info_id, name, type, version, uuid,start_date, end_date, raw, reg_user_id, auto_update, expire, update_server_status )
            VALUES({sid}, '{name}', '{type}', '{version}','{uuid}','{start_date}', '{end_date}', '{raw}', 2, False, False, False)
            """.format(**dict(sid=sid,name='coway', uuid=str(uuid.uuid4()), type='poc', version='1.1', start_date='2022-01-01', end_date='2023-01-23', raw=license_raw.decode('utf-8')))
        print(query)

        db.pmdatabase.execute(query)
        query = """
            update site_license_approve SET approve_type='confirm', approval_user_id = 2, approval_time = now()
        """
        db.pmdatabase.execute(query)

    def delete_server(self):
        db.pmdatabase.execute('truncate table site_license_approve cascade')
        db.pmdatabase.execute('truncate table site_server_info cascade')
        db.pmdatabase.execute('truncate table site cascade')
