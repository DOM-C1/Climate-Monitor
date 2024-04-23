"""This file, provides the functions needed to upload to the database and clean data."""
import pandas as pd
from psycopg2 import connect


def get_db_connection(config: dict) -> connect:
    """Returns database connection."""

    return connect(
        server=config["host"],
        port=config["port"],
        user=config["user"],
        database=config["climate-monitoring-database"],
        password=config["password"],
        as_dict=True
    )


def get_df():
    """This reads from a local file and transforms it into a Pandas dataframe."""
    return pd.read_csv('postcodes.csv')

def get_long_lat(postcode:str) -> tuple:
    """Given a postal, find the longitude and latitude in that order."""
    df = get_df()
    location = df[df['postcode'] == postcode][['longitude','latitude']]
    return location['longitude'].iloc[0],location['latitude'].iloc[0]


def get_location_name(postcode:str) -> str:
    """Given the postcode, find the associated location name."""
    df = get_df()
    return df[df['postcode'] == postcode]['town'].iloc[0]

def get_county(postcode:str):
    """Given the postcode, find the associated region name."""
    df = get_df()
    return df[df['postcode'] == postcode]['region'].iloc[0]

def add_to_databse(table: str,data:tuple, conn:connect):
    """This will be used to add to the database."""
    raise NotImplementedError('When the database is setup, we should be able to upload.')
