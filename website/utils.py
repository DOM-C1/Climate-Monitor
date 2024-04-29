"""This file, provides the functions needed to fetch the data."""
import requests
from geopy.geocoders import Nominatim


def get_details_from_post_code(postcode: str) -> dict:
    """Retuns a dictionary containing the details we need for a given postcode. """
    response = requests.get(
        f'https://api.postcodes.io/postcodes/{postcode}', timeout=6).json()
    return response


def get_postcode_long_lat(details: dict) -> tuple:
    """Given a dictioanry, find the longitude and latitude in that order."""
    return (details['result']['longitude'], details['result']['latitude'])


def get_location(address: dict) -> str:
    """Extract the city/town/village name of a location."""
    if 'city' in address:
        return address['city']
    if 'town' in address:
        return address['town']
    if 'village' in address:
        return address['village']
    return ""


def get_county(address: dict) -> str:
    """Extract the county name of a location."""
    if 'county' in address:
        return address['county']
    if 'state_district' in address:
        return address['state_district']
    return ""


def get_country(address: dict) -> str:
    """Extract the country name of a location."""
    items = address.values()
    if 'England' in items:
        return 'England'
    if 'Alba / Scotland' in items:
        return 'Scotland'
    if 'Cymru / Wales' in items:
        return 'Wales'
    if 'Northern Ireland / Tuaisceart Éireann' in items:
        return 'Northern Ireland'
    return ""


def get_location_names(longitude: float, latitude: float) -> tuple[str]:
    """Extract the location names from a longitude and latitude."""
    geolocator = Nominatim(user_agent="my_application")
    location_obj = geolocator.reverse(
        f"{latitude}, {longitude}")
    address = location_obj.raw['address']
    country = get_country(address)
    county = get_county(address)
    location = get_location(address)
    if not location:
        location = county
    if not county:
        county = location
    return location, county, country


def get_standard_long_lat(location: str) -> tuple[float]:
    """Get the latitude and longitude from a county."""
    geolocator = Nominatim(user_agent="my_application")
    location_details = geolocator.geocode(location)
    return location_details.longitude, location_details.latitude
