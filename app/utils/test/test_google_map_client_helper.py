import unittest
from app.utils.google_map_client_helper import GoogleMapsRouteHelper
from app.utils import app_utils as util


class TestGoogleMapHelper(unittest.TestCase):

    def setUp(self):
        self.config = util.load_yaml_config(util.absolute_path_from_project_root("config.yaml"))
        self.gmaps = GoogleMapsRouteHelper(self.config["gmap-api-key"])
        self.directions = self.gmaps.get_routes("1146 homer street, Vancouver, BC", "650 W 41st Ave, Vancouver, BC")

    def test_get_response(self):
        self.assertGreaterEqual(len(self.directions), 1)

    def test_response_has_unicode_polyline_representation(self):
        self.assertIn('overview_polyline', self.directions[0])
        self.assertIn('points', self.directions[0]['overview_polyline'])
        self.assertTrue(isinstance(self.directions[0]['overview_polyline']['points'], unicode))

    def test_ployline_converted_to_coords(self):
        self.assertIn('overview_points', self.directions[0])
        self.assertTrue(isinstance(self.directions[0]['overview_points'], list))
        self.assertTrue(isinstance(self.directions[0]['overview_points'][0], tuple))