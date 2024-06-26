"""This file provides useful functions needed to do database related things."""
from psycopg2 import connect
from psycopg2.extensions import connection
from utils import get_standard_long_lat, get_postcode_long_lat, get_location_names
import pandas as pd

ERROR_CODE = -1


def get_db_connection(config: dict) -> connection:
    """Connect to the database."""
    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"]
    )


def add_to_database(table: str, data: dict, conn: connection) -> None:
    """This function adds a row to the database."""
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s' for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    values = list(data.values())
    with conn.cursor() as cur:
        cur.execute(query, values)
    conn.commit()
    return None


def get_id(table: str, column: str, value: str, conn: connection) -> int:
    """Given the table name, column and a value, checks whether that
    value exists and return it's ID if it does exist; a return value of -1
    indicates that value doesn't exist."""
    query = f"SELECT * FROM {table} WHERE {column} = %s"
    with conn.cursor() as cur:
        cur.execute(query, (value,))
        result = cur.fetchall()
        return result[0][0] if result else ERROR_CODE


def get_loc_id(latitude: float, longitude: float, conn: connection) -> int:
    """This function gets a location_id, assuming that a unique location is
       defined by its longitude and latitude. """

    query = """SELECT loc_id FROM location
                WHERE latitude = %s AND longitude = %s"""
    values = (latitude, longitude,)
    with conn.cursor() as cur:
        cur.execute(query, values)
        result = cur.fetchone()
    return result[0] if result else ERROR_CODE


def setup_user_location(details, name, email, sub_newsletter, sub_alerts, password, conn) -> None:
    """This sets up location tracking for a user, if the user exists then it just adds a new
       location, otherwise, it sets up the new user too."""
    longitude, latitude = get_postcode_long_lat(details)
    location_name, county, country = get_location_names(longitude, latitude)
    longitude, latitude = get_standard_long_lat(location_name)
    country_id = get_id('country', 'name', country, conn)
    county_id = get_id('county', 'name', county, conn)

    if county_id == ERROR_CODE:
        county_data = {'name': county, 'country_id': country_id}
        add_to_database('county', county_data, conn)
        county_id = get_id('county', 'name', county, conn)
    user_id = get_id('user_details', 'email', email, conn)

    if user_id == ERROR_CODE:
        user_data = {'email': email, 'name': name, 'password': password}
        add_to_database('user_details', user_data, conn)
        user_id = get_id('user_details', 'email', email, conn)
    loc_id = get_loc_id(latitude, longitude, conn)

    if loc_id == ERROR_CODE:
        location_data = {'loc_name': location_name,
                         'county_id': county_id, 'longitude': longitude, 'latitude': latitude}
        add_to_database('location', location_data, conn)
        loc_id = get_loc_id(latitude, longitude, conn)

    user_loc_data = {'user_id': user_id, 'loc_id': loc_id,
                     'report_opt_in': sub_newsletter, 'alert_opt_in': sub_alerts}
    add_to_database('user_location_assignment',
                    user_loc_data, conn)

    conn.close()
    return None


def get_value_from_db(table: str, column: str, _id: str, id_name: str, conn) -> str:
    """Extract the value associated with a particular ID,
       table and column."""
    query = f"SELECT {column} FROM {table} WHERE {id_name} = %s"
    with conn.cursor() as cur:
        cur.execute(query, (_id,))
        result = cur.fetchone()
    return result[0] if result else ''


def check_row_exists(conn: connection, table_name: str, column1: str, value1: str, column2: str, value2: str) -> bool:
    """Check if a row exists in the database that satisfies the conditions for two columns."""
    query = f"""
    SELECT EXISTS (
        SELECT 1 FROM {table_name}
        WHERE {column1} = %s AND {column2} = %s
    );
    """
    with conn.cursor() as cur:

        cur.execute(query, (value1, value2))
        exists = cur.fetchone()[0]
    return bool(exists)


def query_to_df(conn: connection, query: str) -> pd.DataFrame:
    """Executes a SQL query and returns the results as a pandas DataFrame."""
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

    return pd.DataFrame(rows, columns=columns)


def get_locations_for_user(conn: connection, email: str) -> pd.DataFrame:
    """This gets the locations associated with a particular user."""
    user_details_query = """
        SELECT *
        FROM user_details AS UD
        JOIN user_location_assignment ON UD.user_id = user_location_assignment.user_id
        JOIN location ON user_location_assignment.loc_id = location.loc_id;
    """
    user_details = query_to_df(conn, user_details_query)
    user_details = user_details.loc[:,
                                    ~user_details.columns.duplicated()]
    return user_details[user_details['email'] == email]


def update_loc_assignment(conn: connection, _id_name: str, _id: int, column: str, value: str) -> None:
    """If a user wants to update alerts and report settings for a particular location
       it is done through this function."""
    query = f"""
    UPDATE user_location_assignment
    SET {column} = %s
    WHERE {_id_name} = %s;
    """
    values = (value, _id)
    with conn.cursor() as cur:
        cur.execute(query, values)
    conn.commit()
    return None


def delete_user(conn: connection, _id: int) -> None:
    """Deletes a users records."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM user_location_assignment WHERE user_id = %s;", (_id,))
        cur.execute("DELETE FROM user_details WHERE user_id = %s;", (_id,))
        conn.commit()
        return None
