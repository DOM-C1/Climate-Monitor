"""Transform a JSON of a single weather report into pandas DataFrames for use in load.py"""
from datetime import datetime, timedelta
from itertools import zip_longest
from os import environ as ENV

import pandas as pd
import psycopg2
import psycopg2.extras
import requests
from dotenv import load_dotenv
from geopy.geocoders import Nominatim


from extract import get_air_quality, get_flood_warning_json, get_weather_details_for_24hrs, get_weather_details_for_week


def rename_columns(data: pd.DataFrame):
    data = data.rename(columns={'time': 'forecast_timestamp', 'relative_humidity_2m': 'humidity',
                                'precipitation_probability': 'precipitation_prob', 'rain': 'rainfall',
                                'temperature_2m': 'temperature', 'wind_direction_10m': 'wind_direction',
                                'wind_gusts_10m': 'wind_gusts', 'wind_speed_10m': 'wind_speed',
                                'weather_code': 'weather_code_id'})
    return data


def change_data_types(data):
    data['forecast_timestamp'] = data['forecast_timestamp'].apply(
        pd.to_datetime)
    data['visibility'] = data['visibility'].apply(lambda x: int(x))
    return data


def create_warning_list(forecast):
    warning_list = []
    for i, alert in enumerate(forecast):
        if alert != 4:
            warning_list.append(
                {'alert_type_id': i + 1, 'severity_type_id': alert})
    if not warning_list:
        warning_list is None
    return warning_list


def calculate_heat_alerts(temperature: float):
    """Find extreme heat alerts amongst temperature data."""
    if 32 <= temperature:
        return 1
    if 27 <= temperature < 32:
        return 2
    if 22 <= temperature < 27:
        return 3
    return 4


def calculate_wind_alerts(wind_gust: float, wind_speed: float):
    """Find extreme wind alerts amongst wind data."""
    if 130 <= wind_gust or 80 <= wind_speed:
        return 1
    if 110 <= wind_gust < 130 or 65 <= wind_speed < 80:
        return 2
    if 90 <= wind_gust < 110 or 50 <= wind_speed < 65:
        return 3
    return 4


def calculate_ice_alerts(temperature: float):
    """Find extreme ice alerts amongst temperature and precipitation data."""
    if -10 >= temperature:
        return 1
    if -5 >= temperature > -10:
        return 2
    if -3 >= temperature > -5:
        return 3
    return 4


def calculate_lightning_alerts(lightning: pd.Series):
    """Find extreme lightning alerts amongst lightning potential data."""
    if 2500 <= lightning:
        return 1
    if 1000 <= lightning < 2500:
        return 2
    if 300 <= lightning < 1000:
        return 3
    return 4


def calculate_snowfall_alerts(snowfall: pd.Series):
    """Find extreme lightning alerts amongst lightning potential data."""
    if 2 <= snowfall:
        return 1
    if 0.5 <= snowfall < 2:
        return 2
    if 0.1 <= snowfall < 0.5:
        return 3
    return 4


def calculate_visibility_alerts(visibility: pd.Series):
    """Find low visibility alerts amongst visibility data."""
    if 20 >= visibility:
        return 1
    if 50 >= visibility > 20:
        return 2
    if 150 >= visibility > 0.5:
        return 3
    return 4


def calculate_air_quality_alert(concentration: float):
    """Find if air quality is an alert from the severity_id."""
    if 0 <= concentration < 101:
        severity_id = 4
    elif 101 <= concentration < 161:
        severity_id = 3
    elif 161 <= concentration < 241:
        severity_id = 2
    elif 241 <= concentration:
        severity_id = 1
    return severity_id


def calculate_uv_alerts(uv_index: float):
    """Find extreme uv alerts amongst uv-index data."""
    if 7.5 <= uv_index:
        return 1
    elif 5.5 <= uv_index < 7.5:
        return 2
    elif 2.5 <= uv_index < 5.5:
        return 3
    return 4


def calculate_rain_alerts(rainfall: float):
    """Find extreme rain alerts amongst rainfall data."""
    if 10 <= rainfall:
        return 1
    elif 5 <= rainfall < 10:
        return 2
    elif 3 <= rainfall < 5:
        return 3
    return 4


def get_weather_alerts(weather_data: pd.DataFrame):
    """Find alerts for weather in dataframe."""
    alerts = pd.DataFrame()
    twelve_hour_data = weather_data[weather_data['forecast_timestamp'] < datetime.now(
    ) + timedelta(hours=12)]
    alerts['heat_warning'] = twelve_hour_data['temperature'].apply(
        calculate_heat_alerts)
    alerts['wind_warning'] = twelve_hour_data[['wind_gusts', 'wind_speed']].apply(
        lambda x: calculate_wind_alerts(x['wind_gusts'], x['wind_speed']), axis=1)
    alerts['ice_warning'] = twelve_hour_data['temperature'].apply(
        calculate_ice_alerts)
    alerts['lightning_warning'] = twelve_hour_data['lightning_potential'].apply(
        calculate_lightning_alerts)
    alerts['snowfall_warning'] = twelve_hour_data['snowfall'].apply(
        calculate_snowfall_alerts)
    alerts['visibility_warning'] = twelve_hour_data['visibility'].apply(
        calculate_visibility_alerts)
    alerts['uv_warning'] = twelve_hour_data['uv_index'].apply(
        calculate_uv_alerts)
    alerts['rainfall_warning'] = twelve_hour_data['rainfall'].apply(
        calculate_rain_alerts)
    return alerts


def gather_data_from_json(json_data, key):
    data = pd.DataFrame(json_data[key])
    data = data.map(lambda x: 0 if x is None or x == 'null' else x)
    data = rename_columns(data)
    data = change_data_types(data)
    alerts = get_weather_alerts(data)
    forecasts = data.to_dict(orient="records")
    warnings = alerts.itertuples(index=False, name=None)
    forecast_warnings = (create_warning_list(forecast)
                         for forecast in warnings)
    return list({'forecast': x, 'warnings': y} for x, y in zip_longest(forecasts, forecast_warnings))


def gather_weather_data(latitude, longitude):
    minutely_data = get_weather_details_for_24hrs(latitude, longitude)
    hourly_data = get_weather_details_for_week(latitude, longitude)
    return gather_data_from_json(minutely_data, 'minutely_15') + gather_data_from_json(hourly_data, 'hourly'),


def gather_air_quality(latitude, longitude):
    concentration = get_air_quality(latitude, longitude)['O3']['concentration']
    try:
        concentration = float(concentration)
    except:
        concentration = 'error'
    if concentration < 0:
        concentration = 'error'
    severity_id = calculate_air_quality_alert(concentration)
    return {'o3_concentration': concentration, 'severity_id': severity_id}


def get_flood_warning(data: dict):
    geolocator = Nominatim(user_agent="my_application")
    warnings = []
    severity = data['severityLevel']
    time_raised = data['timeRaised']
    for location_place in data['floodArea']['county'].split(', '):
        location = geolocator.geocode(location_place)
        flood_dict = {"latitiude": location.latitude, "longitude": location.longitude,
                      "severity_id": severity, "time_raised": time_raised}
        if flood_dict not in warnings:
            warnings.append(flood_dict)
    return warnings


def get_all_floods():
    flood_warnings = []
    for flood in get_flood_warning_json()['items']:
        if datetime.strptime(flood['timeMessageChanged'], "%Y-%m-%dT%H:%M:%S") > datetime.now() - timedelta(hours=1):
            flood_warnings += get_flood_warning(flood)
    return flood_warnings


if __name__ == "__main__":
    load_dotenv()
    for x in gather_weather_data(0, 0):
        print(x)
    print(gather_air_quality(0, 0))
    print(get_all_floods())
