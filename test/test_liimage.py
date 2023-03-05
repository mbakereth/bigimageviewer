"""
Unit tests for a TIFF image loaded using the large_image package.
"""

import unittest

from src.bigimageviewer.liimage import LIImage
from src.bigimageviewer.bigimage import FileFormatError, ZoomError

_FILENAME = "test/images/adelboden.tif"


class TestDZImage(unittest.TestCase):
    def setUp(self):
        try:
            self.image = LIImage(_FILENAME)
        except FileFormatError as e:
            self.fail(f"Instantiate DZImage raised FileFormatError: "
                      + f"{e.message}")

    def test_zoom_levels(self):
        # check zoom range is correct
        self.assertEqual(self.image.min_zoom, 0)
        self.assertEqual(self.image.max_zoom, 6)

        # check individual zooms are correct
        widths = (82, 164, 329, 659, 1318, 2637, 5274)
        heights = (24, 49, 98, 197, 394, 789, 1579)
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

    def test_metadata(self):
        self.assertEqual(self.image.tile_width, 128)
        self.assertEqual(self.image.tile_height, 128)

    def test_tile_counts(self):
        zoom = 4
        self.assertEqual(self.image.num_tiles_across(zoom), 11)
        self.assertEqual(self.image.num_tiles_down(zoom), 4)

    def test_tile_sizes(self):
        zoom = 4

        # tile sizes
        self.assertEqual(self.image.tile_width, 128)
        self.assertEqual(self.image.tile_height, 128)

        # x tile starts
        self.assertEqual(self.image.tile_start_x(0), 0)
        self.assertEqual(self.image.tile_start_x(1),
                         self.image.tile_width)
        self.assertEqual(self.image.tile_start_x(10),
                         10*self.image.tile_width)

        # x tile ends
        self.assertEqual(self.image.tile_end_x_plus_one(0, zoom),
                         self.image.tile_width)
        self.assertEqual(self.image.tile_end_x_plus_one(1, zoom),
                         self.image.tile_start_x(1) + self.image.tile_width)
        self.assertEqual(self.image.tile_end_x_plus_one(10, zoom),
                         self.image.image_width_for_zoom(zoom))

        # y tile starts
        self.assertEqual(self.image.tile_start_y(0), 0)
        self.assertEqual(self.image.tile_start_y(1),
                         self.image.tile_height)
        self.assertEqual(self.image.tile_start_y(3),
                         3*self.image.tile_height)

        # y tile ends
        self.assertEqual(self.image.tile_end_y_plus_one(0, zoom),
                         self.image.tile_height)
        self.assertEqual(self.image.tile_end_y_plus_one(1, zoom),
                         self.image.tile_start_y(1) + self.image.tile_height)
        self.assertEqual(self.image.tile_end_y_plus_one(3, zoom),
                         self.image.image_height_for_zoom(zoom))

    def test_overlaps(self):
        zoom = 4

        # left overlap
        self.assertEqual(self.image.left_overlap(0), 0)
        self.assertEqual(self.image.left_overlap(10), 0)

        # right overlap
        self.assertEqual(self.image.right_overlap(0, zoom), 0)
        self.assertEqual(self.image.right_overlap(10, zoom), 0)

        # top overlap
        self.assertEqual(self.image.top_overlap(0), 0)
        self.assertEqual(self.image.top_overlap(3), 0)

        # bottom overlap
        self.assertEqual(self.image.bottom_overlap(0, zoom), 0)
        self.assertEqual(self.image.bottom_overlap(3, zoom), 0)

    def test_tile_load(self):
        zoom = 4

        # test we don't get exceptions about unexpected dimensions
        # and that the expected dimensions match (which should be checked
        # in the code anyway)
        tiles = ((0, 0), (0, 1), (0, 3),
                 (1, 1),
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
