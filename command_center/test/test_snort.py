import unittest

from command_center.client.data import DataClientMixin
from command_center.client.license import LicenseClientMixin
from command_center.client.license_create import CreateLicense
from command_center.client.site import SiteClientMixin
from command_center.protocol.data.data_pb2 import DataType
from command_center.test import TestCaseMixin
from command_center.library.AppConfig import gconfig
from command_center.protocol.license import license_pb2
from command_center.protocol.site import server_pb2


class TestStringMethods(TestCaseMixin):
    def test_version(self):
        value = DataClientMixin()
        value.GetVersions()

    def test_server(self):
        value = DataClientMixin()
        value.GetData(DataType.SNORT, 100002)

if __name__ == '__main__':
    import command_center.library.database as db
    db.global_db_connect()
    unittest.main(verbosity=2)

