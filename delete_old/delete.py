"""This script deletes the out of date data from the database using sql statements."""

from os import environ as ENV
from psycopg2 import connect
from psycopg2.extensions import connection
from dotenv import load_dotenv


def get_db_connection(config: dict) -> connection:
    """Connect to the database."""

    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def delete_weather_alert(conn: connection) -> None:
    """Delete any weather update that is out of date and has been notified."""

    sql_query = """
    DELETE FROM weather_alert AS WA
    WHERE (WA.forecast_id in 
    (SELECT forecast_id
    FROM forecast
    WHERE forecast_timestamp < CURRENT_TIMESTAMP)) OR
    (WA.severity_level_id = 4);"""

    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()


def delete_weather_forecast(conn: connection) -> None:
    """Delete any forecast that is out of date."""

    sql_query = """DELETE FROM forecast
                    WHERE (forecast_timestamp < CURRENT_TIMESTAMP - INTERVAL '30 minutes') AND 
                    (forecast_id NOT IN (SELECT WA.forecast_id FROM weather_alert AS WA));
                """

    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()


def delete_air_quality(conn: connection) -> None:
    """Delete out of date air quality reports."""

    sql_query = """DELETE FROM air_quality WHERE
                weather_report_id IN (SELECT WR.weather_report_id FROM weather_report 
                AS WR WHERE WR.report_time < CURRENT_TIMESTAMP - INTERVAL '1 day');
                """

    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()


def delete_weather_reports(conn: connection) -> None:
    """Delete out of date weather reports."""

    sql_query = """DELETE FROM weather_report WHERE
    (weather_report_id NOT IN (SELECT F.weather_report_id FROM forecast AS F))
    AND (weather_report_id NOT IN (SELECT AQ.weather_report_id FROM air_quality AS AQ));
                """

    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()


def delete_flood_warnings(conn: connection) -> None:
    """Delete out of date flood warnings."""

    sql_query = """DELETE FROM flood_warnings
    WHERE time_raised < CURRENT_TIMESTAMP - INTERVAL '7 days';"""

    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()


def clear_the_data(config: connection) -> None:
    """Delete all out of the out of date data."""

    with get_db_connection(config) as conn:
        delete_weather_alert(conn)
        delete_weather_forecast(conn)
        delete_air_quality(conn)
        delete_weather_reports(conn)
        delete_flood_warnings(conn)
    conn.close()


def handler(event: list[dict], context: dict = None) -> None:
    """AWS Lambda function handler of the delete function."""

    load_dotenv()
    clear_the_data(ENV)
