"""This file, provides the functions needed to fetch the data."""
import requests


def get_details_from_post_code(postcode: str) -> dict:
    """Retuns a dictionary containing the details we need for a given postcode. """
    response = requests.get(
        f'https://api.postcodes.io/postcodes/{postcode}', timeout=6).json()
    return response


def get_long_lat(details: dict) -> tuple:
    """Given a dictioanry, find the longitude and latitude in that order."""
    return (details['result']['longitude'], details['result']['latitude'])


def get_location_name(details: dict) -> str:
    """Given the location details extract the location name"""
    return details['result']['nuts']


def get_county(details: dict) -> str:
    """Given the location details extract the county."""
    return details['result']['admin_county']


def get_country(details: dict) -> str:
    """Given the location details extract the country."""
    return details['result']['country']
