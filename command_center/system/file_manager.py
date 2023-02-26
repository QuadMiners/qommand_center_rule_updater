#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import hashlib
import os
import logging
import shutil

import time


logger = logging.getLogger(__name__)


class File(object):
    file_size = 0
    create_time = 0
    file = None

    def __init__(self, path, filename, open_type = os.O_RDONLY, psize=False):
        """
        :param path:
        :param filename:
        :param psize: 파일사이즈를 OPEN과 함께 구할것인가?
        """
        self.open_type = open_type
        self.file_name = filename
        self.path = path

        fpath = os.path.join(self.path, self.file_name)
        self.f_path = isinstance(fpath, bytes) and fpath or fpath.encode('utf-8')
        self.p_size = psize

    def open(self):
        try:
            if not self.file:
                self.file = os.open(self.f_path, self.open_type)

                if self.p_size:
                    self.load()
        except FileNotFoundError as e:
            logger.error("Error] FileNotFound  FileName [{0}]".format(self.f_path))
            raise e
        return self.file

    def seek(self, offset):
        self.file.seek(offset)

    def write(self, buf):
        self.file.write(buf)

    def close(self):
        try:
            os.close(self.file)
            self.file = None
        except Exception as e:
            pass

    def hash_info(self):
        self.open()
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        while True:
            data = os.read(self.file, 4096)
            if not data:
                break
            md5.update(data)
            sha1.update(data)
            sha256.update(data)
        self.close()
        return md5.hexdigest(), sha256.hexdigest(), sha1.hexdigest()

    def load(self):
        try:
            stat = os.stat(self.f_path)
            try:
                self.create_time = stat.st_mtime # 수정날짜
            except AttributeError:
                self.create_time = stat.st_mtime

            self.file_size = stat.st_size
        except FileNotFoundError as e:
            logger.error("Error] FileNotFound  FileName [{0}]".format(self.f_path))
            raise e

        return self.file_size

    def file_date_range(self, check_date):
        cre_date = datetime.datetime.fromtimestamp(self.create_time)
        if check_date == cre_date.replace(hour=0, minute=0, second=0, microsecond=0):
            return self.file_size
        return 0

    def remove(self):
        try:
            os.remove(self.f_path)
            if len([name for name in os.listdir('.') if os.path.isfile(name)]) <= 0:
                shutil.rmtree(self.path)
        except OSError as e:
            pass
        except Exception as e:
            pass

    def check_file(self, worktime):
        curtime = time.time()

        self.load() # 재생성될 경우를 대비해 업데이트함.
        if (curtime - self.create_time) > worktime:
            return False  # 남아있어야함.
        return True  # remove

    def __str__(self):
        return "File : {0}/{1}".format(self.path, self.file_name)

    def __lt__(self, other):
        return self.create_time < other.create_time

    def __hash__(self):
        return int(hashlib.sha1(self.f_path).hexdigest(), 16) % (10 ** 8)

    def __eq__(self, other):
        return other.f_path == self.f_path

    def __ne__(self, other):
        """
            <>  !=
        """
        return other.f_path != self.f_path

    def __del__(self):
        if self.file:
            self.close()
