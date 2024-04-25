"""Load flood warnings into the database"""

from os import environ as ENV

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

from transform_flood import get_all_floods


def get_db_connection(config):
    """Connect to the database."""
    return psycopg2.connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def get_location(address: dict) -> str | None:
    """Extract the city/town/village name of a location."""
    if 'city' in address:
        return address['city']
    if 'town' in address:
        return address['town']
    if 'village' in address:
        return address['village']
    return None


def get_county(address: dict) -> str | None:
    """Extract the county name of a location."""
    if 'county' in address:
        return address['county']
    if 'state_district' in address:
        return address['state_district']
    return None


def get_country(address: dict) -> str | None:
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
    return None


def get_location_names(latitude: float, longitude: float) -> tuple[str]:
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


def insert_location(conn: connection, latitude: float, longitude: float) -> int | None:
    """Insert a location into the database, and it's associated county 
    and country where they don't already exist."""
    location, county, country = get_location_names(latitude, longitude)
    if country:
        with conn.cursor() as cur:
            cur.execute(f"""SELECT country_id FROM country
                            WHERE name = '{country}'""")
            country_id = cur.fetchone()[0]
            cur.execute(f"""SELECT county_id FROM county
                            WHERE name = '{county}'
                            AND country_id = {country_id}""")
            county_id = cur.fetchone()
            if not county_id:
                cur.execute(f"""INSERT INTO county (name, country_id)
                                VALUES ('{county}', {country_id})
                                RETURNING county_id""")
                conn.commit()
                county_id = cur.fetchone()
            county_id = county_id[0]
            cur.execute(f"""INSERT INTO location (latitude, longitude, loc_name, county_id)
                            VALUES ({latitude}, {longitude}, '{location}', {county_id})
                            RETURNING loc_id""")
            conn.commit()
            loc_id = cur.fetchone()
        return loc_id
    return None


def get_location_id(conn: connection, latitude: float, longitude: float) -> int | None:
    """Obtain the location id from the database."""
    with conn.cursor() as cur:
        cur.execute(f"""SELECT loc_id FROM location
                    WHERE latitude = {latitude}
                    AND longitude = {longitude}""")
        loc_id = cur.fetchone()
    if not loc_id:
        loc_id = insert_location(conn, latitude, longitude)
    if loc_id:
        return loc_id[0]
    return None


def insert_flood(conn: connection, flood: dict) -> None:
    """Insert a flood into the database."""
    loc_id = get_location_id(conn, flood['latitude'], flood['longitude'])
    if loc_id:
        severity_level_id = flood['severity_level_id']
        time_raised = flood['time_raised']
        with conn.cursor() as cur:
            cur.execute(f"""SELECT * FROM flood_warnings
                        WHERE severity_level_id = {severity_level_id}
                        AND time_raised = '{time_raised}'
                        AND loc_id = {loc_id}""")
            flood = cur.fetchone()
            if not flood:
                cur.execute(f"""INSERT INTO flood_warnings
                            (severity_level_id, time_raised, loc_id, notified)
                            VALUES ({severity_level_id}, '{time_raised}', {loc_id}, False)""")
                conn.commit()


def insert_all_floods(config, floods: list[dict]) -> None:
    """Insert all floods in the data into the database."""
    with get_db_connection(config) as conn:
        for flood in floods:
            insert_flood(conn, flood)
