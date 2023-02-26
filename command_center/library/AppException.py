#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
logger = logging.getLogger(__name__)


class QMError(Exception):
    msg = None
    code = None

    def __init__(self, code, error, exception_key=None, status_code=400):
        self.code = code
        self.msg = error
        self.exception_key = exception_key
        self.status_code = status_code

    def response_data(self):
        return dict(error_code=self.code, results=self.msg)

    def __str__(self):
        return "{0}:{1}".format(self.code, self.msg)


class ContentsException(QMError):
    pass

class ContentsNotFoundException(QMError):
    pass

class ContentsParserException(QMError):
    pass

class ContentsNoContentsException(QMError):
    pass


class NotFoundHistoryCode(QMError):
    pass


class DateRangeException(QMError):
    pass
