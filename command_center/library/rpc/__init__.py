import datetime
import logging

import google
from google.protobuf.struct_pb2 import Struct

import command_center.library.database as db
from command_center import DBException

logger = logging.getLogger(__name__)


def query_to_object(query, msg_class):
    """
    msg_class 가 Struct 일 경우

    """
    datas = []
    try:
        with db.pmdatabase.get_cursor() as pcursor:
            pcursor.execute(query)
            rows = pcursor.fetchall()
            columns = pcursor.description
            for row in rows:
                if isinstance(msg_class, google.protobuf.pyext.cpp_message.GeneratedProtocolMessageType):
                    msg = Struct()
                else:
                    msg = dict()

                for (index, value) in enumerate(row):
                    if isinstance(value, int):
                        msg[columns[index].name] = str(int(value))
                    elif isinstance(value, datetime):
                        msg[columns[index].name] = str(value)
                    else:
                        msg[columns[index].name] = value
                datas.append(msg)
    except DBException as e:
        logger.error("DBException Query To Object | {0} \n {1}".format(e, query))
    except ValueError as p:
        logger.error("ValueError Exception Query To Object | {0} \n {1}".format(p, query))

    return datas
