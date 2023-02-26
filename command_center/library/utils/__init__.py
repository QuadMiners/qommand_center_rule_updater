#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

import pytz

def str_to_datetime(value, date_format='%Y-%m-%d %H:%M'):
    """
        YYYY-MM-DD HH24:MI

    :param value:
    :return:
    """
    return datetime.datetime.strptime(value, date_format)


def str_to_datetime_timezone(value, date_format='%Y-%m-%d %H:%M'):
    """
      DB에서 읽어 올경우 TimeZone 정보가 뒤에 붙는다 이럴때는 해당 내용으로 변경해야한다.
    
        
        
    :param value:
    :return: 
        %Y-%m-%d %H:%M:%S  %Z%z 포멧으로 리턴됨 .
    """
    naive = datetime.datetime.strptime(value, date_format)
    return naive.replace(tzinfo=pytz.timezone('Asia/Seoul'))


def datetime_to_datetime_timezone(naive):
    """
      DB에서 읽어 올경우 TimeZone 정보가 뒤에 붙는다 이럴때는 해당 내용으로 변경해야한다.



    :param value:
    :return: 
        %Y-%m-%d %H:%M:%S  %Z%z 포멧으로 리턴됨 .
    """
    return naive.replace(tzinfo=pytz.timezone('Asia/Seoul'))

