"""This file fetches the jsons for various locations."""
import requests


def get_weather_details(longitude: str, latitude: str) -> dict


response = requests.get('https://api.open-meteo.com/v1/forecast?')
