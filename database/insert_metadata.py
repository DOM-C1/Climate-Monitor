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


def get_metadata(filename):
    with open('metadata/' + filename) as f:
        return [x.strip() for x in f.readlines()]


def insert_countries(conn):
    """Insert country metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO country (name) VALUES (%s)", get_metadata('countries.txt'))
        conn.commit()


def insert_counties(conn):
    """Insert county metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO county (name, country_id) VALUES (%s)", get_metadata('counties.txt'))
        conn.commit()


def insert_locations(conn):
    """Insert location metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO location (latitude, longitude, location_name, county_id) VALUES (%s)", get_metadata('locations.txt'))
        conn.commit()


def insert_emergency_types(conn):
    """Insert emergency types metadata into database"""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO emergency_type (type) VALUES (%s)", get_metadata('emergencies.txt'))
        conn.commit()


if __name__ == "__main__":
    load_dotenv()
    # with get_db_connection(ENV) as connection:
    #     insert_emergency_types(connection)
    #     insert_countries(connection)
    #     insert_counties(connection)
    #     insert_locations(connection)
