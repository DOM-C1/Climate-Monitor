"""This script is the full ETL pipeline for a single location."""

from os import environ as ENV

from dotenv import load_dotenv
from psycopg2.extensions import connection

from extract import async_api_calls
from transform import gather_weather_data, gather_air_quality
from load import (get_db_connection, get_location_id, insert_weather_report,
                  insert_forecast, insert_weather_alert, insert_air_quality)


def pipeline(conn: connection, config: dict, latitude: float, longitude: float) -> None:
    """Loads data from weather APIs to a database."""

    api_data = async_api_calls(latitude, longitude, config)

    weather = gather_weather_data(api_data["weather_for_24hr"],
                                  api_data["weather_for_week"])
    air_quality = gather_air_quality(api_data["air_quality"])

    loc_id = get_location_id(conn, latitude, longitude)
    weather_report_id = insert_weather_report(conn, loc_id)

    for w in weather:
        forecast_id = insert_forecast(
            conn, w["forecast"], weather_report_id, loc_id)
        if w["warnings"]:
            for warning in w["warnings"]:
                insert_weather_alert(conn, warning, forecast_id)

    insert_air_quality(conn, air_quality, weather_report_id)


def handler(event: list[dict], context: dict = None) -> None:
    """AWS Lambda function handler of the pipeline for multiple locations."""

    load_dotenv()
    connection = get_db_connection(ENV)

    for e in event:
        pipeline(connection, ENV, e["latitude"], e["longitude"])

    connection.close()
