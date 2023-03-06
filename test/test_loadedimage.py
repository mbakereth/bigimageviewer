"""
Unit test for LoadImage class
"""

import unittest

from src.bigimageviewer.loadedimage import LoadedImage
from src.bigimageviewer.dzimage import DZImage
from src.bigimageviewer.bigimage import FileFormatError, ZoomError

import numpy as np

_FILENAME = "test/images/bw.dzi"
_VP_TILES_ACROSS = 10
_VP_TILES_DOWN = 10


class TestDZImage(unittest.TestCase):
    def _zero_tiles(self):
        self.tiles = np.zeros((_VP_TILES_DOWN, _VP_TILES_ACROSS, 1), np.uint8)

    def _create_image(self, zoom=1):
        try:
            self.image = DZImage(_FILENAME)
            self.loaded_image = LoadedImage(self.image, 2)
            self.loaded_image.viewport_on_fullimage = \
                4*self.image.tile_width, 4*self.image.tile_height
            self.loaded_image.viewport_size = \
                (2*self.image.tile_width, 2*self.image.tile_height)
            self.loaded_image.zoom = zoom
            self.loaded_image.load_image()
        except FileFormatError as e:
            self.fail(f"Instantiate image raised FileFormatError: "
                      + f"{e.message}")
        except ZoomError as e:
            self.fail(f"Instantiate image raised ZoomError: "
                      + f"{e.message}")


    def _assert_tiles_match(self):
        for i in range(0, _VP_TILES_DOWN):
            for j in range(0, _VP_TILES_ACROSS):
                xstart = self.image.tile_width * j
                xend = xstart + self.image.tile_width
                ystart = self.image.tile_height * i
                yend = ystart + self.image.tile_height
                #print(j, i, np.sum(self.loaded_image._pixels[ystart:yend, xstart:xend]))
                self.assertTrue(np.all(
                    self.loaded_image._pixels[ystart:yend, xstart:xend] == \
                    self.tiles[j, i]), 
                    f"Tile x={j} y={i} not all {self.tiles[j, i]}")

    def test_01_load(self):
        self._create_image()
        self._zero_tiles()
        self.tiles[2:4,2:4] = 1
        self._assert_tiles_match()

    def test_02_scroll(self):
        # scroll left 1 tile
        self._create_image()
        self.loaded_image.scroll(-self.image.tile_width, 0)
        self._zero_tiles()
        self.tiles[1:3, 2:4] = 1
        self._assert_tiles_match()

        # scroll right 1 tile
        self._create_image()
        self.loaded_image.scroll(self.image.tile_width, 0)
        self._zero_tiles()
        self.tiles[3:5, 2:4] = 1
        self._assert_tiles_match()
        
        # scroll up 1 tile
        self._create_image()
        self.loaded_image.scroll(0, -self.image.tile_height, )
        self._zero_tiles()
        self.tiles[2:4, 1:3] = 1
        self._assert_tiles_match()

        # scroll down 1 tile
        self._create_image()
        self.loaded_image.scroll(0, self.image.tile_height)
        self._zero_tiles()
        self.tiles[2:4, 3:5] = 1
        self._assert_tiles_match()

    def test_03_zoom(self):
        self._create_image()
        self.loaded_image.scroll(-self.image.tile_width, 0)

        # zoom in
        self._zero_tiles()
        centerx = int(self.loaded_image.viewport_size[0] / 2)
        centery = int(self.loaded_image.viewport_size[1] / 2)
        self.loaded_image.zoom_to(0, centerx, centery)
        self.tiles[2:3, 3:4] = 1
        self._assert_tiles_match()

        # zoom out
        self._zero_tiles()
        centerx = int(self.loaded_image.viewport_size[0] / 2)
        centery = int(self.loaded_image.viewport_size[1] / 2)
        self.loaded_image.zoom_to(1, centerx, centery)
        self.tiles[1:3, 2:4] = 1
        self._assert_tiles_match()
