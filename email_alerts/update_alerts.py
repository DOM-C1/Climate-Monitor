"""Update the alerts within the database to show they have been notified."""

from os import environ as ENV

from psycopg2 import connect
from psycopg2.extensions import connection


TABLE_ID_POS = 1


def get_db_connection(config: dict):
    """Connect to the database."""
    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def update_weather_alert(conn: connection) -> bool:
    """Update the weather alert table based on forecast_id and alert_type_id. 
    Notified is updated to to true."""
    sql_query = """UPDATE weather_alert
                        SET
                        notified = True
                        ;"""
    with conn.cursor() as cur:
        cur.execute(sql_query)
    conn.commit()


def update_flood_alert(conn: connection, table_id: int) -> bool:
    """Update the flood alert table so notified is true."""
    sql_query = """UPDATE flood_warnings
                        SET
                        notified = True
                        WHERE flood_id = %s
                        ;"""
    with conn.cursor() as cur:
        cur.execute(sql_query, (table_id,))
    conn.commit()


def update_air_alert(conn: connection, table_id: int) -> bool:
    """Update the air quality table so notified is true."""
    sql_query = """UPDATE air_quality
                        SET
                        notified = True
                        WHERE air_quality_id = %s
                        ;"""

    with conn.cursor() as cur:
        cur.execute(sql_query, (table_id,))
    conn.commit()


def update_all_alert_tables(config: dict, recipients: dict) -> None:
    """Sorts through all the alerts and updates their respective row in the database."""

    weather_alert = ENV['WEATHER_WARNING_TABLE']
    flood_alert = ENV['FLOOD_WARNING_TABLE']
    air_quality = ENV['AIR_QUALITY_TABLE']
    with get_db_connection(config) as conn:
        for key in recipients.keys():
            if not recipients.get(key):
                continue
            for alert in recipients.get(key):
                if alert[0] == weather_alert:
                    update_weather_alert(conn)
                if alert[0] == air_quality:
                    update_air_alert(conn, alert[TABLE_ID_POS])
                if alert[0] == flood_alert:
                    update_flood_alert(conn, alert[TABLE_ID_POS])
    conn.close()
    print('Finished')
