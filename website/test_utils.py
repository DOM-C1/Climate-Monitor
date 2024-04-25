import unittest
from unittest.mock import patch

from utils import get_details_from_post_code, get_long_lat, get_location_name, get_county, get_country


class TestPostcodeUtils(unittest.TestCase):

    def setUp(self):
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
        mock_get.return_value.json.return_value = self.mock_postcode_response
        response = get_details_from_post_code('SW1A 1AA')
        self.assertEqual(response, self.mock_postcode_response)

    def test_get_long_lat(self):
        long_lat = get_long_lat(self.mock_postcode_response)
        self.assertEqual(long_lat, (-0.12574, 51.50853))

    def test_get_location_name(self):
        location_name = get_location_name(self.mock_postcode_response)
        self.assertEqual(location_name, 'Westminster')

    def test_get_county(self):
        county = get_county(self.mock_postcode_response)
        self.assertEqual(county, 'Greater London')

    def test_get_country(self):
        country = get_country(self.mock_postcode_response)
        self.assertEqual(country, 'England')


if __name__ == '__main__':
    unittest.main()
