"""This file, provides the functions needed to fetch the data."""
from geopy.geocoders import Nominatim
import requests


def get_details_from_post_code(postcode: str) -> dict:
    """Retuns a dictionary containing the details we need for a given postcode. """
    response = requests.get(
        f'https://api.postcodes.io/postcodes/{postcode}', timeout=6).json()
    return response


def get_long_lat(details: dict) -> tuple:
    """Given a dictioanry, find the longitude and latitude in that order."""
    return (details['result']['longitude'], details['result']['latitude'])


def get_county(latitude: float, longitude: float) -> tuple[str]:
    """Extract the location names from a latitude and longitude."""
    geolocator = Nominatim(user_agent="my_application")
    location_obj = geolocator.reverse(
        f"{latitude}, {longitude}")
    address = location_obj.raw['address']
    return address['county'] if 'county' in address else address.get('state_district', '')


def get_location_name(details: dict) -> str:
    """Given the location details extract the location name"""
    return details['result']['nuts']


def get_country(details: dict) -> str:
    """Given the location details extract the country."""
    return details['result']['country']
