
from os import environ as ENV

from dotenv import load_dotenv
from boto3 import client
import pandas as pd
from psycopg2 import connect


def get_db_connection(config: dict) -> client:
    """Returns database connection."""

    return connect(
        server=config["DB_HOST"],
        port=config["DB_PORT"],
        user=config["DB_USER"],
        database=config["DB_NAME"],
        password=config["DB_PASSWORD"],
        as_dict=True,
    )


def get_df(conn: connect) -> pd.DataFrame:
    """Returns a Dataframe of the database"""

    query = """
            SELECT *
            FROM table...

            """

    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    return pd.DataFrame(rows)


def send_email(sesclient: client, html: str) -> None:
    """Sends email using BOTO3"""

    sesclient.send_email(
        Source="trainee.dominic.chambers@sigmalabs.co.uk",
        Destination={
            "ToAddresses": [
                "trainee.dominic.chambers@sigmalabs.co.uk", ,
            ]
        },
        Message={
            "Subject": {"Data": "Here is your weekly report."},
            "Body": {"Text": {"Data": "Daily report"}, "Html": {"Data": html}},
        },
    )
    return None


def get_ses_client(config: dict) -> client:
    return client(
        "ses",
        aws_access_key_id=ENV["AWS_KEY"],
        aws_secret_access_key=ENV["AWS_SKEY"],
        region_name="eu-west-2",
    )
