"""
Class for manipulating tiled pyramid images using the large_image package

Classes:
    LIImage -- Rpresents a DeepZoom image
"""

import math
import os
import os.path
import pathlib
import re
import logging
from bs4 import BeautifulSoup
import cv2
from PySide6.QtGui import QImage, QPixmap
import large_image
from .bigimage import BigImage, FileFormatError, ZoomError


class LIImage(BigImage):
    """
    Class for manipulating tiled pyramid images using the large_image package.

    This class reads and returns the metadata for the image,
    provides helper functions for working with dimensions, and
    loads and returns tiles.  It doesn't contain actual image pixels.

    Higher zoom means bigger picture.  0 is smallest picture available
    """

    def __init__(self, filename=None):
        super().__init__()
        if (filename is not None):
            self.open(filename)

    def open(self, filename):
        """ Reads the metadata for an image"""

        # create directory and filenames
        self.filename = filename
        path = pathlib.Path(filename)
        self._basename = path.stem
        self._full_path = path.parent
        self._files_directory = self._basename+'_files'
        self._files_full_path = os.path.join(self._full_path,
                                             self._files_directory)

        self._source = large_image.open(filename)

        meta = self._source.getMetadata()
        self._min_zoom = 0
        self._max_zoom = 0
        self._width = None
        self._height = None
        self._tile_width = None
        self._tile_height = None
        if ('levels' in meta):
            self._max_zoom = meta['levels'] - 1
        if ('tileWidth' in meta):
            self._tile_width = meta['tileWidth']
        if ('tileHeight' in meta):
            self._tile_height = meta['tileHeight']
        if (self._tile_width is None):
            raise FileFormatError("Tile width missing from image")
        if (self._tile_height is None):
            raise FileFormatError("Tile height missing from image")
        if ('sizeX' in meta):
            self._width = meta['sizeX']
        if ('sizeY' in meta):
            self._height = meta['sizeY']
        if (self._width is None):
            raise FileFormatError("Width missing from image")
        if (self._height is None):
            raise FileFormatError("Height missing from image")

        # calculate zooms
        self._zoom_to_width = {}
        self._zoom_to_height = {}

        for z in range(self._min_zoom, self._max_zoom+1):
            level = self._max_zoom - z
            zoomed_width = self._width >> level
            zoomed_height = self._height >> level
            self._zoom_to_width[z] = zoomed_width
            self._zoom_to_height[z] = zoomed_height

        self._zooms = list(range(self._max_zoom, -1, -1))

    @property
    def max_zoom(self):
        """
        Returns the maximum zoom available for this image (biggest number)
        """
        return self._max_zoom

    @property
    def min_zoom(self):
        """
        Returns the minimum zoom available for this image (smallest number)
        """
        return self._min_zoom

    def tile_start_x(self, tile, clip=False):
        """
        Returns the x coordinate of the top-left corner of the
        given tile, including the overlap pixels
        """
        coord = tile*self._tile_width
        if (clip and coord < 0):
            return 0
        return coord

    def tile_start_y(self, tile, clip=False):
        """
        Returns the y coordinate of the top-left corner of the
        given tile, including the overlap pixels
        """
        coord = tile*self._tile_height
        if (clip and coord < 0):
            return 0
        return coord

    def tile_end_x_plus_one(self, tile, zoom):
        """
        Returns 1 pixel beyond the x coordinate of the right corner of the
        given tile, including the overlap pixels
        """
        tile_start = self.tile_start_x(tile)
        tile_end_plus_one = tile_start + self.tile_width
        if (tile_end_plus_one > self._zoom_to_width[zoom]):
            tile_end_plus_one = self._zoom_to_width[zoom]
        return tile_end_plus_one

    def tile_end_y_plus_one(self, tile, zoom):
        """
        Returns 1 pixel beyond the y coordinate of the bottom corner of the
        given tile, including the overlap pixels
        """
        tile_start = self.tile_start_y(tile)
        tile_end_plus_one = tile_start + self._tile_height
        if (tile_end_plus_one > self._zoom_to_height[zoom]):
            tile_end_plus_one = self._zoom_to_height[zoom]
        return tile_end_plus_one

    def left_overlap(self, tile):
        """ Overlap for given tile number on the left side """
        return 0

    def right_overlap(self, tile, zoom):
        """ Overlap for given tile number on the right side """
        return 0

    def top_overlap(self, tile):
        """ Overlap for given tile number on the top side """
        return 0

    def bottom_overlap(self, tile, zoom):
        """ Overlap for given tile number on the bottom side """
        return 0

    @property
    def tile_width(self):
        """ return the normal tile width (same for all tiles) """
        return self._tile_width

    @property
    def tile_height(self):
        """ return the normal tile height (same for all tiles) """
        return self._tile_height

    def image_width_for_zoom(self, zoom):
        """
        Returns the width of the image at the given zoom.

        Raises ZoomError if the zoom doesn't exist
        """
        if zoom in self._zoom_to_width:
            return self._zoom_to_width[zoom]
        raise ZoomError(f"Invalid zoom {zoom} requested")

    def image_height_for_zoom(self, zoom):
        """
        Returns the height of the image at the given zoom.

        Raises ZoomError if the zoom doesn't exist
        """
        if zoom in self._zoom_to_height:
            return self._zoom_to_height[zoom]
        raise ZoomError(f"Invalid zoom {zoom} requested")

    @property
    def zooms(self):
        """ Return an array of available zooms, biggest to smallest """
        return self._zooms

    def load_tile(self, tilex, tiley, zoom):
        """
        Loads the image with the given tile number and zoom.

        Positional parameters:
            tilex : number of the tile in the x direction to load
            tiley : number of the tile in the y direction to load
            zoom  : zoom factor to load

        Raises FileFormatError if format is not recognised
        """

        expected_width = self.tile_width_at_zoom(tilex, zoom)
        expected_height = self.tile_height_at_zoom(tiley, zoom)

        img = self._source.getTile(tilex, tiley, zoom,
                                   numpyAllowed=True)

        height, width, channel = img.shape
        if (width == self.tile_width and expected_width < self.tile_width or
                height == self.tile_height and
                expected_height < self.tile_height):
            return img[0:expected_height, 0:expected_width]
        return img

    @property
    def band_format(self):
        """ Returns BigImage.BGR or BigImage.RGB """
        return BigImage.BGR
