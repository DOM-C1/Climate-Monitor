"""This file tests the utility functions located in utils.py"""
import unittest
from unittest.mock import patch
import pandas as pd


from utils import get_df, get_long_lat, get_location_name, get_county

class TestDatabaseTools(unittest.TestCase):
    """Test suite for database utility functions."""

    def setUp(self):
        """Prepare resources for tests, mocking CSV reading."""
        self.example_data = pd.DataFrame({
            'postcode': ['AB10', 'AB11'],
            'longitude': [2.12, 2.11],
            'latitude': [57.13, 57.12],
            'town': ['Town1', 'Town2'],
            'region': ['Region1', 'Region2']
        })
        self.patcher = patch('pandas.read_csv', return_value=self.example_data)
        self.mock_csv = self.patcher.start()

    def tearDown(self):
        """Clean up after tests by stopping the patcher."""
        self.patcher.stop()

    def test_get_df(self):
        """Test if get_df correctly reads data into a DataFrame."""
        df = get_df()
        pd.testing.assert_frame_equal(df, self.example_data)

    def test_get_long_lat(self):
        """Test fetching longitude and latitude by postcode."""
        longitude, latitude = get_long_lat('AB10')
        self.assertEqual(longitude, 2.12)
        self.assertEqual(latitude, 57.13)

    def test_get_location_name(self):
        """Test fetching location name by postcode."""
        location_name = get_location_name('AB10')
        self.assertEqual(location_name, 'Town1')

    def test_get_county(self):
        """Test fetching county by postcode."""
        county = get_county('AB10')
        self.assertEqual(county, 'Region1')


if __name__ == '__main__':
    unittest.main()
