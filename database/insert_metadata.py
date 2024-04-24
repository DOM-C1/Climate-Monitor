"""Insert metadata into a new database."""

from os import environ as ENV

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


def get_db_connection(config):
    """Connect to the database"""
    return psycopg2.connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def get_metadata(filepath):
    """Get a list of data from local files."""
    with open(filepath, encoding='utf-8') as file:
        return [x.strip() for x in file.readlines()]


def insert_countries(conn):
    """Insert country metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO country (name) VALUES (%s)",
            [[data] for data in get_metadata('metadata/countries.txt')])
        conn.commit()


def insert_counties(conn):
    """Insert county metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO county (name, country_id) VALUES (%s, %s)",
            [[data.split(', ')[0], int(data.split(', ')[1])]
             for data in get_metadata('metadata/counties.txt')])
        conn.commit()


def insert_locations(conn):
    """Insert location metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO location (latitude, longitude, loc_name, county_id) \
                VALUES (%s, %s, %s, %s)", [[float(data.split(', ')[0]),
                                            float(data.split(', ')[1]),
                                            data.split(', ')[2],
                                            int(data.split(', ')[3])]
                                           for data in get_metadata('metadata/locations.txt')])
        conn.commit()


def insert_alert_types(conn):
    """Insert alert types metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO alert_type (name) VALUES (%s)",
            [[name] for name in get_metadata('metadata/emergencies.txt')])
        conn.commit()


def insert_severities(conn):
    """Insert alert types metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO severity_level (severity_level_id, severity_level) VALUES (%s, %s)",
            [[int(level.split(', ')[0]), level.split(', ')[1]] for level in get_metadata('metadata/severities.txt')])
        conn.commit()


def insert_weather_codes(conn):
    """Insert weather code metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO weather_code (weather_code_id, description) VALUES (%s, %s)",
            [[int(data.split(', ')[0]), data.split(', ')[1]]
             for data in get_metadata('metadata/weather_codes.txt')])
        conn.commit()


def insert_metadata(config):
    """Insert all metadata into database."""
    with get_db_connection(config) as connection:
        insert_alert_types(connection)
        insert_severities(connection)
        insert_weather_codes(connection)
        insert_countries(connection)
        insert_counties(connection)
        insert_locations(connection)


if __name__ == "__main__":
    load_dotenv()
    insert_metadata(ENV)
