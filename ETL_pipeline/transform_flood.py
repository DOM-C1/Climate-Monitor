"""Transform flood data and load it straight into the database"""

from datetime import datetime, timedelta

import pandas as pd
from geopy.geocoders import Nominatim

from extract import get_flood_warning_json


def get_lat_lon(county):
    geolocator = Nominatim(user_agent="my_application")
    location = geolocator.geocode(county)
    return location.latitude, location.longitude


def convert_dtypes(data):
    data['time_raised'] = data['time_raised'].apply(pd.to_datetime)
    data['severity_level_id'] = data['severity_level_id'].apply(pd.to_numeric)
    return data


def clean_data(data):
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


def get_location_columns(data):
    data['floodArea'] = data['floodArea'].apply(get_lat_lon)
    data['latitude'] = data['floodArea'].apply(lambda x: x[0])
    data['longitude'] = data['floodArea'].apply(lambda x: x[1])
    return data


def get_all_floods():
    flood_warnings = pd.DataFrame(get_flood_warning_json()['items'])
    flood_warnings = clean_data(flood_warnings)
    flood_warnings = convert_dtypes(flood_warnings)
    flood_warnings = get_location_columns(flood_warnings)
    flood_warnings = flood_warnings[[
        'latitude', 'longitude', 'severity_level_id', 'time_raised']].drop_duplicates(ignore_index=True)
    flood_warnings = flood_warnings.reset_index(drop=True)
    return flood_warnings.to_dict(orient="records")


if __name__ == "__main__":
    print(get_all_floods())
