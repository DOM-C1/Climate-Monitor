"""Transform flood data and load it straight into the database."""

from datetime import datetime, timedelta

import pandas as pd
from geopy.geocoders import Nominatim

from extract_flood import get_flood_warning_json


def get_lat_lon(county: str) -> tuple[float]:
    """Get the latitude and longitude from a county."""
    geolocator = Nominatim(user_agent="my_application", timeout=10)
    location = geolocator.geocode(county)
    return round(location.latitude, 7), round(location.longitude, 7)


def convert_dtypes(data: pd.DataFrame) -> pd.DataFrame:
    """Convert the datatypes of 'time_raised' and 'severity_level_id' columns."""
    data['time_raised'] = data['time_raised'].apply(pd.to_datetime)
    data['severity_level_id'] = data['severity_level_id'].apply(pd.to_numeric)
    return data


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """Restrict the data to just the past hour,
    Extract the county name from given location info,
    Separate cells with a list of counties into separate rows,
    Rename the columns."""
    data['timeMessageChanged'] = data['timeMessageChanged'].apply(
        pd.to_datetime)
    data = data[data['timeMessageChanged'] >
                datetime.now() - timedelta(hours=1)]
    data.loc[:, 'floodArea'] = data.loc[:, 'floodArea'].apply(
        lambda x: x['county'].split(', '))
    data = data.explode('floodArea')
    data = data.rename(
        columns={'severityLevel': 'severity_level_id', 'timeRaised': 'time_raised'})
    return data


def get_location_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Create 'latitude' and 'longitude' columns."""
    data['floodArea'] = data['floodArea'].apply(get_lat_lon)
    data['latitude'] = data['floodArea'].apply(lambda x: x[0])
    data['longitude'] = data['floodArea'].apply(lambda x: x[1])
    return data


def get_all_floods() -> list[dict]:
    """Obtains a information about latest floods in the UK."""
    flood_warnings = pd.DataFrame(get_flood_warning_json()['items'])
    flood_warnings = clean_data(flood_warnings)
    flood_warnings = convert_dtypes(flood_warnings)
    flood_warnings = get_location_columns(flood_warnings)
    flood_warnings = flood_warnings[['latitude', 'longitude',
                                     'severity_level_id',
                                     'time_raised']].drop_duplicates(ignore_index=True)
    flood_warnings = flood_warnings.reset_index(drop=True)
    return flood_warnings.to_dict(orient="records")
