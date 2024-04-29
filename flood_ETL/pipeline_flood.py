"""This script is the full ETL pipeline for a single location."""

from os import environ as ENV

from dotenv import load_dotenv

from transform_flood import get_all_floods
from load_flood import insert_all_floods


def flood_pipeline() -> None:
    """Loads data from flood API to a database."""
    load_dotenv()
    floods = get_all_floods()
    insert_all_floods(ENV, floods)


def handler(event: None, context: dict = None) -> None:
    """AWS Lambda function handler of the pipeline."""
    flood_pipeline()
