"""This file fetches the jsons for various locations."""
import requests


def get_weather_details_for_today(latitude: str, longitude: str) -> dict:
    """This function extract the weather details for today, the results are given
       hourly and it is updated per hour."""
    response = requests.get(
        f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}1&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,wind_speed_10m,wind_direction_10m,wind_gusts_10m&forecast_days=1l',
        timeout=3)
    return response.json()


def get_weather_details_for_week(latitude: str, longitude: str) -> dict:
    """This function extracts the weather details for the week, the API is updated daily."""
    response = requests.get(
        f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
        timeout=3)
    return response.json()


def get_flood_warning_json() -> dict:
    """Returns information for the whole of the UK regarding floods."""
    response = requests.get(
        'http://environment.data.gov.uk/flood-monitoring/id/floods', timeout=3)
    return response.json()


get
