#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum

APP_DEBUG = False

BUFFER_SIZE = 65536

"""
    관리 포트 
"""
QMC_SERVER_PORT = 20060

"""
   자체 SSH 서버 포트 
"""
SSH_SERVER_PORT = 10040

"""
"""

DEFAULT_APP_HOME = "/opt/command_center/"
HOME_PATH = "CM_HOME"

DEFAULT_TLS_CERT_DIR = '/opt/command_center/ssl/'


class EName(Enum):
    """
        Message 이름 정보
    """
    AMS = 'AMS'


class EControlType(Enum):
    """
        제어관련 keyword 이다 .
        API 서버에서 사용되며 , server 에서 db조회용으로 사용한다.
    """
    DIR = "dir"
    FILE = "file"
    TABLE = "table"
    BLACKDB_PAYLOAD = "blackdb-payload"
    BLACKDB_INDEX = "blackdb-index"
    BLACKDB_STATISTIC = "blackdb-statistic"
    BLACKDB_REPACE_PAYLOAD = "blackdb-payload-replace"
    SEARCH_RESULT = "results-search"
    SEARCH_RAPIED = 'results-rsearch'
    SEARCH_PAYLOAD_RESULT = "results-payload"
    SEARCH_CONTENTS_RESULT = "results-contents"
    CONTENTS = 'contents'
    MAIL = "contents-mail"
    SCHEDULE = "contents-schedule"
    BOARD = "contents-board"
    APPROVE = "contents-approve"
    NOTE = "contents-note"
    MEMO = "contents-memo"
    KEYWORD = "contents-keyword"
    TRANSLATE = "contents-translate"
    TRANSFER = "contents-transfer"
    OTHER = "contents-other"
    POST = "contents-post"
    CONTENTS_ERROR = "contents-error"


class EPort(Enum):
    DATA_PORT = 'data-port'   # 데이터 전송 포트
    SSH_PORT = 'ssh-port'     # 자체 SSH 포트
    RPC_PORT = 'rpc-port'     # 제어 RPC 포트


class EUseDatabaseStatus(Enum):
    '''
        DB상태 정보
    '''
    SUCCESS = "success"
    CONN_ERROR = "connect_error"
    LIBRARY_ERROR = "library_error"
    UPDATE_ERROR = "update_error"


database_status_choice = ((EUseDatabaseStatus.SUCCESS.value, '정상'),
                          (EUseDatabaseStatus.CONN_ERROR.value, '접속에러'),
                          (EUseDatabaseStatus.UPDATE_ERROR.value, '업데이트에러'))


class EUseDatabase(Enum):
    ORACLE = 'oracle'
    MYSQL = 'mysql'
    MSSQL = 'mssql'
    PSQL = 'psql'


database_choice = ((EUseDatabase.ORACLE.value, '오라클'),
                   (EUseDatabase.MSSQL.value, 'MSSQL'),
                   (EUseDatabase.MYSQL.value, 'MYSQL'),
                   (EUseDatabase.PSQL.value, 'Postgresql'))


class ENetworkGroup(Enum):
    NONE = 'none'
    INTERNAL = 'internal'
    EXTERNAL = 'external'
    DATABASE = 'database'
    WEB = 'web'

class Progress(Enum):
    preparing = "preparing"         # 준비중
    completed = "completed"         # 완료
    ing = "ing"                     # 진행중
    error = "error"                 # 에러
    loading = 'loading'             # 로딩
    get_data = 'get data'           # 데이터 가지고 옴
    transforming = 'transforming'   # 변환중
