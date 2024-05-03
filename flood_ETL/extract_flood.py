"""This file fetches flood information."""
import requests


def get_flood_warning_json() -> dict:
    """Returns information for the whole of the UK regarding floods."""
    response = requests.get(
        'http://environment.data.gov.uk/flood-monitoring/id/floods', timeout=10)
    return response.json()
