import unittest

from command_center.client.license import LicenseClientMixin
from command_center.client.license_create import CreateLicense
from command_center.test import TestCaseMixin
from command_center.library.AppConfig import gconfig
from command_center.protocol.license import license_pb2
from command_center.protocol.site import server_pb2


class TestStringMethods(TestCaseMixin):

    def test_license_1_request(self):
        self.insert_site()

        server = server_pb2.Server(id = 100, name='Coway', type='allinone', hostname='sample', ipaddr='192.168.20.20',
                                   os_ver='redhat8.4',
                                   hardware_uuid=gconfig.server_model.uuid,
                                   machine_id=gconfig.server_model.machine_id,
                                   license_data='-')

        equest_packet = license_pb2.LicenseRegistrationRequest(reg_user_name = "youngjin", reg_user_tel = "010-0000-0000",
                                                               site_code="coway", server_serial="relay", server=server)
        license = LicenseClientMixin()

        license_status, ret = license.Register(equest_packet)
        self.assertEqual(license_status, license_pb2.LicenseStatus.WAIT)

    def test_license_2_site_none(self):

        server = server_pb2.Server(id = 100, name='Coway', type='allinone', hostname='sample', ipaddr='192.168.20.20',
                                   os_ver='redhat8.4',
                                   hardware_uuid=gconfig.server_model.uuid,
                                   machine_id="server_none",
                                   license_data='-')

        equest_packet = license_pb2.LicenseRegistrationRequest(reg_user_name = "youngjin", reg_user_tel = "010-0000-0000",
                                                               site_code="coway_none", server_serial="relay", server=server)
        license = LicenseClientMixin()

        license_status, ret = license.Register(equest_packet)
        self.assertEqual(license_status, license_pb2.LicenseStatus.SITE_NONE)

    def test_license_3_confirm(self):
        c_license = CreateLicense(dict(server_type='allinone', user_name='admin', site_name='coway', site_code='coway',
                                       hardware_info=dict(bps=10,hardware_key=gconfig.server_model.uuid, hdd=100, machine_id=gconfig.server_model.machine_id),
                                       server_id = 3700, license_type='poc', license_version='1.0', start_date='2022-01-01', end_date='2023-01-03'
                                  ))

        raw = c_license.filename_buffer()
        self.insert_license(dict(), raw)

        license = LicenseClientMixin()
        license_status, ret = license.Status()
        self.assertEqual(license_status, license_pb2.LicenseStatus.CONFIRM)



if __name__ == '__main__':
    import command_center.library.database as db
    db.global_db_connect()
    unittest.main(verbosity=2)
