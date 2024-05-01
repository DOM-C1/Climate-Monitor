"""Transform a JSON of a single weather report into a list of dictionaries for use in load.py"""
from datetime import datetime, timedelta
from itertools import zip_longest

import pandas as pd


def rename_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Rename the dataframe columns to match database."""
    data = data.rename(columns={'time': 'forecast_timestamp',
                                'relative_humidity_2m': 'humidity',
                                'precipitation_probability': 'precipitation_prob',
                                'rain': 'rainfall',
                                'temperature_2m': 'temperature',
                                'wind_direction_10m': 'wind_direction',
                                'wind_gusts_10m': 'wind_gusts',
                                'wind_speed_10m': 'wind_speed',
                                'weather_code': 'weather_code_id'})
    return data


def change_data_types(data: pd.DataFrame) -> pd.DataFrame:
    """Convert incorrect datatypes to match database."""
    data['forecast_timestamp'] = data['forecast_timestamp'].apply(
        pd.to_datetime)
    data['visibility'] = data['visibility'].apply(int)
    return data


def create_warning_list(forecast: tuple) -> list[dict]:
    """Create a list of weather warnings associated with a forecast."""
    warning_list = []
    for i, alert in enumerate(forecast):
        if alert != 4:
            warning_list.append(
                {'alert_type_id': i + 1, 'severity_type_id': alert})
    if not warning_list:
        warning_list = None
    return warning_list


def calculate_heat_alerts(temperature: float) -> int:
    """Find extreme heat alerts amongst temperature data."""
    if 32 <= temperature:
        return 1
    if 27 <= temperature < 32:
        return 2
    if 22 <= temperature < 27:
        return 3
    return 4


def calculate_wind_alerts(wind_gust: float, wind_speed: float) -> int:
    """Find extreme wind alerts amongst wind data."""
    if 130 <= wind_gust or 80 <= wind_speed:
        return 1
    if 110 <= wind_gust < 130 or 65 <= wind_speed < 80:
        return 2
    if 90 <= wind_gust < 110 or 50 <= wind_speed < 65:
        return 3
    return 4


def calculate_ice_alerts(temperature: float) -> int:
    """Find extreme ice alerts amongst temperature and precipitation data."""
    if temperature <= -10:
        return 1
    if -10 <= temperature < -5:
        return 2
    if -5 <= temperature < -3:
        return 3
    return 4


def calculate_lightning_alerts(lightning: pd.Series) -> int:
    """Find extreme lightning alerts amongst lightning potential data."""
    if 2500 <= lightning:
        return 1
    if 1000 <= lightning < 2500:
        return 2
    if 300 <= lightning < 1000:
        return 3
    return 4


def calculate_snowfall_alerts(snowfall: pd.Series) -> int:
    """Find extreme lightning alerts amongst lightning potential data."""
    if 2 <= snowfall:
        return 1
    if 0.5 <= snowfall < 2:
        return 2
    if 0.1 <= snowfall < 0.5:
        return 3
    return 4


def calculate_visibility_alerts(visibility: pd.Series) -> int:
    """Find low visibility alerts amongst visibility data."""
    if visibility <= 20:
        return 1
    if 20 <= visibility < 50:
        return 2
    if 50 <= visibility < 150:
        return 3
    return 4


def calculate_air_quality_alert(concentration: float) -> int:
    """Find if air quality is an alert from the concentration of o3."""
    if 0 <= concentration < 101:
        return 4
    if 101 <= concentration < 161:
        return 3
    if 161 <= concentration < 241:
        return 2
    return 1


def calculate_uv_alerts(uv_index: float) -> int:
    """Find extreme uv alerts amongst uv-index data."""
    if 11 <= uv_index:
        return 1
    if 8 <= uv_index < 11:
        return 2
    if 6 <= uv_index < 8:
        return 3
    return 4


def calculate_rain_alerts(rainfall: float) -> int:
    """Find extreme rain alerts amongst rainfall data."""
    if 10 <= rainfall:
        return 1
    if 5 <= rainfall < 10:
        return 2
    if 3 <= rainfall < 5:
        return 3
    return 4


def get_weather_alerts(weather_data: pd.DataFrame) -> pd.DataFrame:
    """Obtain a dataframe of alerts for a forecast."""
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


def gather_data_from_json(json_data: dict, key: str) -> list[dict]:
    """Obtain transformed forecast data from hourly or 15-minutely data."""
    data = pd.DataFrame(json_data[key])
    data['lightning_potential'] = data['lightning_potential'].fillna(0)
    data = rename_columns(data)
    data = change_data_types(data)
    alerts = get_weather_alerts(data)
    forecasts = data.to_dict(orient="records")
    warnings = alerts.itertuples(index=False, name=None)
    forecast_warnings = (create_warning_list(forecast)
                         for forecast in warnings)
    return list({'forecast': x, 'warnings': y} for x, y
                in zip_longest(forecasts, forecast_warnings))


def gather_weather_data(minutely_data: dict, hourly_data: dict) -> list[dict]:
    """Obtain transformed forecast data for the whole weather report."""
    return gather_data_from_json(minutely_data, 'minutely_15') +\
        gather_data_from_json(hourly_data, 'hourly')


def gather_air_quality(air_quality_data: dict) -> dict:
    """Obtain the o3 air quality for the weather report."""
    concentration = air_quality_data['O3']['concentration']
    try:
        concentration = float(concentration)
    except ValueError:
        concentration = 'error'
    if concentration < 0:
        concentration = 'error'
    severity_id = calculate_air_quality_alert(concentration)
    return {'o3_concentration': concentration, 'severity_id': severity_id}
