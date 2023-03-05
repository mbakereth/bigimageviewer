"""
Unit test for a DeepZoom image
"""

import unittest

from src.bigimageviewer.dzimage import DZImage
from src.bigimageviewer.bigimage import FileFormatError, ZoomError
_FILENAME = "test/images/adelboden.dzi"


class TestDZImage(unittest.TestCase):
    def setUp(self):
        try:
            self.image = DZImage(_FILENAME)
        except FileFormatError as e:
            self.fail(f"Instantiate DZImage raised FileFormatError: "
                      + f"{e.message}")

    def test_zoom_levels(self):
        # check zoom range is correct
        self.assertEqual(self.image.min_zoom, 0)
        self.assertEqual(self.image.max_zoom, 13)

        # check individual zooms are correct
        widths = (1, 2, 3, 6, 11, 21, 42, 83, 165, 330, 660, 1319, 2637,
                  5274)
        heights = (1, 1, 1, 2, 4, 7, 13, 25, 50, 99, 198, 395, 790, 1579)
        for z in range(self.image.min_zoom, self.image.max_zoom+1):
            width = self.image.image_width_for_zoom(z)
            height = self.image.image_height_for_zoom(z)
            self.assertEqual(width, widths[z])
            self.assertEqual(height, heights[z])

        # check other zooms through an exception
        with self.assertRaises(ZoomError):
            self.image.image_width_for_zoom(len(widths))
        with self.assertRaises(ZoomError):
            self.image.image_height_for_zoom(len(heights))

    def test_tile_sizes(self):
        zoom = 12

        # tile sizes
        self.assertEqual(self.image.tile_width, 254)
        self.assertEqual(self.image.tile_height, 254)

        # x tile starts
        self.assertEqual(self.image.tile_start_x(0), 0)
        self.assertEqual(self.image.tile_start_x(1),
                         self.image.tile_width-1)
        self.assertEqual(self.image.tile_start_x(10),
                         10*self.image.tile_width-1)

        # x tile ends
        self.assertEqual(self.image.tile_end_x_plus_one(0, zoom),
                         self.image.tile_width+1)
        self.assertEqual(self.image.tile_end_x_plus_one(1, zoom),
                         self.image.tile_start_x(1) + self.image.tile_width +
                         2)
        self.assertEqual(self.image.tile_end_x_plus_one(10, zoom),
                         self.image.image_width_for_zoom(zoom))

        # y tile starts
        self.assertEqual(self.image.tile_start_y(0), 0)
        self.assertEqual(self.image.tile_start_y(1),
                         self.image.tile_height-1)
        self.assertEqual(self.image.tile_start_y(3),
                         3*self.image.tile_height-1)

        # y tile ends
        self.assertEqual(self.image.tile_end_y_plus_one(0, zoom),
                         self.image.tile_height+1)
        self.assertEqual(self.image.tile_end_y_plus_one(1, zoom),
                         self.image.tile_start_y(1) + self.image.tile_height +
                         2)
        self.assertEqual(self.image.tile_end_y_plus_one(3, zoom),
                         self.image.image_height_for_zoom(zoom))

    def test_overlaps(self):
        zoom = 12

        # left overlap
        self.assertEqual(self.image.left_overlap(0), 0)
        self.assertEqual(self.image.left_overlap(1), 1)
        self.assertEqual(self.image.left_overlap(10), 1)

        # right overlap
        self.assertEqual(self.image.right_overlap(0, zoom), 1)
        self.assertEqual(self.image.right_overlap(1, zoom), 1)
        self.assertEqual(self.image.right_overlap(10, zoom), 0)

        # top overlap
        self.assertEqual(self.image.top_overlap(0), 0)
        self.assertEqual(self.image.top_overlap(1), 1)
        self.assertEqual(self.image.top_overlap(3), 1)

        # bottom overlap
        self.assertEqual(self.image.bottom_overlap(0, zoom), 1)
        self.assertEqual(self.image.bottom_overlap(1, zoom), 1)
        self.assertEqual(self.image.bottom_overlap(3, zoom), 0)

    def test_tile_load(self):
        zoom = 12

        # test we don't get exceptions about unexpected dimensions
        # and that the expected dimensions match (which should be checked
        # in the code anyway)
        tiles = ((0, 0), (0, 1), (0, 3),
                 (1, 1),
                 (9, 1),
                 (10, 0), (10, 1), (10, 3),
                 )
        for tile in tiles:
            tilex, tiley = tile
            expected_width = self.image.tile_width_at_zoom(tilex, zoom)
            expected_height = self.image.tile_height_at_zoom(tiley, zoom)
        img = self.image.load_tile(tilex, tiley, zoom)
        height, width, channel = img.shape
        self.assertEqual(height, expected_height)
        self.assertEqual(width, expected_width)
