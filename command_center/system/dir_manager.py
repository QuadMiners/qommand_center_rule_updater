#!/usr/bin/env python
# -*- coding: utf-8 -*-
import concurrent
import os
import logging
import datetime
import shutil

import time

from termcolor import cprint

import pcapbox_app.contents as df
from pcapbox_library.AppConfig import gconfig
import pcapbox_library.database as db
from pcapbox_library.database import DBException
from pcapbox_library.qredis.redis_server import ClientRedisMixin
from pcapbox_library.AppLibrary import datetime_range_array, path_to_order_date
from pcapbox_app.system import LoopMixin
import pcapbox_library.AppDefine as define

logger = logging.getLogger(__name__)

"""

[
  {
  	"partition": "/results",
    "loop": "hour",
    "name": "detail",
    "path": "/results/payload",
    "save": "1hour",
    "exception_dir": "",
    "related_table": "",
    "related_redis_key": ""
  },
  {
  	"partition": "/results",
    "loop": "day",
    "name": "search",
    "path": "/results/search",
    "save": "7day",
    "exception_dir": "",
    "related_table": "",
    "related_redis_key": ""
  },
  {
  	"partition": "/results",
    "loop": "day",
    "name": "contents",
    "path": "/results/contents",
    "save": "7day",
    "exception_dir": "",
    "related_table": "",
    "related_redis_key": ""
  }
]

"""


class DirectoryManager(LoopMixin, ClientRedisMixin):
    __current_total_byte = None
    __files = None

    def __init__(self, obj):
        ClientRedisMixin.__init__(self)

        for key in obj.keys():
            setattr(self, key, obj[key])

    def file_timecheck(self, path):
        stat = os.stat(path)
        try:
            return stat.st_birthtime
        except AttributeError:
            return stat.st_mtime

    @property
    def current_total_byte(self):
        return self.__current_total_byte

    @current_total_byte.setter
    def current_total_byte(self, val):
        self.__current_total_byte = val

    @property
    def files(self):
        return self.__files

    @files.setter
    def files(self, val):
        self.__files = val

    def get_tree_files(self, in_path=None, totalByteFlag=False):
        """
            Directory Total Size 구하기
        """
        total = 0
        self.__files = set([])

        if in_path:
            local_path = in_path
        else:
            local_path = self.path

        tmp_files = set([])
        temp_dirs = set([])

        for dirpath, dirnames, filenames in os.walk(local_path):
            if len(filenames) > 0:  # 파일이 존재하는 디렉터리만 추린다..
                temp_dirs.add(dirpath)

        def file_obj(local_dir, flag=False):
            from pcapbox_app.system.file_manager import File

            ret = set([])
            for dirpath, dirnames, filenames in os.walk(local_dir):
                for filename in filenames:
                    try:
                        f = File(dirpath, filename, psize=flag)
                        ret.add(f)
                    except OSError as error:
                        logger.error('Error calling stat(): %s', str(error))
            return ret

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_file = {executor.submit(file_obj, o_dir, totalByteFlag): o_dir for o_dir in temp_dirs}
            for future in concurrent.futures.as_completed(future_to_file):
                data = future.result()
                tmp_files |= data

        ''' 
        기존에 체크했던 파일들을 다시 체크하지 않기 위해
        '''
        rets = tmp_files - self.files
        self.files |= rets

        if len(self.files) > 0:
            self.files = set(sorted(self.files, reverse=True))

        if totalByteFlag:
            for v in self.files:
                if v.file_size <= 0:
                    v.load()
                total = total + v.file_size

        return total

    # 동작
    def process(self):
        logger.info("DirectoryManager Process Start : {0}".format(self.desc))
        # Work Time
        itime = time.mktime(self.save_time().timetuple())

        try:
            for in_dir in os.listdir(self.path):
                if self.check_exception_dir(in_dir):
                    dir_path = os.path.join(self.path, in_dir)
                    if self.file_timecheck(dir_path) < itime:
                        if os.path.isdir(dir_path):
                            logger.info("<< Delete dir  >> : {0}".format(in_dir))
                            shutil.rmtree(dir_path)
                        else:
                            logger.info("<< Delete file >> : {0}".format(in_dir))
                            os.remove(dir_path)
        except OSError as oe:
            logger.error("Directory Process : OS Error  Name: {0} Path: {1} : {2}".format(self.desc, self.path, oe))
        except Exception as ee:
            logger.error("Directory Process : Exception Name: {0} Path: {1} : {2}".format(self.desc, self.path, ee))

        logger.info("DirectoryManager Process End : {0} \n".format(self.desc))


class SearchResultDirectoryManager(DirectoryManager):
    """
        results-search
        나중에 필요시 사용하자
    """

    def remove_table(self):
        query = """ SELECT results FROM search_history WHERE reg_date < '{0}' """.format(self.save_time())
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                rows = pcursor.fetchall()
                for row in rows:
                    yield row[0]['dirname']


"""
    컨텐츠 관리 
"""


class ContentsFile(DirectoryManager):
    """
        파일 정리
    """

    def check_files(self, id, s_date):
        check_file= [
                        "SELECT count(*) FROM contents_session_files where file_id = {id} ",
                        "SELECT count(*) FROM contents_mail_files where file_id = {id} ",
                        "SELECT count(*) FROM contents_approve_files where file_id = {id} ",
                        "SELECT count(*) FROM contents_board_files where file_id={id}",
                        "SELECT count(*) FROM contents_schedule_files where file_id={id}",
                    ]

        cnt = 0
        value_param = dict(id=id, session_date=s_date)
        for query in check_file:
            with db.pmdatabase.get_cursor() as pcursor:
                pcursor.execute(query.format(**value_param))
                cnt, = pcursor.fetchone()
            if cnt > 0:
                break

        return cnt > 0

    def remove_real_dir(self, id, dirname):
        logger.info("Contents Remove File Dir : {0} [{1} ] ".format(id, dirname))
        try:
            try:
                if os.path.exists(dirname) and os.path.isdir(dirname):
                    if define.APP_DEBUG is False:
                        shutil.rmtree(dirname, ignore_errors=True)
                    else:
                        print("Real Remove Dir ", dirname)
            except OSError as e:
                logger.error("Remove Real Remove Tree {0}".format(e))

        except IOError as e:
            logger.error("Error Contents RealRemove {0}".format(dirname))

    def delete_data_files_table(self, id):
        try:
            db.pmdatabase.execute('DELETE FROM data_files_ams WHERE file_id = {0}'.format(id))
        except DBException as e:
            pass

        try:
            db.pmdatabase.execute('DELETE FROM data_files_virus WHERE file_id = {0}'.format(id))
            db.pmdatabase.execute('DELETE FROM data_files WHERE id = {0}'.format(id))
            return True
        except DBException as e:
            logger.error("Delete Files Table Error {0}".format(e))
            return False

    def files(self, itime):
        d_date = """ '{0}-{1}-{2} 00:00:00' """.format(itime.year, itime.month, itime.day)
        query = "SELECT id, dir_info FROM data_files WHERE last_date < {0} and server_id = {1} LIMIT 10000".format(d_date, gconfig.server_id)

        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                rows = pcursor.fetchall()
                for row in rows:
                    if not self.check_files(row[0], itime):
                        logger.info("Delete File {0} | {1}".format(row[0], row[1]))
                        if self.delete_data_files_table(row[0]):
                            self.remove_real_dir(row[0], row[1])
    def process(self):
        """
            하루에 1번씩 체크 하자
        """
        print_dict = dict(desc=self.desc)

        logger.info("Contents File Process Start : {desc} : ".format(**print_dict))
        try:
            itime = self.save_time().replace(hour=0, minute=0, second=0)
            self.files(itime)
        except OSError as e:
            logger.error("Contents File Process : OS Error  Name: {0} Error [ {1} ]".format(self.desc, e))
        except Exception as e:
            logger.error("Contents Process : Exception Name: {0} Error [ {1} ]".format(self.desc, e))

        logger.info("Contents File Process End : {desc} ".format(**print_dict))


class ContentsManager(DirectoryManager):
    """
        Contents 관리
            /data/contents/{category}/{application}
                                      { error }/yyyy/mm/dd/


            day total count

        관리 
            path / YYYY / MM / DD / Hour / Min/

        (?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<hour>\d+)/(?P<minute>\d+)
    """
    first_date = None
    last_date = None

    def __init__(self, obj):
        super(ContentsManager, self).__init__(obj)

        if gconfig.server_type == define.EServerType.MANAGER.value:
            self.first_date = self._check_last_date_database()
        else:
            self.first_date = self._check_last_date()
        self.last_date = datetime.datetime.now().replace(hour=0,minute=0, second=0)

    def _check_last_date_database(self, order=False):
        r_date = datetime.datetime.now()
        query ="""
                SELECT session_date FROM contents_session order by 1  {0} limit 1""".format(order and 'desc' or '')
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                (r_date, )= pcursor.fetchone()

        return datetime.datetime(r_date.year, r_date.month, r_date.day, r_date.hour, r_date.minute)

    def _check_last_date(self, asc=False):
        value_date = None
        dirs = os.listdir(self.path)
        for k_dir in dirs:
            if k_dir == 'file':
                continue
            p_dir = os.path.join(self.path, k_dir)
            if os.path.isdir(p_dir):
                ret_date = path_to_order_date(p_dir, asc)
                if ret_date:
                    if asc is False:
                        if value_date is None:
                            value_date = ret_date
                        elif value_date > ret_date:
                            value_date = ret_date
                    else:
                        if value_date is None:
                            value_date = ret_date
                        elif value_date > ret_date:
                            value_date = ret_date

        if value_date is None:
            value_date = datetime.datetime.now().replace(hour=0,minute=0, second=0)
        return value_date

    def delete_db_time(self):
        d_date = "{0}-{1}-{2} {3}:00:00".format(self.first_date.year, self.first_date.month, self.first_date.day, self.first_date.hour)

        for ecategory in define.EActionCategory:
            try:
                if ecategory in (define.EActionCategory.unknown, define.EActionCategory.file, define.EActionCategory.all):
                    """
                        POST 는 아래에서 삭제됨.
                    """
                    continue

                table = df.g_table_instance[ecategory.value]

                contents_delete_query = """ DELETE FROM {0} WHERE  session_date <  '{1}' """.format(table.tablename, d_date)
                if define.APP_DEBUG:
                    cprint(contents_delete_query, 'green')

                contents_file_delete_query = """ DELETE FROM {0}_files WHERE session_id in (select session_id FROM {0} WHERE  session_date <  '{1}') """.format(table.tablename, d_date)
                if define.APP_DEBUG:
                    cprint(contents_file_delete_query, 'green')

                if define.APP_DEBUG is False:
                    if ecategory not in (define.EActionCategory.other, define.EActionCategory.note, define.EActionCategory.memo, define.EActionCategory.translate, define.EActionCategory.login, define.EActionCategory.keyword, define.EActionCategory.comment):
                        try:
                            logger.info("Query {0}".format(contents_file_delete_query))
                            db.pmdatabase.execute(contents_file_delete_query)
                        except DBException as k:
                            """ 컨텐츠의 File 디렉터리가 존재 하지 않을수 있음"""
                            logger.error("Contents File Table Delete  | {0} | Error {1}".format(contents_file_delete_query, k))
                    try:
                        logger.info("Query {0}".format(contents_delete_query))
                        db.pmdatabase.execute(contents_delete_query)
                    except DBException as l:
                        logger.error("Contents Table Delete  | {0} | Error {1}".format(contents_delete_query, l))

                else:
                    print(contents_file_delete_query)
                    print(contents_delete_query)
            except Exception as e:
                logger.error("Contents Delete Exception {0}".format(e))

        session_delete = """ 
                                DELETE FROM contents_session WHERE session_date < '{0}'  """.format(d_date)

        session_file_delete_query = """
                                DELETE FROM contents_session_files WHERE session_date < '{0}' """.format(d_date)

        if define.APP_DEBUG is False:

            try:
                logger.info("Query {0}".format(session_file_delete_query))
                db.pmdatabase.execute(session_file_delete_query)
            except DBException as e:
                """ 컨텐츠의 File 디렉터리가 존재 하지 않을수 있음"""
                logger.error("Contents File Delete  | {0}".format(session_file_delete_query))
                pass

            try:
                logger.info("Query {0}".format(session_delete))
                db.pmdatabase.execute(session_delete)
            except DBException as e:
                logger.error("Contents Session Delete  | {0}".format(session_delete))
                pass
        else:
            print(session_file_delete_query)
            print(session_delete)

    def remove_real_dir(self, dirname):
        remove_dir = os.path.join(self.path, dirname)
        logger.info("<< Contents Remove Contents Dir >> {0} || {1}".format(dirname, remove_dir))
        try:
            try:
                if os.path.exists(remove_dir) and os.path.isdir(remove_dir):
                    if define.APP_DEBUG is False:
                        shutil.rmtree(remove_dir, ignore_errors=True)
                    else:
                        print("Real Remove Dir ", remove_dir)
            except OSError as e:
                logger.error("Remove Real Remove Tree {0}".format(e))

        except IOError as e:
            logger.error("Error Contents RealRemove {0}".format(remove_dir))

    def remove_contents_file(self, remove_date):

        for category in define.EActionCategory:
            if category not in (define.EActionCategory.memo, define.EActionCategory.keyword, define.EActionCategory.note, define.EActionCategory.translate, define.EActionCategory.other, define.EActionCategory.file):
                try:
                    if category == define.EActionCategory.unknown:
                        k_path = os.path.join(self.path, 'post')
                    else:
                        k_path = os.path.join(self.path, category.value)

                    if os.path.exists(k_path):
                        p_date = path_to_order_date(k_path, False)
                        if p_date and p_date <= remove_date:
                            logger.info("Contents Remove Start Category [ {0} ]  Start Date  {1} ~ {2} ".format(category.value, p_date, remove_date))
                            for r_date in datetime_range_array(p_date, remove_date, 24 * 60 * 60):
                                timetuple = r_date.timetuple()
                                category_name = category.value
                                if category == define.EActionCategory.unknown:
                                    category_name = 'post'

                                dirtype = "%s/%d/%d/%d" % (category_name, timetuple.tm_year, timetuple.tm_mon, timetuple.tm_mday)
                                self.remove_real_dir(dirtype)

                                # 1day 씩 삭제
                                tempdate = r_date + datetime.timedelta(days=1)
                                if tempdate.year != r_date.year:
                                    dirtype = "%s/%d" % (category_name, timetuple.tm_year)
                                    self.remove_real_dir(dirtype)
                                elif tempdate.month != r_date.month:
                                    dirtype = "%s/%d/%d" % (category_name, timetuple.tm_year, timetuple.tm_mon)
                                    self.remove_real_dir(dirtype)
                            logger.info("Contents Remove End Category [ {0} ]  Start Date  {1} ~ {2} ".format(category.value, p_date, remove_date))
                except Exception as k:
                    logger.error("Contents Remove Directory |  {0}".format(k))

        self.first_date = remove_date

    def process(self):
        """
            하루에 1번씩 체크 하자
        """
        print_dict = dict(desc=self.desc, last_date=self.last_date.strftime("%Y-%m-%d"), first_date=self.first_date.strftime("%Y-%m-%d"))
        logger.info("Contents Process Start : {desc} :  {first_date} ~ {last_date}".format(**print_dict))

        try:
            itime = self.save_time().replace(hour=0, minute=0, second=0)

            self.last_date = datetime.datetime.now().replace(hour=0,minute=0, second=0)
            if self.first_date < itime:
                if gconfig.server_type in (define.EServerType.ALLINONE.value, define.EServerType.MANAGERNODE.value):
                    self.remove_contents_file(itime)
                    self.delete_db_time()
                elif gconfig.server_type == define.EServerType.MANAGER.value:
                    self.delete_db_time()
                else:
                    self.remove_contents_file(itime)

        except OSError as e:
            logger.error("Directory Process : OS Error  Name: {0} Error [ {1} ]".format(self.desc, e))
        except Exception as e:
            logger.error("Directory Process : Exception Name: {0} Error [ {1} ]".format(self.desc, e))

        print_dict = dict(desc=self.desc, last_date=self.last_date, first_date=self.first_date)

        logger.info("Contents Process End : {desc} :  {first_date} ~ {last_date}".format(**print_dict))


class ErrorContentsDirectory(ContentsManager):
    """
        /data/contents/<type>/error/<application>/<action>/YYYY/MM/DD/
    """

    def _check_last_date(self, order="desc"):

        r_date = datetime.datetime.now()
        query ="""
                SELECT {0} FROM
                    {1}
                    WHERE server_id = {2} order by {0} {3}""".format(self.related_table_column, self.related_table, gconfig.server_id, order)
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                (r_date, )= pcursor.fetchone()
        return datetime.datetime(r_date.year, r_date.month, r_date.day, r_date.hour, r_date.minute)

    def application_load(self):
        self.applications = set([])
        query = "SELECT  keyword FROM contents_export_application"
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            if pcursor.rowcount > 0:
                rows = pcursor.fetchall()
                for keyword in rows:
                    self.applications.add(keyword[0])

    def delete_db_time(self):
        d_date = """to_timestamp('%d-%02d-%02d 00:00:00', 'YYYY-MM-DD HH24:MI:SS')""" % (self.first_date.year, self.first_date.month, self.first_date.day)

        error_query = """
                                DELETE FROM {0} WHERE session_date < {1} and server_id = {2}
                      """.format(self.related_table, d_date, gconfig.server_id)

        if define.APP_DEBUG is False:
            db.pmdatabase.execute(error_query)
        else:
            print(error_query)

    def remove_database(self, remove_date):

        timetuple = remove_date.timetuple()

        for category in define.EActionCategory:
            for application in self.applications:
                for action in define.EActionList:
                    dirtype = "%s/error/%s/%s/%d/%d/%d" % (category.value, application, action.value, timetuple.tm_year, timetuple.tm_mon, timetuple.tm_mday)
                    self.remove_real_dir(dirtype)

                    # 1hour 씩 삭제
                    tempdate = remove_date + datetime.timedelta(days=1)

                    if tempdate.month != self.first_date.month:
                        dirtype = "%s/error/%s/%s/%d/%d" % (category.value, application, action.value, timetuple.tm_year, timetuple.tm_mon)
                        self.remove_real_dir(dirtype)

                    if tempdate.year != self.first_date.year:
                        dirtype = "%s/error/%s/%s/%d" % (category.value, application, action.value, timetuple.tm_year)
                        self.remove_real_dir(dirtype)

        self.first_date = remove_date + datetime.timedelta(days=1)

    def process(self):
        self.path = define.DEFAULT_CONTENTS_DIR
        self.application_load()
        """
            하루에 1번씩 체크 하자
        """
        print_dict = dict(desc=self.desc, last_date=self.last_date, first_date=self.first_date)
        logger.info("Contents Error Process Start : {desc} :  {first_date} ~ {last_date}".format(**print_dict))

        try:
            itime = self.save_time()
            self.last_date = self._check_last_date()

            if self.first_date < itime:
                dircheck_range = datetime_range_array(self.first_date, self.last_date, 24 * 60 * 60)

                for date_range in dircheck_range:
                    if date_range < itime:
                        self.remove_database(date_range)
                    else:
                        break
        except OSError as e:
            logger.error("Directory Process : OS Error  Name: {0} Path: {1}".format(self.desc, self.path))
        except Exception as e:
            logger.error("Directory Process : Exception Name: {0} Path: {1}".format(self.desc, self.path))

        print_dict = dict(desc=self.desc, last_date=self.last_date, first_date=self.first_date)

        logger.info("Contents Error Process End : {desc} :  {first_date} ~ {last_date}".format(**print_dict))

