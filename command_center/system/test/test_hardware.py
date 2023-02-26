import unittest

from pcapbox_app.system.powersupply import PowerSupplyWatcher
from pcapbox_app.system.raid.mega_raid import MegaRaidManager


class TestHardware(unittest.TestCase):
    def test_powersupply(self):
        power = PowerSupplyWatcher()


    def test_raidcard(self):
        """

        """
        mega = MegaRaidManager()

if __name__ == '__main__':
    from pcapbox_library.database import global_db_connect, pmdatabase
    from pcapbox_app.contents import global_table_instance
    import pcapbox_library.AppDefine as define

    define.APP_DEBUG = True
    global_db_connect()
    global_table_instance()
    unittest.main()
