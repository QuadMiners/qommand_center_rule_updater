#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os

from pcapbox_library.AppDecorator import database_exception
from pcapbox_library.AppNtp import NTPException, NTPClient
from pcapbox_library.AppObject import QObject
import pcapbox_library.database as db
from pcapbox_library.history.AppHistory import HistoryMixin

logger = logging.getLogger(__name__)


class NTPManager(HistoryMixin):
    """
        NTP 업데이트 
    """
    error_cnt = 0

    @database_exception
    def __get_ntp_info(self):
        result = QObject()
        status = ""
        ok = True
        get_query = "SELECT hostname, use_flag FROM system_ntp "

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(get_query)
            columns = pcursor.description
            row = pcursor.fetchone()
            for (index, column) in enumerate(row):
                result[columns[index][0].lower()] = column
        return result

    def __set_system(self, update_time, host):
        """
            실제 Hardware 에 시간 설정  
        """

        try:
            os.system("date +%s -s @{0}".format(update_time.recv_time))
            logger.info("NTP Time Update Success >> {0}".format(update_time.recv_time))
            self.history_info(code=80100, **dict(host=host))
        except Exception as e:
            logger.error("NTP Update Error {0}".format(e))

    def __update_status(self, ok, host, error=None):
        status = ""
        update_query = "UPDATE system_ntp SET  sync_date = now() {0}  "

        if ok is False and self.error_cnt > 3:
            status = ", status='socket_error'"
            self.history_error(code=80101, **dict(host=host, err=error))
        db.pmdatabase.execute(update_query.format(status))

    def process(self):
        error = None
        ok = True

        result = self.__get_ntp_info()

        logger.info("NTP Process Start")
        if result and result.use_flag == 'Y':
            try:
                client = NTPClient()
                response = client.request(result.hostname, version=3)
                self.__set_system(response, result.hostname)
                self.error_cnt = 0
            except NTPException as e:
                ok = False
                error = str(e)
                self.error_cnt = self.error_cnt + 1
            except Exception as e:
                logger.error("NTP Process Exception {0}".format(e))
            finally:
                try:
                    self.__update_status(ok, result.hostname, error)
                except Exception as e:
                    logger.error("NTP Update Exception | {0}".format(e))
        logger.info("NTP Process End ")


