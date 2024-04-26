

from os import environ as ENV

from psycopg2 import connect
from psycopg2.extensions import connection


def get_db_connection(config: dict):
    """Connect to the database."""
    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def update_weather_alert(conn: connection, table_id: int) -> bool:
    """update the air quality table notified column notified to true."""
    sql_query = """UPDATE weather_alert 
                        SET
                        notified = True
                        WHERE alert_id = %s
                        ;"""
    try:
        with conn.cursor() as cur:
            cur.execute(sql_query, (table_id,))
        conn.commit()
        return True
    except:
        return False


def update_flood_alert(conn: connection, table_id: int) -> bool:
    """update the air quality table notified column notified to true."""
    sql_query = """UPDATE flood_warnings 
                        SET
                        notified = True
                        WHERE flood_id = %s
                        ;"""
    try:
        with conn.cursor() as cur:
            cur.execute(sql_query, (table_id,))
        conn.commit()
        return True
    except:
        return False


def update_air_alert(conn: connection, table_id: int) -> bool:
    """update the air quality table notified column to true."""
    sql_query = """UPDATE air_quality
                        SET
                        notified = True
                        WHERE air_quality_id = %s
                        ;"""
    try:
        with conn.cursor() as cur:
            cur.execute(sql_query, (table_id,))
        conn.commit()
        return True
    except:
        return False


def update_all_alert_tables(config: dict, recipients: dict) -> None:
    """sorts through all the alerts and updates their respective row in the database."""

    with get_db_connection(config) as conn:
        for key in recipients.keys():
            if not recipients.get(key):
                continue
            for alert in recipients.get(key):
                if alert[0] == 'weather_alert':
                    update_weather_alert(conn, alert[1])
                if alert[0] == 'air_quality':
                    update_air_alert(conn, alert[1])
                if alert[0] == 'flood_warnings':
                    update_flood_alert(conn, alert[1])
    print('Finished')
