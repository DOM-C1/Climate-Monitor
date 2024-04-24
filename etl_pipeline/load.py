"""This file is the load aspect of the cloud monitor ETL Pipeline."""

from os import environ as ENV
from datetime import datetime

from dotenv import load_dotenv
from psycopg2 import connect, Connection


def get_db_connection(config: dict) -> Connection:
    """Returns a connection to the database."""

    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def insert_weather_report(conn: Connection, location_id: int) -> int:
    """Returns a weather report ID from the database having inserted a weather report."""

    q = """
        INSERT INTO weather_report
            (report_time, loc_id)
        VALUES
            (%s, %s)
        RETURNING weather_report_id;
        """

    with conn.cursor() as cur:
        cur.execute(q, (datetime.now(), location_id))
        weather_report_id = cur.fetchone()
    conn.commit()

    return weather_report_id


def insert_forecast(conn: Connection, forecast: dict, weather_report_id: int) -> int:
    """Returns the forecast ID from the database having inserted a forecast."""

    forecast["weather_report_id"] = weather_report_id

    q = """
        INSERT INTO forecast
            {cols}
        VALUES
            {vals}
        RETURNING forecast_id;
        """.format(cols=forecast.keys(), vals=forecast.values())

    with conn.cursor() as cur:
        cur.execute(q)
        forecast_id = cur.fetchone()
    conn.commit()

    return forecast_id


def insert_weather_alert(conn: Connection, weather_alert: dict, forecast_id: int) -> None:
    """Inserts a weather alert into the database."""

    q = """
        INSERT INTO weather_alert
            (alert_type_id, forecast_id, severity_level_id)
        VALUES
            (%s, %s);
        """

    with conn.cursor() as cur:
        cur.execute(q, (weather_alert["alert_type_id"],
                        forecast_id,
                        weather_alert["severity_level_id"]))
    conn.commit()


def insert_flood_warning(conn: Connection, flood_warning: dict, location_id: int) -> None:
    """Inserts a flood warning into the database."""

    q = """
        INSERT INTO flood_warnings
            (severity_level_id, time_raised, loc_id)
        VALUES
            (%s, %s, %s);
        """

    with conn.cursor() as cur:
        cur.execute(q, (flood_warning["severity_level_id"],
                        flood_warning["time_raised"],
                        location_id))
    conn.commit()


def insert_air_quality(conn: Connection, air_quality: dict, weather_report_id: int) -> None:
    """Inserts an air quality reading to the database."""

    q = """
        INSERT INTO air_quality
            (o3_concentration, severity_level_id, weather_report_id)
        VALUES
            (%s, %s, %s);
        """

    with conn.cursor() as cur:
        cur.execute(q , (air_quality["o3_concentration"],
                         air_quality["severity_level_id"],
                         weather_report_id))
    conn.commit()