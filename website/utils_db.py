"""This file provides useful functions needed to do database related things."""
from flask import render_template
from psycopg2 import connect
from utils import get_country, get_county, get_long_lat, get_location_name


def get_db_connection(config: dict) -> connect:
    """Connect to the database."""
    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def add_to_database(table: str, data: dict, conn: connect) -> None:
    """This function adds a row to the database."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s' for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    values = list(data.values())
    with conn.cursor() as cur:
        cur.execute(query, values)
        conn.commit()
    return None


def get_id(table: str, column: str, value: str, conn: connect) -> int:
    """Given the table name, column and a value, checks whether that value exists and return it's ID if
       if it does exist; a return value of -1 indicates that value doesn't exist."""
    query = f"SELECT * FROM {table} WHERE {column} = %s"
    with conn.cursor() as cur:
        cur.execute(query, (value,))
        result = cur.fetchall()
        if result:
            return result[0][0]
        return -1


def get_loc_id(longitude: float, latitude: float, conn: connect) -> int:
    """This function gets a location_id, assuming that a unique location is
       defined by its longitude and latitude. """
    query = """SELECT loc_id FROM location
                WHERE longitude = %s AND latitude = %s
                         """
    values = (longitude, latitude)
    with conn.cursor() as cur:
        cur.execute(query, values)
        result = cur.fetchone()
    if result:
        return result[0]
    return -1


def setup_user_location(details, name, email, sub_newsletter, sub_alerts, conn) -> str:
    """This sets up location tracking for a user, if the user exists then it just adds a new
       location, otherwise, it sets up the new user too."""
    longitude, latitude = get_long_lat(details)
    location_name = get_location_name(details)
    country = get_country(details)
    county = get_county(latitude, longitude)
    country_id = get_id('country', 'name', country, conn)
    if country_id == -1:
        return render_template('cant_be_found_page.html')

    county_id = get_id('county', 'name', county, conn)
    if county_id == -1:
        county_data = {'name': county, 'country_id': country_id}
        add_to_database('county', county_data, conn)
        county_id = get_id('county', 'name', county, conn)
    user_data = {'email': email, 'name': name}
    user_id = get_id('user_details', 'email', email, conn)
    if user_id == -1:
        add_to_database('user_details', user_data, conn)
        user_id = get_id('user_details', 'email', email, conn)
    loc_id = get_loc_id(longitude, latitude, conn)
    if loc_id == -1:
        location_data = {'loc_name': location_name,
                         'county_id': county_id, 'longitude': longitude, 'latitude': latitude}
        add_to_database('location', location_data, conn)
        loc_id = get_loc_id(longitude, latitude, conn)

    user_loc_data = {'user_id': user_id, 'loc_id': loc_id,
                     'report_opt_in': sub_newsletter, 'alert_opt_in': sub_alerts}
    add_to_database('user_location_assignment',
                    user_loc_data, conn)
    conn.close()
    return ''


def get_value_from_db(table: str, column: str, _id: str, id_name: str, conn) -> str:
    """Extract the value associated with a particular ID, 
       table and column."""
    query = f"SELECT {column} FROM {table} WHERE {id_name} = %s"
    with conn.cursor() as cur:
        cur.execute(query, (_id,))
        result = cur.fetchone()
    if result:
        return result[0]
    return ''
