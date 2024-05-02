"""This file provides useful functions needed to do database related things."""
from flask import render_template
from psycopg2 import connect
from psycopg2.extensions import connection
from utils import get_standard_long_lat, get_postcode_long_lat, get_location_names
import pandas as pd

ERROR_CODE = -1


def get_db_connection(config: dict) -> connect:
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


def get_id(table: str, column: str, value: str, conn: connection) -> int:
    """Given the table name, column and a value, checks whether that
    value exists and return it's ID if it does exist; a return value of -1
    indicates that value doesn't exist."""
    query = f"SELECT * FROM {table} WHERE {column} = %s"
    with conn.cursor() as cur:
        cur.execute(query, (value,))
        result = cur.fetchall()
        return result[0][0] if result else ERROR_CODE


def get_loc_id(longitude: float, latitude: float, conn: connection) -> int:
    """This function gets a location_id, assuming that a unique location is
       defined by its longitude and latitude. """
    query = """SELECT loc_id FROM location
                WHERE longitude = %s AND latitude = %s
                         """
    values = (longitude, latitude)
    with conn.cursor() as cur:
        cur.execute(query, values)
        result = cur.fetchone()
    return result[0] if result else ERROR_CODE


def setup_user_location(details, name, email, sub_newsletter, sub_alerts, password, conn) -> str:
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

    user_data = {'email': email, 'name': name, 'password': password}
    user_id = get_id('user_details', 'email', email, conn)
    if user_id == ERROR_CODE:
        add_to_database('user_details', user_data, conn)
        user_id = get_id('user_details', 'email', email, conn)

    loc_id = get_loc_id(longitude, latitude, conn)
    if loc_id == ERROR_CODE:
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
    return result[0] if result else ''


def check_row_exists(conn, table_name, column1, value1, column2, value2) -> bool:
    """
    Check if a row exists in the database that satisfies the conditions for two columns."""
    query = f"""
    SELECT EXISTS (
        SELECT 1 FROM {table_name}
        WHERE {column1} = %s AND {column2} = %s
    );
    """

    with conn.cursor() as cur:

        cur.execute(query, (value1, value2))
        exists = cur.fetchone()[0]
    return True if exists else False


def execute_query(conn: connection, query: str) -> pd.DataFrame:
    """Executes a SQL query and returns the results as a pandas DataFrame."""
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]

    return pd.DataFrame(rows, columns=columns)


def prepare_data_frame(conn: connection, email: str) -> pd.DataFrame:
    """Prepares a complete data frame combining user details with weather forecasts."""
    user_details_query = """
        SELECT *
        FROM user_details AS UD
        JOIN user_location_assignment ON UD.user_id = user_location_assignment.user_id
        JOIN location ON user_location_assignment.loc_id = location.loc_id
        JOIN weather_report ON location.loc_id = weather_report.loc_id
    """
    forecast_query = """
        SELECT *
        FROM forecast AS F
        JOIN weather_code WC ON F.weather_code_id = WC.weather_code_id
        JOIN weather_report WR ON F.weather_report_id = WR.weather_report_id
    """
    user_details = execute_query(conn, user_details_query)
    forecast_details = execute_query(conn, forecast_query)
    forecast_details = forecast_details.loc[:,
                                            ~forecast_details.columns.duplicated()]

    combined_df = pd.merge(user_details, forecast_details,
                           on='weather_report_id', suffixes=('_user', '_forecast'))
    combined_df = combined_df.loc[:,
                                  ~combined_df.columns.duplicated()]
    return combined_df[combined_df['email'] == email]
