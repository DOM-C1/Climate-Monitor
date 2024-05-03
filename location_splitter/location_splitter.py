"""This script separates the locations into chunks for mapping to AWS Lambdas."""

from os import environ as ENV

from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection


def get_db_connection(config: dict) -> connection:
    """Returns a connection to the database."""

    return connect(
        user=config["DB_USER"],
        password=config["DB_PASSWORD"],
        host=config["DB_HOST"],
        port=config["DB_PORT"],
        database=config["DB_NAME"],
        cursor_factory=RealDictCursor
    )


def query_locations(conn: connection) -> dict[float]:
    """Returns a list of dictionaries representing the latitude and
    longitude of each location in the database."""

    sql_query = """
                SELECT latitude, longitude
                FROM location;
                """

    with conn.cursor() as cur:
        cur.execute(sql_query)
        coordinates = cur.fetchall()

    return [{"latitude": c["latitude"], "longitude": c["longitude"]}
            for c in coordinates]


def chunk_locations(locations: list[dict], chunk_size: int = 100) -> list[list[dict]]:
    """Returns a list of location chunks (list of dictionaries)."""

    return [locations[i:i+chunk_size]
            for i in range(0, len(locations), chunk_size)]


def handler(event: dict = None, context: dict = None) -> dict[list[list[dict]]]:
    """AWS Lambda function handler for chunking locations, returns
    JSON list of list of dictionaries."""

    load_dotenv()
    conn = get_db_connection(ENV)
    locations = query_locations(conn)
    conn.close()

    return {"data": chunk_locations(locations)}
