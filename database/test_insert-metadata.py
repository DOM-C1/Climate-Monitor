from insert_metadata import get_metadata, insert_countries, insert_counties, insert_locations, insert_emergency_types


def test_get_metadata():
    locations = get_metadata('locations.txt')
    assert locations is not None
    assert isinstance(locations, list)
    assert all('\n' not in x for x in locations)
    assert all(len(x.split(', ')) == 4 for x in locations)
