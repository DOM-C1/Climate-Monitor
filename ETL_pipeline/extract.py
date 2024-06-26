"""This file fetches weather information for various locations."""
from datetime import datetime, timedelta

from grequests import get, map


def time_rounder(timestamp: datetime, get_fifteen: bool = True) -> datetime:
    """Returns the most recent 15 min time, or the most recent hour."""
    if get_fifteen:
        return (timestamp.replace(second=0, microsecond=0, minute=(timestamp.minute // 15 * 15)))
    return (timestamp.replace(second=0, microsecond=0, minute=0))


def generate_time_strings(get_today: bool = True) -> list[str]:
    """Returns the times for either today and tomorrow, or tomorrow and next week."""
    if get_today:
        today = time_rounder(datetime.now())
        time_str = today.isoformat(timespec='minutes')
        tomorrow = time_rounder(today, get_fifteen=False) + timedelta(days=1)
    else:
        today = time_rounder(datetime.now(), get_fifteen=False)
        next_week = today + timedelta(weeks=1)
        time_str = next_week.isoformat(timespec='minutes')
        tomorrow = today + timedelta(hours=25)
    tomorrow_str = tomorrow.isoformat(timespec='minutes')
    return time_str, tomorrow_str


def get_weather_details_for_week(latitude: float, longitude: float) -> dict:
    """Returns a request object for the weather details for the coming week."""
    next_week_str, tomorrow_str = generate_time_strings(get_today=False)
    return get(
        f'https://api.open-meteo.com/v1/forecast?latitude={str(latitude)}&longitude={str(longitude)}&hourly=apparent_temperature,cloud_cover,relative_humidity_2m,lightning_potential,precipitation,precipitation_probability,rain,snowfall,temperature_2m,uv_index,visibility,wind_direction_10m,wind_gusts_10m,wind_speed_10m,weather_code&start_hour={tomorrow_str}&end_hour={next_week_str}&timezone=Europe/London',
        timeout=6)


def get_weather_details_for_24hrs(latitude: float, longitude: float) -> dict:
    """Returns a request object for the weather details for the next 24 hours."""
    today_str, tomorrow_str = generate_time_strings()
    return get(
        f'https://api.open-meteo.com/v1/forecast?latitude={str(latitude)}&longitude={str(longitude)}&minutely_15=apparent_temperature,cloud_cover,relative_humidity_2m,lightning_potential,precipitation,precipitation_probability,rain,snowfall,temperature_2m,uv_index,visibility,wind_direction_10m,wind_gusts_10m,wind_speed_10m,weather_code&start_minutely_15={today_str}&end_minutely_15={tomorrow_str}&timezone=Europe/London',
        timeout=6)


def get_air_quality(latitude: float, longitude: float, config: dict) -> dict:
    """Returns a request object for the air quality given a latitude and longitude."""
    api_url = f'https://api.api-ninjas.com/v1/airquality?lat={latitude}&lon={longitude}'
    return get(api_url, headers={'X-Api-Key': config['API_KEY']}, timeout=6)


def async_api_calls(latitude: float, longitude: float, config: dict) -> dict:
    """Returns a dictionary of a JSON response for each request."""

    requests = [get_weather_details_for_week(latitude, longitude),
                get_weather_details_for_24hrs(latitude, longitude),
                get_air_quality(latitude, longitude, config)]

    responses = map(requests)

    return {"weather_for_week": responses[0].json(),
            "weather_for_24hr": responses[1].json(),
            "air_quality": responses[2].json()}
