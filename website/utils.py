"""This file, provides the functions needed to upload to the database and clean data."""
import pandas as pd


def get_gb_df():
    return pd.read_csv('gb.csv')
def is_postal(postal:str,df:pd.DataFrame) -> bool:
    """Returns True if the postcode is a valid one, and False otherwise"""
    return not df[df['postcode'] == postal].empty


def is_email(email:str) -> bool:
    return '@' in email


def get_df():
    return pd.read_csv('postcodes.csv')

def get_long_lat(postcode:str) -> tuple:
    """Given a postal, find the longitude and latitude in that order."""
    location = df[df['postcode'] == postcode][['longitude','latitude']]
    return location['longitude'].iloc[0],location['latitude'].iloc[0]
def get_location_name(postcode:str) -> str:
    return df[df['postcode'] == postcode]['region'].iloc[0]


df = get_df()
