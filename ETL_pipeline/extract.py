"""This file fetches weather information for various locations."""
from datetime import datetime, timedelta
from os import environ as ENV

from dotenv import load_dotenv
import requests


def get_weather_details_for_week(latitude: float, longitude: float) -> dict:
    """This function extracts the weather details for the coming week."""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(weeks=1)
    tomorrow_str = tomorrow.isoformat(timespec='minutes')
    next_week_str = next_week.isoformat(timespec='minutes')
    response = requests.get(
        f'https://api.open-meteo.com/v1/forecast?latitude={str(latitude)}&longitude={str(longitude)}&hourly=apparent_temperature,cloud_cover,relative_humidity_2m,lightning_potential,precipitation,precipitation_probability,rain,snowfall,temperature_2m,uv_index,visibility,wind_direction_10m,wind_gusts_10m,wind_speed_10m,weather_code&start_hour={tomorrow_str}&end_hour={next_week_str}',
        timeout=6)
    return response.json()


def get_weather_details_for_24hrs(latitude: float, longitude: float) -> dict:
    """This function extracts the weather details for the next 24hours."""
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    today_str = today.isoformat(timespec='minutes')
    tomorrow_str = tomorrow.isoformat(timespec='minutes')
    response = requests.get(
        f'https://api.open-meteo.com/v1/forecast?latitude={str(latitude)}&longitude={str(longitude)}&minutely_15=apparent_temperature,cloud_cover,relative_humidity_2m,lightning_potential,precipitation,precipitation_probability,rain,snowfall,temperature_2m,uv_index,visibility,wind_direction_10m,wind_gusts_10m,wind_speed_10m,weather_code&start_minutely_15={today_str}&end_minutely_15={tomorrow_str}',
        timeout=6)
    return response.json()


def get_flood_warning_json() -> dict:
    """Returns information for the whole of the UK regarding floods."""
    response = requests.get(
        'http://environment.data.gov.uk/flood-monitoring/id/floods', timeout=6)
    return response.json()


def get_air_quality(latitude: float, longitude: float) -> dict:
    """This function gets the air quality given a latitude and longitude."""
    load_dotenv()
    api_url = f'https://api.api-ninjas.com/v1/airquality?lat={latitude}&lon={longitude}'
    response = requests.get(
        api_url, headers={'X-Api-Key': ENV['API_KEY']}, timeout=6)
    return response.json()
