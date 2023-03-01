import logging

from termcolor import cprint

from command_center.client.data import DataClientMixin
from command_center.command import ValueInput
from command_center.protocol.data.data_pb2 import DataType, DataLevel
import command_center.library.database as db

logger = logging.getLogger(__name__)


class SyncDataMixin(DataClientMixin):
    def _last_version(self, data_type):
        query = """
                SELECT version FROM data_last_versions WHERE data_type = {0}
            """.format(data_type)
        last_version = 0
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                last_version, = pcursor.fetchone()
        return last_version

    def _update_data(self, data_type, version, update_level):
        while True:
            status, version = self.GetData(data_type, version, level=update_level)
            if status:
                """ 최초 이후에는 업데이트된 정보만 가져온다. """
                if update_level == DataLevel.L_ALL:
                    update_level = DataLevel.L_UPDATE
                cprint("Version Upgrade Success : {0}".format(version), "yellow")
                version = version + 1
            else:
                break

    def data_snort(self):
        ret = ValueInput("Full synchronization to snort ? ( Y / N )", valuetype=['Y', 'N'] ,Default='N')
        if ret == 'exit':
            return

        cprint("Snort Update Begin", "green")
        if ret.lower() == 'y':
            self._update_data(DataType.SNORT, 0, DataLevel.L_ALL)
        else:
            last_version = self._last_version(DataType.SNORT)
            level = (last_version and DataLevel.L_UPDATE or DataLevel.L_ALL)
            self._update_data(DataType.SNORT, last_version, level)

        cprint("Snort Update Done", 'green')