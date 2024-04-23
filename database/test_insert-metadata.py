from insert_metadata import get_metadata, insert_countries, insert_counties, insert_locations, insert_alert_types
import os


def test_get_location_metadata():
    files = os.listdir()
    print(files)
    if 'metadata' not in files and 'database' in files:
        filepath = 'database/metadata/locations.txt'
    elif 'metadata' in files:
        filepath = 'metadata/locations.txt'
    else:
        raise FileNotFoundError(
            "Run pytest in 'database' or in parent directory.")
    locations = get_metadata(filepath)
    assert locations is not None
    assert isinstance(locations, list)
    assert all('\n' not in x for x in locations)
    assert all(len(x.split(', ')) == 4 for x in locations)
