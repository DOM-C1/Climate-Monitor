"""This file is the load aspect of the cloud monitor ETL Pipeline."""

from datetime import datetime

from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection


def get_db_connection(config: dict) -> connection:
    """Returns a connection to the database."""

    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"],
        cursor_factory=RealDictCursor
    )


def get_location_id(conn:connection, latitude: float, longitude: float) -> int:
    """Returns the location ID for a given latitude and longitude."""

    q = """
        SELECT loc_id
        FROM location
        WHERE latitude = %s
        AND longitude = %s;
        """

    with conn.cursor() as cur:
        cur.execute(q, (latitude, longitude))
        location_id = cur.fetchone()

    return location_id["loc_id"]


def insert_weather_report(conn: connection, location_id: int) -> int:
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

    return weather_report_id["weather_report_id"]


def insert_forecast(conn: connection, forecast: dict, weather_report_id: int) -> int:
    """Returns the forecast ID from the database having inserted a forecast."""

    q = """
        INSERT INTO forecast
            (forecast_timestamp, visibility, humidity, precipitation,
             precipitation_prob, rainfall, snowfall, wind_speed, wind_direction,
             wind_gusts, lightning_potential, uv_index, cloud_cover, temperature,
             apparent_temp, weather_report_id, weather_code_id)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING forecast_id;
        """

    with conn.cursor() as cur:
        cur.execute(q, (forecast["forecast_timestamp"],
                        forecast["visibility"],
                        forecast["humidity"],
                        forecast["precipitation"],
                        forecast["precipitation_prob"],
                        forecast["rainfall"],
                        forecast["snowfall"],
                        forecast["wind_speed"],
                        forecast["wind_direction"],
                        forecast["wind_gusts"],
                        forecast["lightning_potential"],
                        forecast["uv_index"],
                        forecast["cloud_cover"],
                        forecast["temperature"],
                        forecast["apparent_temperature"],
                        weather_report_id,
                        forecast["weather_code_id"]))
        forecast_id = cur.fetchone()
    conn.commit()

    return forecast_id["forecast_id"]


def insert_weather_alert(conn: connection, weather_alert: dict, forecast_id: int) -> None:
    """Inserts a weather alert into the database."""

    # TODO: check for matching alert in the database.

    q = """
        INSERT INTO weather_alert
            (alert_type_id, forecast_id, severity_level_id)
        VALUES
            (%s, %s, %s);
        """

    with conn.cursor() as cur:
        cur.execute(q, (weather_alert["alert_type_id"],
                        forecast_id,
                        weather_alert["severity_type_id"]))
    conn.commit()


def insert_air_quality(conn: connection, air_quality: dict, weather_report_id: int) -> None:
    """Inserts an air quality reading to the database."""

    q = """
        INSERT INTO air_quality
            (o3_concentration, severity_level_id, weather_report_id)
        VALUES
            (%s, %s, %s);
        """

    with conn.cursor() as cur:
        cur.execute(q , (air_quality["o3_concentration"],
                         air_quality["severity_id"],
                         weather_report_id))
    conn.commit()