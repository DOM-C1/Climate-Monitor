"""This file provides useful functions needed to do databse related things."""
from psycopg2 import connect


def get_db_connection(config: dict):
    """Connect to the database."""
    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def add_to_database(table: str, data: dict, conn: connect) -> None:
    """This will be used to add to the database securely using parameterized queries."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s' for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    values = list(data.values())
    with conn.cursor() as cur:
        cur.execute(query, values)
        conn.commit()


def get_id(table: str, column: str, value: str, conn: connect) -> int:
    """Given the table name, column and a value, checks whether that value exists and return it's ID if 
       if it does exist; a return value of -1 indicates that value doesn't exist."""
    query = f"SELECT * FROM {table} WHERE {column} = %s"
    with conn.cursor() as cur:
        cur.execute(query, (value,))
        result = cur.fetchall()
        if result:
            return result[0][0]
        return -1
