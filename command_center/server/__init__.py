import command_center.library.database as db
from command_center.library.AppObject import QObject


class SiteMixin(object):
    def get_site(self, site_code):
        site_info = None
        query = """
                SELECT id, name, address, tel, 'desc', engineer, sales 
                FROM site
                WHERE code = '{0}'
                """.format(site_code)

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                row = pcursor.fetchone()
                col_name = (columns[0] for columns in pcursor.description)
                row_data_dict = dict(zip(col_name, row))
                site_info = QObject(row_data_dict)

        return site_info
