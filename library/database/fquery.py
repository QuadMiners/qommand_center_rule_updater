import psycopg2.extras

import library.database as db

db.global_db_connect()


def fetchall_query(query: str, database=db):
    with database.pmdatabase.get_cursor() as pcursor:
        pcursor.execute(query)
        if pcursor.rowcount > 0:
            rows = pcursor.fetchall()
            return rows
        else:
            return 0


def fetchall_query_to_dict(query: str, database=db):
    with database.pmdatabase.get_cursor(cursor_factory=psycopg2.extras.DictCursor) as pcursor:
        pcursor.execute(query)
        if pcursor.rowcount > 0:
            rows_dict = pcursor.fetchall()
            return rows_dict
        else:
            return 0


def fetchone_query_to_dict(query: str, database=db):
    with database.pmdatabase.get_cursor(cursor_factory=psycopg2.extras.DictCursor) as pcursor:
        pcursor.execute(query)
        if pcursor.rowcount > 0:
            row_dict = pcursor.fetchone()
            return row_dict
        else:
            return 0
