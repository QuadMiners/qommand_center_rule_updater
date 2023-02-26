import unittest

from pcapbox_app.system.day_statistic import StatisticContents


class Contents(unittest.TestCase):

    def test_system(self):
        system = StatisticContents()
        system.process()
        system.set_database()

if __name__ == '__main__':
    from pcapbox_library.database import global_db_connect
    global_db_connect()

    unittest.main()
