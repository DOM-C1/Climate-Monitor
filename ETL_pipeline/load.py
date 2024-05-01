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


def get_location_id(conn: connection, latitude: float, longitude: float) -> int:
    """Returns the location ID for a given latitude and longitude."""

    sql_query = """
        SELECT loc_id
        FROM location
        WHERE latitude = %s
        AND longitude = %s;
        """

    with conn.cursor() as cur:
        cur.execute(sql_query, (latitude, longitude))
        location_id = cur.fetchone()["loc_id"]

    return location_id


def insert_weather_report(conn: connection, location_id: int) -> int:
    """Returns a weather report ID from the database having inserted a weather report."""

    sql_query = """
        INSERT INTO weather_report
            (report_time, loc_id)
        VALUES
            (%s, %s)
        RETURNING weather_report_id;
        """

    with conn.cursor() as cur:
        cur.execute(sql_query, (datetime.now(), location_id))
        weather_report_id = cur.fetchone()
    conn.commit()

    return weather_report_id["weather_report_id"]


def check_forecasts(conn: connection, forecast: dict, location_id: int) -> int:
    """Check if a forecast with a matching timestamp and return it's id."""
    sql_query = f"""
        SELECT forecast_id FROM forecast AS f
        JOIN weather_report AS wr
        ON (wr.weather_report_id = f.weather_report_id)
        WHERE f.forecast_timestamp = '{forecast["forecast_timestamp"]}'
        AND wr.loc_id = {location_id}
        """
    with conn.cursor() as cur:
        cur.execute(sql_query)
        forecast_id = cur.fetchone()
    if forecast_id:
        return forecast_id["forecast_id"]
    return 0


def insert_forecast(conn: connection, forecast: dict, weather_report_id: int, location_id: int) -> int:
    """Returns the forecast ID from the database having inserted a forecast."""
    forecast_id = check_forecasts(conn, forecast, location_id)
    if forecast_id:
        sql_query = """UPDATE forecast as f 
                        SET
                        visibility = u.new_vis,
                        humidity = u.new_hum,
                        precipitation = u.new_prec,
                        precipitation_prob = u.new_prec_prob,
                        rainfall = u.new_rain,
                        snowfall = u.new_snow,
                        wind_speed = u.new_speed,
                        wind_direction = u.new_dir,
                        wind_gusts = u.new_gust,
                        lightning_potential = u.new_light,
                        uv_index = u.new_uv,
                        cloud_cover = u.new_cloud,
                        temperature = u.new_temp,
                        apparent_temp = u.new_apptemp,
                        weather_report_id = u.new_rep,
                        weather_code_id = u.new_code
                        FROM (VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ) AS u(forecast_id, new_vis, new_hum, new_prec, new_prec_prob, new_rain, 
                        new_snow, new_speed, new_dir, new_gust, new_light, new_uv, 
                        new_cloud, new_temp, new_apptemp, new_rep, new_code)
                        WHERE f.forecast_timestamp = %s
                        AND f.forecast_id = u.forecast_id
                        ;"""
        with conn.cursor() as cur:
            cur.execute(sql_query, (forecast_id,
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
                                    forecast["weather_code_id"],
                                    forecast["forecast_timestamp"]))
        conn.commit()
    else:
        sql_query = """
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
            cur.execute(sql_query, (forecast["forecast_timestamp"],
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
            forecast_id = cur.fetchone()["forecast_id"]
        conn.commit()

    return forecast_id


def insert_weather_alert(conn: connection, weather_alert: dict, forecast_id: int) -> None:
    """Inserts a weather alert into the database."""
    with conn.cursor() as cur:
        select_sql_query = """SELECT * FROM weather_alert
                        WHERE alert_type_id = %s
                        AND forecast_id = %s
                        AND severity_level_id = %s"""
        cur.execute(select_sql_query, (weather_alert["alert_type_id"],
                                       forecast_id,
                                       weather_alert["severity_type_id"]))
        alert = cur.fetchone()
        if not alert:
            insert_sql_query = """
                INSERT INTO weather_alert
                    (alert_type_id, forecast_id, severity_level_id)
                VALUES
                    (%s, %s, %s);
                """

            cur.execute(insert_sql_query, (weather_alert["alert_type_id"],
                                           forecast_id,
                                           weather_alert["severity_type_id"]))
        conn.commit()


def insert_air_quality(conn: connection, air_quality: dict, weather_report_id: int) -> None:
    """Inserts an air quality reading to the database."""

    sql_query = """
        INSERT INTO air_quality
            (o3_concentration, severity_level_id, weather_report_id)
        VALUES
            (%s, %s, %s);
        """

    with conn.cursor() as cur:
        cur.execute(sql_query, (air_quality["o3_concentration"],
                                air_quality["severity_id"],
                                weather_report_id))
    conn.commit()
