"""
Class for manipulating DeepZoom images.

Classes:
    DZImage -- Rpresents a DeepZoom image
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
from .bigimage import BigImage, FileFormatError, ZoomError


class DZImage(BigImage):
    """
    A DigitalZoom image.

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
        if (not self.filename.lower().endswith(".dzi")):
            filename = filename + ".dzi"
        path = pathlib.Path(filename)
        self._basename = path.stem
        self._full_path = path.parent
        self._files_directory = self._basename+'_files'
        self._files_full_path = os.path.join(self._full_path,
                                             self._files_directory)

        # read XML file
        with open(filename, 'r') as f:
            data = f.read()

        soup = BeautifulSoup(data, "xml")
        if (soup.Image is None):
            raise FileFormatError("No Image tag found in file")
        if ("Width" in soup.Image.attrs):
            self._width = soup.Image['Width']
        if ("Height" in soup.Image.attrs):
            self._height = soup.Image['Height']
        if ("TileSize" in soup.Image.attrs):
            self._tile_width = soup.Image['TileSize']
            self._tile_height = self._tile_width
        else:
            raise FileFormatError("Image tag contains no tile size")
        if ("Overlap" in soup.Image.attrs):
            self._overlap = soup.Image['Overlap']
        else:
            self._overlap = 0
        if ("Format" in soup.Image.attrs):
            self._format = soup.Image['Format']
        else:
            raise FileFormatError("Image tag contains no format")

        if (soup.Size is not None):
            if ("Width" in soup.Size.attrs):
                self._width = soup.Size['Width']
            if ("Height" in soup.Size.attrs):
                self._height = soup.Size['Height']

        if (self._width is None):
            raise FileFormatError("Image tag contains no width")
        if (self._height is None):
            raise FileFormatError("Image tag contains no height")

        try:
            self._width = int(self._width)
        except ValueError:
            raise FileFormatError("Width is not an integer")
        try:
            self._height = int(self._height)
        except ValueError:
            raise FileFormatError("height is not an integer")
        try:
            self._overlap = int(self._overlap)
        except ValueError:
            raise FileFormatError("overlap is not an integer")
        try:
            self._tile_width = int(self._tile_width)
            self._tile_height = self._tile_width
        except ValueError:
            raise FileFormatError("tile size is not an integer")

        # calculate zooms
        self._zoom_to_width = {}
        self._zoom_to_height = {}

        max_num = 0
        min_num = None
        dirs = []
        for d in os.listdir(self._files_full_path):
            if re.search('^[0-9]+$', d):
                dir_num = int(d)
                if (dir_num > max_num):
                    max_num = dir_num
                if (min_num is None or dir_num < min_num):
                    min_num = dir_num
                dirs.append(dir_num)
        zoomed_width = self._width
        zoomed_height = self._height
        dirs.sort(reverse=True)
        for d in dirs:
            self._zoom_to_width[d] = zoomed_width
            self._zoom_to_height[d] = zoomed_height
            zoomed_width = int(math.ceil(zoomed_width / 2))
            zoomed_height = int(math.ceil(zoomed_height / 2))

        self._zooms = list(range(max_num, -1, -1))
        self._max_zoom = max_num
        self._min_zoom = min_num

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

    def _tile_filename(self, tilex, tiley):
        """
        Given the x and y coordinates in the full image. returns
        the filename for the tile without the path.
        """
        return f"{tilex}_{tiley}.{self._format}"

    def _tile_fullpath(self, x, y, zoom):
        return os.path.join(self._files_full_path, str(zoom),
                            self._tile_filename(x, y))

    def tile_start_x(self, tile, clip=False):
        """
        Returns the x coordinate of the top-left corner of the
        given tile, including the overlap pixels
        """
        coord = tile*self._tile_width
        if (clip and coord - self._overlap < 0):
            return 0
        if (tile == 0):
            overlap = 0
        else:
            overlap = self._overlap
        return coord - overlap

    def tile_start_y(self, tile, clip=False):
        """
        Returns the y coordinate of the top-left corner of the
        given tile, including the overlap pixels
        """
        coord = tile*self._tile_height
        if (clip and coord - self._overlap < 0):
            return 0
        if (tile == 0):
            overlap = 0
        else:
            overlap = self._overlap
        return coord - overlap

    def tile_end_x_plus_one(self, tile, zoom):
        """
        Returns 1 pixel beyond the x coordinate of the right corner of the
        given tile, including the overlap pixels
        """
        tile_start = self.tile_start_x(tile)
        tile_end_plus_one = tile_start + self._tile_width \
            + self.left_overlap(tile) + self.right_overlap(tile, zoom)
        if (tile_end_plus_one > self._zoom_to_width[zoom]):
            tile_end_plus_one = self._zoom_to_width[zoom]
        return tile_end_plus_one

    def tile_end_y_plus_one(self, tile, zoom):
        """
        Returns 1 pixel beyond the y coordinate of the bottom corner of the
        given tile, including the overlap pixels
        """
        tile_start = self.tile_start_y(tile)
        tile_end_plus_one = tile_start + self._tile_height \
            + self.top_overlap(tile) + self.bottom_overlap(tile, zoom)
        if (tile_end_plus_one > self._zoom_to_height[zoom]):
            tile_end_plus_one = self._zoom_to_height[zoom]
        return tile_end_plus_one

    def left_overlap(self, tile):
        """ Overlap for given tile number on the left side """
        if (tile == 0):
            return 0
        return self._overlap

    def right_overlap(self, tile, zoom):
        """ Overlap for given tile number on the right side """
        last_tile = self.num_tiles_across(zoom)-1
        if (tile == last_tile):
            return 0
        return self._overlap

    def top_overlap(self, tile):
        """ Overlap for given tile number on the top side """
        if (tile == 0):
            return 0
        return self._overlap

    def bottom_overlap(self, tile, zoom):
        """ Overlap for given tile number on the bottom side """
        last_tile = self.num_tiles_down(zoom)-1
        if (tile == last_tile):
            return 0
        return self._overlap

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

        filename = self._tile_fullpath(tilex, tiley, zoom)
        img = cv2.imread(filename)
        height, width, channel = img.shape
        if (width != expected_width or height != expected_height):
            raise FileFormatError(f"Tile {tilex},{tiley} image size " +
                                  f"{width}x{height} does not match " +
                                  f"expected size " +
                                  f"{expected_width}x{expected_height}"
                                  )

        return img

    @property
    def band_format(self):
        """ Returns BigImage.BGR or BigImage.RGB """
        return BigImage.RGB
