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

def fetchone_query(query: str, database=db):
    with database.pmdatabase.get_cursor() as pcursor:
        pcursor.execute(query)
        if pcursor.rowcount > 0:
            row = pcursor.fetchone()
            return row
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

