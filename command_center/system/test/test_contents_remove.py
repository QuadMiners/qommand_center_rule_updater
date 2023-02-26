import unittest

from pcapbox_app.system.dir_manager import ContentsManager, ContentsFile
import pcapbox_library.AppDefine as define


class ContentsCheckFileSize(unittest.TestCase):

    def test_remove_contents(self):
        t = ContentsManager(dict(loop='day',
                                 partition='/data',
                                 path="/data/contents",
                                 percent=90,
                                 storage="100day",
                                 type='contents'))

        t.process()

        #t = ErrorContentsDirectory(dict(loop='day', partition='/data', path="/data/contents/", related_table='contents_migrate_error', percent=90, storage="30day", type='mail', related_table_column="session_date"))
        #t.process()
        #t = DirectoryManager(dict(loop='day', partition='/results', path="/results/search/search_flow", related_table='search_history', percent=90, storage="10day", type='result-search', path_exception='today_files', related_table_column="reg_date"))
        #t.process()

        #t = DirectoryManager(dict(loop='day', partition='/results', path="/results/search", percent=90, storage="10day", type='result-payload', path_exception='search_flow' ))
    def test_remove_file(self):
        t = ContentsFile(dict(loop='day',
                                 partition='/data',
                                 path="/data/contents/file",
                                 percent=90,
                                 storage="100day",
                                 type='contents'))

        t.process()

if __name__ == '__main__':
    from pcapbox_library.database import global_db_connect, pmdatabase
    import pcapbox_app.contents as df
    define.APP_DEBUG = True
    global_db_connect()
    df.global_table_instance()

    unittest.main()
