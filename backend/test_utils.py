"""Test the functions in the utils module."""

import unittest
from unittest.mock import patch

from utils import get_details_from_post_code, get_postcode_long_lat, get_location_names


class TestPostcodeUtils(unittest.TestCase):
    """
    Unit tests for postcode utility functions that fetch various details based on a given postcode.
    """

    def setUp(self):
        """
        Set up a mock response for the postcode API that includes geographic and 
        administrative information.
        """
        self.mock_postcode_response = {
            'result': {
                'longitude': -0.12574,
                'latitude': 51.50853,
                'nuts': 'Westminster',
                'admin_county': 'Greater London',
                'country': 'England'
            }
        }

    @patch('requests.get')
    def test_get_details_from_post_code(self, mock_get):
        """
        Test fetching detailed information from a postcode API to ensure it correctly 
        captures and returns data.
        """
        mock_get.return_value.json.return_value = self.mock_postcode_response
        response = get_details_from_post_code('SW1A 1AA')
        self.assertEqual(response, self.mock_postcode_response)

    def test_get_long_lat(self):
        """
        Test extraction of longitude and latitude from the postcode API response.
        """
        long_lat = get_postcode_long_lat(self.mock_postcode_response)
        self.assertEqual(long_lat, (-0.12574, 51.50853))

    def test_get_location_name(self):
        """
        Test extraction of the location name from the postcode API response.
        """
        long, lat = get_postcode_long_lat(self.mock_postcode_response)
        location_name = get_location_names(long, lat)[0]
        self.assertEqual(location_name, 'London')

    def test_get_county(self):
        """
        Test extraction of the county from the postcode API response.
        """
        long, lat = get_postcode_long_lat(self.mock_postcode_response)
        county = get_location_names(long, lat)[1]
        self.assertEqual(county, 'Greater London')

    def test_get_country(self):
        """
        Test extraction of the country from the postcode API response.
        """
        long, lat = get_postcode_long_lat(self.mock_postcode_response)
        country = get_location_names(long, lat)[2]
        self.assertEqual(country, 'England')


if __name__ == '__main__':
    unittest.main()
