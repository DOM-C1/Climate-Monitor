"""This script is the full ETL pipeline for a single location."""

from os import environ as ENV

from dotenv import load_dotenv

from transform import gather_weather_data, gather_air_quality
from load import (get_db_connection, get_location_id, insert_weather_report,
                  insert_forecast, insert_weather_alert, insert_air_quality)


if __name__ == "__main__":

    load_dotenv()

    longitude = -2.99168
    latitude = 53.4071991

    weather = gather_weather_data(latitude, longitude)
    air_quality = gather_air_quality(latitude, longitude)

    connection = get_db_connection(ENV)

    loc_id = get_location_id(connection, latitude, longitude)

    
    weather_report_id = insert_weather_report(connection, loc_id)

    for w in weather:
        forecast_id = insert_forecast(connection, w["forecast"], weather_report_id)
        if w["warnings"]:
            for warning in w["warnings"]:
                insert_weather_alert(connection, warning, forecast_id)

    insert_air_quality(connection, air_quality, weather_report_id)