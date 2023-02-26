import unittest

from pcapbox_app.system.server_monitor import ServerHeartBeatMixin
from pcapbox_library.AppObject import QObject
import pcapbox_library.AppPing as ping


class ContentsCheckFileSize(unittest.TestCase):
    def test_ping(self):
        hartbeat = ServerHeartBeatMixin()
        ret = hartbeat.ping()

    def test_ping_fail(self):
        hartbeat = ServerHeartBeatMixin()
        obj = QObject(dict(server_id=9000))
        ret = hartbeat.ping(obj)

if __name__ == '__main__':
    from pcapbox_library.database import global_db_connect, pmdatabase
    from pcapbox_app.contents import global_table_instance
    ping.DAEMON = True

    global_db_connect()
    global_table_instance()

    unittest.main()
