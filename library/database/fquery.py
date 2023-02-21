import psycopg2.extras
import library.database as db

db.global_db_connect()

def fetchall_query(query: str, database=db):
    with database.pmdatabase.get_cursor() as pcursor:
        pcursor.execute(query)
        if pcursor.rowcount > 0:
            rows = pcursor.fetchall()
            return rows
        elif pcursor.rowcount == 0:
            return 0
        else:
            return None


def fetchall_query_to_dict(query: str, database=db):
    with database.pmdatabase.get_cursor(cursor_factory=psycopg2.extras.DictCursor) as pcursor:
        pcursor.execute(query)
        if pcursor.rowcount > 0:
            rows_dict = pcursor.fetchall()
            return rows_dict
        elif pcursor.rowcount == 0:
            return 0
        else:
            return None


def fetchone_query_to_dict(query: str, database=db):
    with database.pmdatabase.get_cursor(cursor_factory=psycopg2.extras.DictCursor) as pcursor:
        pcursor.execute(query)
        if pcursor.rowcount > 0:
            row_dict = pcursor.fetchone()
            return row_dict
        elif pcursor.rowcount == 0:
            return 0
        else:
            return None


def make_update_query_by_dict(table_name, data_dict, where_dict=None):
    set_clause = ", ".join([f"{key} = {value}" for key, value in data_dict.items()])
    where_clause = " AND ".join([f"{key} = {value}" for key, value in where_dict.items()])

    if where_dict is not None:
        update_query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
    else:
        update_query = f"UPDATE {table_name} SET {set_clause}"

    return update_query


"""
Test Code
a_dict = {"aaa" : "123", "bbb" : "456"}
b_dict = {"qwe" : "12345", "wer" : "12345", "ert" : "123456"}

print(make_update_query_by_dict("black.hello",a_dict, a_dict))
"""
