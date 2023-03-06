"""
Package for manipulating DeepZoom images.

Classes:
    BigImage -- Base class for representing tiled. zoomable images

Exceptions:
    FileFormatError -- raised if there is an error in the XML file or a
                    size mismatch
    ZoomError -- raised if an invalid zoom is requested (one that isn't
                 in the image)
"""

import math


class FileFormatError(Exception):
    """Raised when there is an error in the DZI file format"""

    def __init__(self, message="Error in file format"):
        self.message = message
        super().__init__(self.message)


class ZoomError(Exception):
    """Raised when there an invalid zoom is requested"""

    def __init__(self, message="Error in file format"):
        self.message = message
        super().__init__(self.message)


class BigImage:
    """
    A DigitalZoom image.

    This class reads and returns the metadata for the image,
    provides helper functions for working with dimensions, and
    loads and returns tiles.  It doesn't contain actual image pixels.

    Higher zoom means bigger picture.  0 is smallest picture available
    """

    BGR = 0
    RGB = 1

    def __init__(self, filename=None):
        super().__init__()

    def open(self, filename):
        """ Reads the metadata for an image"""

        raise NotImplementedError

    @property
    def max_zoom(self):
        """
        Returns the maximum zoom available for this image (biggest number)
        """
        raise NotImplementedError

    @property
    def min_zoom(self):
        """
        Returns the minimum zoom available for this image (smallest number)
        """
        raise NotImplementedError

    def num_tiles_across(self, zoom):
        """ Returns the number of tiles in the x direction"""
        tiles = int(math.ceil(self.image_width_for_zoom(zoom)/self.tile_width))
        if (tiles < 1):
            return 1
        return tiles

    def num_tiles_down(self, zoom):
        """ Returns the number of tiles in the y direction """
        tiles = int(math.ceil(self.image_height_for_zoom(zoom) /
                              self.tile_height))
        if (tiles < 1):
            return 1
        return tiles

    def x_to_tile(self, x):
        """
        Given the x cordinate in the full image, returns the tile number
        """
        tile = int(x/self.tile_width+0.0001)
        return tile

    def y_to_tile(self, y):
        """
        Given the y cordinate in the full image, returns the tile number
        """
        tile = int(y/self.tile_height+0.0001)
        return tile

    def tile_filename(self, tilex, tiley):
        """
        Given the x and y coordinates in the full image. returns
        the filename for the tile without the path.
        """
        raise NotImplementedError

    def tile_start_x(self, tile, clip=False):
        """
        Returns the x coordinate of the top-left corner of the
        given tile, including the overlap pixels
        """
        raise NotImplementedError

    def tile_start_y(self, tile, clip=False):
        """
        Returns the y coordinate of the top-left corner of the
        given tile, including the overlap pixels
        """
        raise NotImplementedError

    def tile_end_x_plus_one(self, tile, zoom):
        """
        Returns 1 pixel beyond the x coordinate of the right corner of the
        given tile, including the overlap pixels
        """
        raise NotImplementedError

    def tile_end_y_plus_one(self, tile, zoom):
        """
        Returns 1 pixel beyond the y coordinate of the bottom corner of the
        given tile, including the overlap pixels
        """
        raise NotImplementedError

    def left_overlap(self, tile):
        """ Overlap for given tile number on the left side """
        raise NotImplementedError

    def right_overlap(self, tile, zoom):
        """ Overlap for given tile number on the right side """
        raise NotImplementedError

    def top_overlap(self, tile):
        """ Overlap for given tile number on the top side """
        raise NotImplementedError

    def bottom_overlap(self, tile, zoom):
        """ Overlap for given tile number on the bottom side """
        raise NotImplementedError

    @property
    def tile_width(self):
        """ return the normal tile width (same for all tiles) """
        raise NotImplementedError

    @property
    def tile_height(self):
        """ return the normal tile height (same for all tiles) """
        raise NotImplementedError

    def tile_width_at_zoom(self, tile, zoom):
        """
        Returns the width of the given tile number at the given zoom,
        including overlap. trimmed if neccessary to the image size
        """
        return self.tile_end_x_plus_one(tile, zoom) - self.tile_start_x(tile)

    def tile_height_at_zoom(self, tile, zoom):
        """
        Returns the height of the given tile number at the given zoom,
        including overlap. trimmed if neccessary to the image size
        """
        return self.tile_end_y_plus_one(tile, zoom) - self.tile_start_y(tile)

    def image_width_for_zoom(self, zoom):
        """
        Returns the width of the image at the given zoom.

        Raises ZoomError if the zoom doesn't exist
        """
        raise NotImplementedError

    def image_height_for_zoom(self, zoom):
        """
        Returns the height of the image at the given zoom.

        Raises ZoomError if the zoom doesn't exist
        """
        raise NotImplementedError

    @property
    def zooms(self):
        """ Return an array of available zooms, biggest to smallest """
        raise NotImplementedError

    def fit_to_viewport(self, viewport_width, viewport_height):
        """
        Returns (zoom, width, height) of the biggest zoom that will
        completely fit within the given viewport size.

        If none fit, the smallest zoom is returned.  Width and height
        may be bigger than the viewport

        Positional arguments:
        viewport_width  : width of the viewport image must fit in
        viewport_height : height of the viewport image must fit in
        """

        for z in self.zooms:
            try:
                width = self.image_width_for_zoom(z)
                height = self.image_height_for_zoom(z)
                if (width <= viewport_width and height < viewport_height):
                    return (z, width, height)
            except ZoomError:
                pass  # we just skip any zooms that don't exist
        # fallback - return smallest zoom.  may be bigger than viewport
        return (z, width, height)

    def load_tile(self, tilex, tiley, zoom):
        """
        Loads the image with the given tile number and zoom.

        Positional parameters:
            tilex : number of the tile in the x direction to load
            tiley : number of the tile in the y direction to load
            zoom  : zoom factor to load

        Raises FileFormatError if format is not recognised
        """

        raise NotImplementedError

    @property
    def band_format(self):
        """ Returns BigImage.BGR or BigImage.RGB """
        raise NotImplemented
