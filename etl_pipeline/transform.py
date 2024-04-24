"""Transform a JSON of a single weather report into pandas DataFrames for use in load.py"""
from os import environ as ENV

import pandas as pd
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


def get_db_connection(config):
    """Connect to the database"""
    return psycopg2.connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def gather_data(json_data, air_qualities, key):
    data = pd.DataFrame(json_data[key])
    data = data.map(lambda x: 0 if x is None or x == 'null' else x)
    return list(data.itertuples(index=False, name=None))



if __name__ == "__main__":
    test_json_15min = {"latitude": 52.52, "longitude": 13.419998, "generationtime_ms": 0.32198429107666016, "utc_offset_seconds": 0, "timezone": "GMT", "timezone_abbreviation": "GMT", "elevation": 38.0, "minutely_15_units": {"time": "iso8601", "apparent_temperature": "°C", "cloud_cover": "%", "relative_humidity_2m": "%", "lightning_potential": "J/kg", "precipitation": "mm", "precipitation_probability": "%", "rain": "mm", "snowfall": "cm", "temperature_2m": "°C", "uv_index": "", "visibility": "m", "wind_direction_10m": "°", "wind_gusts_10m": "km/h", "wind_speed_10m": "km/h", "weather_code": "wmo code"}, "minutely_15": {"time": ["2024-04-24T12:00", "2024-04-24T12:15", "2024-04-24T12:30", "2024-04-24T12:45", "2024-04-24T13:00", "2024-04-24T13:15", "2024-04-24T13:30", "2024-04-24T13:45", "2024-04-24T14:00", "2024-04-24T14:15", "2024-04-24T14:30", "2024-04-24T14:45", "2024-04-24T15:00", "2024-04-24T15:15", "2024-04-24T15:30", "2024-04-24T15:45", "2024-04-24T16:00", "2024-04-24T16:15", "2024-04-24T16:30", "2024-04-24T16:45", "2024-04-24T17:00", "2024-04-24T17:15", "2024-04-24T17:30", "2024-04-24T17:45", "2024-04-24T18:00", "2024-04-24T18:15", "2024-04-24T18:30", "2024-04-24T18:45", "2024-04-24T19:00", "2024-04-24T19:15", "2024-04-24T19:30", "2024-04-24T19:45", "2024-04-24T20:00", "2024-04-24T20:15", "2024-04-24T20:30", "2024-04-24T20:45", "2024-04-24T21:00", "2024-04-24T21:15", "2024-04-24T21:30", "2024-04-24T21:45", "2024-04-24T22:00", "2024-04-24T22:15", "2024-04-24T22:30", "2024-04-24T22:45", "2024-04-24T23:00", "2024-04-24T23:15", "2024-04-24T23:30", "2024-04-24T23:45", "2024-04-25T00:00", "2024-04-25T00:15", "2024-04-25T00:30", "2024-04-25T00:45", "2024-04-25T01:00", "2024-04-25T01:15", "2024-04-25T01:30", "2024-04-25T01:45", "2024-04-25T02:00", "2024-04-25T02:15", "2024-04-25T02:30", "2024-04-25T02:45", "2024-04-25T03:00", "2024-04-25T03:15", "2024-04-25T03:30", "2024-04-25T03:45", "2024-04-25T04:00", "2024-04-25T04:15", "2024-04-25T04:30", "2024-04-25T04:45", "2024-04-25T05:00", "2024-04-25T05:15", "2024-04-25T05:30", "2024-04-25T05:45", "2024-04-25T06:00", "2024-04-25T06:15", "2024-04-25T06:30", "2024-04-25T06:45", "2024-04-25T07:00", "2024-04-25T07:15", "2024-04-25T07:30", "2024-04-25T07:45", "2024-04-25T08:00", "2024-04-25T08:15", "2024-04-25T08:30", "2024-04-25T08:45", "2024-04-25T09:00", "2024-04-25T09:15", "2024-04-25T09:30", "2024-04-25T09:45", "2024-04-25T10:00", "2024-04-25T10:15", "2024-04-25T10:30", "2024-04-25T10:45", "2024-04-25T11:00", "2024-04-25T11:15", "2024-04-25T11:30", "2024-04-25T11:45", "2024-04-25T12:00"], "apparent_temperature": [6.8, 6.8, 6.6, 6.3, 6.2, 6.2, 6.3, 5.9, 5.6, 5.5, 5.7, 5.8, 6.0, 5.9, 5.9, 5.5, 5.3, 5.2, 5.0, 4.8, 4.5, 4.6, 4.9, 5.1, 5.1, 4.9, 4.5, 4.1, 3.7, 3.5, 3.4, 3.2, 3.1, 3.0, 2.8, 2.7, 2.6, 2.4, 2.3, 2.1, 2.0, 1.9, 1.8, 1.8, 1.7, 1.6, 1.5, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.5, 0.4, 0.3, 0.2, -0.0, -0.2, -0.3, -0.4, -0.6, -0.7, -0.8, -0.8, -0.7, -0.7, -0.6, -0.4, -0.2, 0.1, 0.3, 0.6, 0.9, 1.2, 1.5, 1.8, 2.1, 2.6, 2.9, 3.2, 3.5, 3.6, 3.8, 3.9, 3.9, 3.9, 4.0, 4.1, 4.2, 4.4, 4.7, 5.0, 5.5, 5.8, 6.0], "cloud_cover": [90, 92, 93, 95, 96, 97, 98, 99, 100, 100, 100, 100, 100, 100, 99, 99, 98, 96, 94, 92, 90, 93, 95, 98, 100, 99, 98, 96, 95, 83, 72, 60, 48, 45, 43, 40, 37, 28, 19, 9, 0, 0, 0, 0, 0, 22, 44, 66, 88, 76, 64, 52, 40, 47, 55, 62, 69, 74, 78, 83, 87, 86, 86, 85, 84, 88, 92, 96, 100, 100, 100, 100, 100, 100, 100, 99, 99, 99, 100, 100, 100, 99, 99, 98, 97, 98, 99, 99, 100, 99, 98, 96, 95, 94, 94, 93, 92], "relative_humidity_2m": [48, 49, 51, 53, 56, 59, 63, 66, 68, 67, 65, 62, 61, 62, 64, 67, 68, 68, 67, 66, 66, 67, 69, 71, 73, 74, 74, 74, 75, 76, 77, 78, 79, 80, 82, 83, 84, 84, 84, 84, 85, 86, 88, 90, 92, 93, 93, 94, 94, 94, 95, 95, 95, 95, 94, 94, 93, 92, 92, 91, 91, 91, 91, 92, 92, 92, 92, 91, 91, 90, 90, 89, 88, 87, 85, 83, 81, 78, 75, 72, 70, 68, 67, 66, 65, 65, 66, 67, 67, 67, 66, 65, 64, 62, 60, 58, 57], "lightning_potential": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "precipitation": [0.00, 0.00, 0.10, 0.10, 0.00, 0.00, 0.00, 0.10, 0.10, 0.10, 0.00, 0.00, 0.00, 0.10, 1.50, 1.50, 0.00, 0.10, 0.80, 0.20, 0.00, 0.00, 0.00, 0.00, 0.00, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.10, 0.20, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], "precipitation_probability": [58, 58, 57, 57, 56, 56, 55, 55, 54, 54, 53, 53, 52, 52, 51, 51, 51, 50, 50, 50, 49, 49, 49, 48, 48, 46, 45, 43, 42, 40, 39, 37, 35, 34, 32, 31, 29, 28, 26, 25, 24, 22, 21, 20, 18, 17, 16, 14, 13, 12, 11, 11, 10, 9, 8, 7, 6, 6, 5, 4, 3, 4, 4, 5, 5, 6, 7, 7, 8, 8, 9, 9, 10, 12, 14, 16, 18, 20, 23, 25, 27, 29, 31, 33, 35, 38, 41, 43, 46, 49, 52, 54, 57, 60, 63, 65, 68], "rain": [
        0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 1.50, 1.40, 0.00, 0.10, 0.80, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.10, 0.20, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], "snowfall": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], "temperature_2m": [10.4, 10.3, 10.1, 9.8, 9.6, 9.2, 8.9, 8.7, 8.6, 8.6, 8.8, 8.9, 9.0, 8.9, 8.6, 8.2, 8.0, 7.8, 7.4, 7.2, 7.1, 7.1, 7.2, 7.3, 7.3, 7.2, 6.9, 6.6, 6.3, 6.2, 6.0, 5.8, 5.7, 5.5, 5.3, 5.2, 5.0, 4.8, 4.8, 4.6, 4.5, 4.3, 4.2, 4.1, 4.0, 3.8, 3.8, 3.6, 3.5, 3.4, 3.3, 3.2, 3.2, 3.1, 3.0, 2.9, 2.8, 2.7, 2.5, 2.5, 2.3, 2.2, 2.1, 2.0, 2.0, 2.0, 2.0, 2.0, 2.1, 2.2, 2.5, 2.7, 3.0, 3.3, 3.7, 4.1, 4.5, 4.9, 5.3, 5.8, 6.2, 6.4, 6.6, 6.7, 6.8, 6.9, 7.0, 7.1, 7.2, 7.2, 7.4, 7.6, 7.8, 8.1, 8.6, 8.9, 9.1], "uv_index": [3.70, 3.85, 4.05, 4.15, 4.20, 4.20, 4.10, 4.00, 3.85, 3.70, 3.55, 3.35, 3.10, 2.75, 2.35, 1.95, 1.60, 1.35, 1.20, 1.05, 0.90, 0.75, 0.60, 0.45, 0.30, 0.20, 0.10, 0.05, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.05, 0.10, 0.15, 0.25, 0.35, 0.50, 0.65, 0.80, 0.95, 1.10, 1.20, 1.30, 1.35, 1.35, 1.35, 1.35, 1.35, 1.30, 1.25, 1.30, 1.40, 1.55, 1.75, 2.00, 2.30, 2.70, 3.05, 3.25, 3.25, 3.05, 2.85, 2.65], "visibility": [8900.00, 12460.00, 16020.00, 19560.00, 23120.00, 23380.00, 23640.00, 23880.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 23980.00, 23800.00, 23640.00, 23460.00, 23400.00, 23360.00, 23300.00, 23240.00, 23460.00, 23700.00, 23920.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00, 22180.00, 20240.00, 18280.00, 16320.00, 12880.00, 9440.00, 5980.00, 2540.00, 7940.00, 13340.00, 18740.00, 24140.00, 24140.00, 24140.00, 24140.00, 24140.00], "wind_direction_10m": [202, 212, 225, 237, 241, 231, 199, 164, 148, 138, 130, 124, 121, 127, 144, 162, 171, 165, 142, 112, 95, 95, 117, 144, 156, 146, 135, 122, 118, 118, 123, 130, 132, 132, 135, 135, 135, 135, 135, 138, 138, 141, 148, 151, 156, 156, 149, 142, 138, 138, 141, 141, 148, 151, 157, 162, 166, 171, 176, 176, 180, 184, 189, 193, 193, 193, 189, 184, 180, 176, 176, 176, 176, 180, 183, 186, 188, 190, 192, 192, 192, 190, 188, 185, 183, 183, 183, 182, 182, 182, 185, 187, 190, 195, 204, 212, 216], "wind_gusts_10m": [31.0, 32.4, 33.8, 34.9, 36.4, 34.9, 33.8, 32.4, 31.0, 31.3, 31.7, 32.0, 32.4, 32.4, 32.8, 32.8, 32.8, 32.0, 31.0, 30.2, 29.2, 24.8, 20.5, 16.2, 11.9, 14.0, 16.6, 18.7, 20.9, 19.1, 17.3, 15.1, 13.3, 13.0, 12.6, 11.9, 11.5, 11.2, 11.2, 10.8, 10.4, 10.4, 10.1, 10.1, 9.7, 9.7, 9.4, 9.4, 9.0, 9.0, 9.4, 9.4, 9.4, 9.4, 9.7, 9.7, 9.7, 9.7, 9.7, 9.4, 9.4, 9.7, 10.1, 10.1, 10.4, 10.4, 10.4, 10.4, 10.4, 11.2, 11.5, 12.2, 12.6, 14.4, 16.2, 17.6, 19.4, 19.8, 20.2, 20.2, 20.5, 20.5, 20.5, 20.5, 20.5, 21.6, 22.3, 23.4, 24.1, 23.8, 23.0, 22.7, 22.0, 22.0, 22.3, 22.7, 22.7], "wind_speed_10m": [9.7, 9.4, 9.7, 9.9, 9.5, 7.9, 6.5, 7.9, 9.4, 9.7, 9.4, 9.1, 8.4, 7.7, 6.7, 6.8, 6.6, 5.6, 4.1, 3.9, 4.3, 4.0, 3.2, 3.1, 3.5, 3.9, 4.6, 5.5, 6.1, 6.1, 6.0, 5.6, 5.4, 5.4, 5.1, 5.1, 5.1, 5.1, 5.1, 4.8, 4.8, 4.6, 4.7, 4.5, 4.3, 4.3, 4.2, 4.1, 4.3, 4.3, 4.6, 4.6, 4.7, 4.5, 4.7, 4.6, 4.5, 4.4, 4.7, 4.7, 4.7, 4.7, 4.7, 4.8, 4.8, 4.8, 4.7, 4.7, 4.7, 4.7, 4.7, 4.7, 5.1, 5.8, 6.5, 7.2, 8.0, 8.4, 8.8, 8.8, 8.8, 8.4, 8.0, 7.6, 7.2, 7.6, 7.9, 8.3, 8.6, 8.6, 8.7, 8.7, 8.4, 8.2, 7.9, 8.1, 8.0], "weather_code": [3, 3, 61, 61, 61, 61, 80, 80, 80, 80, 80, 80, 80, 80, 95, 95, 95, 95, 80, 80, 80, 80, 3, 3, 3, 3, 80, 80, 80, 80, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 80, 80, 80, 80, 80, 80, 80, 80, 3, 3, 3]}}
    test_json_hour = {"latitude":52.52,"longitude":13.4,"generationtime_ms":0.33605098724365234,"utc_offset_seconds":0,"timezone":"GMT","timezone_abbreviation":"GMT","elevation":30.0,"hourly_units":{"time":"iso8601","apparent_temperature":"°C","cloud_cover":"%","relative_humidity_2m":"%","lightning_potential":"J/kg","precipitation":"mm","precipitation_probability":"%","rain":"mm","snowfall":"cm","temperature_2m":"°C","uv_index":"","visibility":"m","wind_direction_10m":"°","wind_gusts_10m":"km/h","wind_speed_10m":"km/h","weather_code":"wmo code"},"hourly":{"time":["2024-04-25T12:00","2024-04-25T13:00","2024-04-25T14:00","2024-04-25T15:00","2024-04-25T16:00","2024-04-25T17:00","2024-04-25T18:00","2024-04-25T19:00","2024-04-25T20:00","2024-04-25T21:00","2024-04-25T22:00","2024-04-25T23:00","2024-04-26T00:00","2024-04-26T01:00","2024-04-26T02:00","2024-04-26T03:00","2024-04-26T04:00","2024-04-26T05:00","2024-04-26T06:00","2024-04-26T07:00","2024-04-26T08:00","2024-04-26T09:00","2024-04-26T10:00","2024-04-26T11:00","2024-04-26T12:00","2024-04-26T13:00","2024-04-26T14:00","2024-04-26T15:00","2024-04-26T16:00","2024-04-26T17:00","2024-04-26T18:00","2024-04-26T19:00","2024-04-26T20:00","2024-04-26T21:00","2024-04-26T22:00","2024-04-26T23:00","2024-04-27T00:00","2024-04-27T01:00","2024-04-27T02:00","2024-04-27T03:00","2024-04-27T04:00","2024-04-27T05:00","2024-04-27T06:00","2024-04-27T07:00","2024-04-27T08:00","2024-04-27T09:00","2024-04-27T10:00","2024-04-27T11:00","2024-04-27T12:00","2024-04-27T13:00","2024-04-27T14:00","2024-04-27T15:00","2024-04-27T16:00","2024-04-27T17:00","2024-04-27T18:00","2024-04-27T19:00","2024-04-27T20:00","2024-04-27T21:00","2024-04-27T22:00","2024-04-27T23:00","2024-04-28T00:00","2024-04-28T01:00","2024-04-28T02:00","2024-04-28T03:00","2024-04-28T04:00","2024-04-28T05:00","2024-04-28T06:00","2024-04-28T07:00","2024-04-28T08:00","2024-04-28T09:00","2024-04-28T10:00","2024-04-28T11:00","2024-04-28T12:00","2024-04-28T13:00","2024-04-28T14:00","2024-04-28T15:00","2024-04-28T16:00","2024-04-28T17:00","2024-04-28T18:00","2024-04-28T19:00","2024-04-28T20:00","2024-04-28T21:00","2024-04-28T22:00","2024-04-28T23:00","2024-04-29T00:00","2024-04-29T01:00","2024-04-29T02:00","2024-04-29T03:00","2024-04-29T04:00","2024-04-29T05:00","2024-04-29T06:00","2024-04-29T07:00","2024-04-29T08:00","2024-04-29T09:00","2024-04-29T10:00","2024-04-29T11:00","2024-04-29T12:00","2024-04-29T13:00","2024-04-29T14:00","2024-04-29T15:00","2024-04-29T16:00","2024-04-29T17:00","2024-04-29T18:00","2024-04-29T19:00","2024-04-29T20:00","2024-04-29T21:00","2024-04-29T22:00","2024-04-29T23:00","2024-04-30T00:00","2024-04-30T01:00","2024-04-30T02:00","2024-04-30T03:00","2024-04-30T04:00","2024-04-30T05:00","2024-04-30T06:00","2024-04-30T07:00","2024-04-30T08:00","2024-04-30T09:00","2024-04-30T10:00","2024-04-30T11:00","2024-04-30T12:00","2024-04-30T13:00","2024-04-30T14:00","2024-04-30T15:00","2024-04-30T16:00","2024-04-30T17:00","2024-04-30T18:00","2024-04-30T19:00","2024-04-30T20:00","2024-04-30T21:00","2024-04-30T22:00","2024-04-30T23:00","2024-05-01T00:00","2024-05-01T01:00","2024-05-01T02:00","2024-05-01T03:00","2024-05-01T04:00","2024-05-01T05:00","2024-05-01T06:00","2024-05-01T07:00","2024-05-01T08:00","2024-05-01T09:00","2024-05-01T10:00","2024-05-01T11:00","2024-05-01T12:00"],"apparent_temperature":[6.1,5.9,6.2,6.4,6.1,6.4,5.6,4.6,4.4,3.7,3.1,2.3,2.0,1.5,1.1,0.4,-0.1,0.1,1.5,3.4,5.4,7.1,8.3,8.7,8.8,9.3,9.8,9.8,10.1,10.1,10.2,9.2,8.2,7.4,6.6,6.2,5.6,5.2,5.1,4.8,4.2,4.4,6.1,8.2,10.6,13.3,15.4,14.9,16.2,16.7,16.7,16.7,16.8,16.7,15.9,14.6,12.9,11.4,10.4,9.8,9.2,8.6,8.1,7.8,7.9,8.2,9.0,10.6,12.7,14.8,16.6,18.4,19.7,20.5,20.8,20.7,20.6,20.3,19.6,18.5,17.0,15.8,15.0,14.6,14.1,13.5,12.9,12.6,12.8,13.3,13.6,12.0,12.7,13.7,15.0,16.9,18.6,19.1,18.7,18.1,17.6,16.7,15.8,15.1,14.5,13.7,13.1,12.5,11.9,11.0,10.2,9.6,9.4,9.5,10.0,11.4,13.3,14.8,15.8,16.5,17.2,17.7,17.9,18.0,18.2,18.4,18.4,17.8,16.9,16.1,15.7,15.5,15.2,14.9,14.3,13.4,12.0,10.5,9.6,9.7,10.3,10.9,11.4,12.2,12.7],"cloud_cover":[92,92,76,89,100,99,100,100,96,91,97,100,99,92,3,1,2,29,0,1,77,96,87,94,73,99,94,96,86,83,81,76,85,53,46,59,33,79,98,100,98,49,1,4,0,0,26,52,50,36,23,9,6,3,0,3,7,10,7,3,0,27,54,81,87,94,100,100,100,100,74,48,22,41,60,79,86,93,100,100,100,100,100,100,100,98,97,95,97,98,100,100,100,100,86,73,59,68,76,85,85,84,84,77,69,62,75,87,100,97,94,91,93,96,98,98,97,97,97,96,96,97,99,100,90,80,70,76,81,87,89,92,94,96,98,100,100,100,100,86,73,59,64,68,73],"relative_humidity_2m":[57,58,48,52,58,54,63,73,76,80,82,86,88,90,92,90,90,87,80,72,63,56,47,41,39,37,36,39,44,48,57,64,68,67,67,69,71,74,74,75,77,77,72,64,57,50,47,49,51,49,45,43,43,45,48,53,60,65,68,70,72,73,75,75,75,75,73,70,65,61,57,54,51,49,47,47,49,53,57,62,68,72,73,73,73,75,77,78,78,78,78,71,65,60,55,50,47,46,47,49,52,56,60,65,71,77,82,87,90,90,88,85,81,76,70,64,57,53,53,56,60,64,69,73,75,76,78,81,86,89,91,93,93,92,90,88,87,85,82,75,67,59,52,46,42],"lightning_potential":[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,'null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null','null'],"precipitation":[0.00,0.30,0.00,0.00,0.00,0.00,0.10,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.10,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.20,0.20,0.20,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.10,0.10,0.10,0.20,0.20,0.20,0.00,0.00,0.00,0.00,0.00,0.00,0.30,0.30,0.30,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00],"precipitation_probability":[68,70,72,74,64,55,45,30,15,0,0,0,0,0,0,0,0,0,0,0,0,0,8,15,23,26,29,32,30,28,26,17,9,0,1,2,3,2,1,0,0,0,0,0,0,0,1,2,3,3,3,3,2,1,0,2,4,6,4,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,2,1,0,0,0,0,0,0,0,0,0,0,0,0,0,1,2,3,3,3,3,3,3,3,4,5,6,6,6,6,4,2,0,2,4,6,4,2,0,3,7,10,13,16,19,17,15,13,12,11,10,9,7,6,5,4,3,4,5,6,7,9,10],"rain":[0.00,0.20,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00],"snowfall":[0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00],"temperature_2m":[9.2,8.9,10.1,10.0,9.5,9.5,8.5,7.4,6.9,6.1,5.5,4.9,4.5,4.1,3.7,3.3,2.8,3.1,4.5,6.6,8.7,10.4,12.0,12.8,13.0,13.4,14.0,13.7,13.2,12.9,12.1,11.1,10.1,9.5,8.8,8.3,7.8,7.3,7.2,6.9,6.4,6.6,8.2,10.4,12.7,15.0,16.7,17.1,17.5,18.2,18.7,18.9,18.8,18.4,17.6,16.4,14.8,13.5,12.5,11.8,11.1,10.6,10.1,10.0,10.1,10.4,11.3,12.9,15.0,17.0,18.5,19.8,20.8,21.6,22.2,22.3,21.9,21.1,20.1,18.9,17.5,16.4,15.7,15.4,15.0,14.4,13.8,13.5,13.5,13.8,14.1,13.5,14.4,15.5,16.8,18.4,19.5,19.9,20.0,19.7,19.0,18.1,17.1,16.1,15.2,14.3,13.5,12.9,12.3,11.7,11.2,11.0,11.0,11.2,11.9,13.3,15.1,16.6,17.3,17.7,18.0,18.1,18.1,18.0,18.0,17.8,17.5,16.9,16.1,15.4,15.1,14.9,14.7,14.6,14.6,14.2,13.3,12.1,11.5,11.9,13.0,14.0,14.8,15.7,16.2],"uv_index":[2.65,2.25,2.00,2.40,1.65,0.90,0.30,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.20,0.80,1.65,2.75,4.00,5.05,5.45,4.75,3.25,2.45,2.60,1.85,1.05,0.35,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.25,0.95,1.80,2.85,4.05,4.80,4.95,5.60,2.75,1.45,1.50,1.00,0.45,0.30,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.25,0.90,1.75,2.65,3.10,4.10,4.90,4.35,3.40,3.90,2.60,2.00,1.10,0.35,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.10,0.35,0.95,1.80,2.65,3.60,4.55,5.15,5.25,5.05,4.50,3.55,2.30,1.25,0.65,0.25,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.05,0.10,0.45,1.20,2.20,3.15,4.20,5.25,5.70,5.15,4.00,2.95,2.30,1.80,1.30,0.80,0.30,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.05,0.15,0.50,1.30,2.35,3.35,4.30,5.25,5.75],"visibility":[24140.00,7120.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,22540.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00,24140.00],"wind_direction_10m":[216,204,248,239,220,233,221,249,234,218,208,208,200,180,180,177,168,171,171,173,182,191,197,201,202,207,213,208,216,221,180,143,145,145,149,156,151,148,130,117,119,122,124,135,138,146,168,184,174,172,167,160,148,124,101,103,108,113,114,118,118,118,117,114,113,113,116,120,124,128,133,138,142,143,143,142,139,133,126,123,126,129,133,137,139,139,140,140,150,160,175,323,332,339,342,342,342,345,347,347,344,341,340,347,4,24,38,45,48,45,45,45,54,65,72,75,78,77,74,69,72,94,121,135,137,131,135,166,198,207,202,195,204,238,263,272,279,287,293,297,297,295,291,286,282],"wind_gusts_10m":[22.7,29.9,27.7,28.4,27.7,25.2,28.8,19.1,17.6,13.3,12.6,13.3,13.3,14.8,14.0,15.5,15.5,15.1,17.6,22.7,25.6,27.4,30.6,33.1,33.5,32.8,32.0,32.0,31.0,21.2,16.9,7.2,8.6,9.4,9.0,8.3,6.8,6.8,5.8,5.0,6.8,6.8,9.7,15.1,15.8,17.6,22.7,36.7,38.5,36.7,34.6,32.8,28.4,23.8,19.4,20.2,20.5,21.2,20.2,18.7,17.6,17.3,17.3,16.9,19.1,21.2,23.4,27.4,31.3,35.3,33.8,32.8,31.3,31.0,31.0,30.6,28.4,26.6,24.5,21.2,18.4,15.1,14.8,14.8,14.4,14.0,13.3,13.0,12.2,11.5,10.8,20.5,20.5,20.9,21.6,22.7,23.4,23.4,23.0,23.0,22.0,20.5,19.4,17.6,15.8,14.0,12.6,10.8,9.4,11.2,13.3,15.1,15.8,16.6,17.3,18.4,19.4,20.5,21.2,21.6,22.3,23.4,24.5,25.6,19.1,13.0,6.5,9.4,12.6,15.5,13.3,11.2,9.0,14.4,19.8,25.2,24.8,24.5,24.1,28.1,31.7,35.6,37.1,38.2,39.6],"wind_speed_10m":[8.0,7.1,11.6,10.5,10.7,7.7,7.1,8.1,6.2,5.9,5.3,6.1,5.4,6.5,6.1,7.2,7.0,6.9,7.3,9.4,10.4,11.4,12.4,13.1,13.6,12.9,13.3,12.2,8.5,7.1,3.2,3.6,4.4,4.4,4.2,3.5,3.7,3.4,2.8,3.2,3.7,3.4,3.9,5.1,5.4,6.5,8.5,10.1,9.8,9.8,9.3,8.4,6.8,5.2,5.5,6.6,8.3,9.4,8.7,7.7,6.9,6.9,7.2,7.9,8.2,9.0,10.0,11.6,13.0,14.1,13.8,13.0,12.3,12.6,12.6,12.3,10.5,7.9,6.2,6.0,6.7,6.9,6.9,6.9,6.6,6.6,6.1,5.6,5.0,4.2,4.0,7.2,7.7,8.1,8.3,8.3,8.3,8.2,8.1,8.1,7.9,7.6,7.3,6.3,4.7,4.3,4.1,4.1,4.3,5.1,6.1,6.6,6.7,6.8,7.2,7.1,7.0,6.6,6.4,6.2,5.7,5.4,6.3,7.1,5.9,3.8,2.0,1.5,2.3,3.2,3.9,4.1,4.3,5.5,8.4,10.8,10.9,10.1,10.2,11.3,12.9,14.3,15.0,15.4,15.8],"weather_code":[3,80,2,3,3,3,61,3,3,3,3,3,3,3,1,0,0,1,0,0,2,3,3,3,2,3,3,3,3,3,3,2,3,2,2,2,1,3,3,3,3,2,0,1,0,0,1,3,2,0,0,0,0,0,0,1,1,1,0,0,0,3,3,3,3,3,3,3,3,3,1,1,1,2,2,2,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,2,2,2,3,3,3,3,3,3,2,2,2,3,3,3,3,3,3,3,3,3,3,3,3,80,80,80,3,3,3,2,2,2,3,3,3,3,3,3,3,3,3,3,3,3,2,2,2,2,2,2]}}
    gather_data(test_json_15min, 'minutely_15')
    print(gather_data(test_json_hour, 'hourly'))
