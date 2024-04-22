from os import environ as ENV

import pandas as pd
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


if __name__ == "__main__":
    load_dotenv()
    with get_db_connection(ENV) as conn:
        pass
