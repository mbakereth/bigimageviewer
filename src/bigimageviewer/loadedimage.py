"""
Module for manipulating and displaying subimages loaded from a DZImage

Classes:
    LoadedImage - Stores a portion of a DZImage as a numpy array

Exceptions:
    NotImplementedException -- Raised when an image shape is not supported

"""

import numpy as np

from PySide6.QtCore import QRect
from PySide6.QtGui import QImage, qRgb

from .dzimage import *

_GRAY_COLOR_TABLE = [qRgb(i, i, i) for i in range(256)]


class NotImplementedException(Exception):
    """Raised when there is an the image shape is not supported"""

    def __init__(self, message="Error image shape"):
        self.message = message
        super().__init__(self.message)


class LoadedImage:
    """
    Stores pixels of partial images loaded from a DeepZoom (DZI) image.

    The pixels that are loaded include some tiles on each side that are
    intended to be outside the displayed area.  This means that when the user
    scrolls a small amount, image tiles are loaded outside the displayed area,
    not inside
    """

    def __init__(self, image, extra_tiles=2):
        """
        Constructor

        Position arguments:
            image       : the DZImage that will supply the data
            extra_tiles : number of extra tiles on each side of viewport to
                        keep loaded
        """
        super().__init__()

        # The outside box is the subimage loaded into self._pixels.
        # The inside box is the viewport displaying the image
        #
        # canvas_x,canvas_y
        # +-----------------------------------------------+
        # |                                               |
        # |                                               |
        # |   viewport_x,viewport_y                       |
        # |   +---------------------+                     |
        # |   |                     |                     |
        # |   |                     |                     |
        # |   |                     |                     |
        # |   |                     |                     |
        # |   |                     |                     |
        # |   +---------------------+                     |
        # |                    viewport_x+viewport_width, |
        # |                    viewport_y+viewport_height |
        # +-----------------------------------------------+
        #                                          canvas_x+canvas_width,
        #                                          canvas_y+canvas_height
        #
        # Also:
        #   tile_xstart, tile_ystart = top-left tile loaded
        #   tile_xend, tile_yend     = bottom-right tile loaded (exclusive)
        #   viewport_x_on_fullimage, viewport_y_on_fullimage = viewport_{xy}
        #   on the full image, not subimage

        self._image = image
        self._viewport_x = None
        self._viewport_y = None
        self._viewport_width = 0
        self._viewport_height = 0
        self._extra_tiles = extra_tiles
        self._zoom = None
        self._zoomed_image_width = None
        self._zoomed_image_height = None
        self._canvas_x = 0
        self._canvas_y = 0
        self._canvas_width = None
        self._canvas_height = None
        self._tile_xstart = None
        self._tile_ystart = None
        self._tile_xend = None
        self._tile_yend = None
        self._viewport_x_on_fullimage = 0
        self._viewport_y_on_fullimage = 0

        self._pixels = None

    @property
    def viewport_on_fullimage(self):
        """ y coord of top-left corner of viewport within full image """
        return (self._viewport_x_on_fullimage, self._viewport_y_on_fullimage)

    @viewport_on_fullimage.setter
    def viewport_on_fullimage(self, value):
        """ y coord of top-left corner of viewport within full image """
        self._viewport_x_on_fullimage = value[0]
        self._viewport_y_on_fullimage = value[1]

    @property
    def viewport_size(self):
        """ Returns the viewport size as a tuple (width, height)"""
        return (self._viewport_width, self._viewport_height)

    @viewport_size.setter
    def viewport_size(self, value):
        """
        Sets the size of the viewport image will be displayed in and reloads
        the image This doesn't redraw the image.  Call load_image() for that.

        Positional arguments:
            value -- array or tuple with width in the first value and height
                     in the second
        """
        self._viewport_width = value[0]
        self._viewport_height = value[1]

    @property
    def zoom(self):
        """ Returns the current zoom level.
            The zoom is image-implementation dependent but big number means
            zoomed in.  0 is the smallest avaulable zoom.
        """
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        """
        Sets the size of the viewport image will be displayed in.
        This doesn't redraw the image.  Call load_image() for that.

        Positional arguments:
            value -- The image zoom with 0 the most zoomed out scale,
                     1 double the size size etc. -1 is fit to viewport.
                     The range of zooms is dependent on the image
                     implementation
        """
        if (value != -1):
            if (value < self._image.min_zoom):
                value = self._image.min_zoom
            if (value > self._image.max_zoom):
                value = self._image.max_zoom
        self._zoom = value

    @property
    def min_available_zoom(self):
        """
        Returns the minimum (most zoomed out) zoom available in the image
        """
        return self._image.min_zoom

    @property
    def max_available_zoom(self):
        """
        Returns the maximum (most zoomed in) zoom available in the image
        """
        return self._image.max_zoom

    def load_image(self, centerx=None, centery=None):
        """
        Load image from scratch, preserving the top-left corner pixel of the
        full image and zoom

        If zoom not set already, defaults to full screen

        Keyword arguments:
            centerx -- if this and centery are not None, image will be centered
                       at this coordinate in the full name
            centery -- see centerx
        """
        if (self._viewport_width == 0 or self._viewport_height == 0):
            return

        # If zoom is not set to fit to window, get the size of the
        # image at the requested zoom
        if (self._zoom != -1):
            self._zoomed_image_width = self._image.image_width_for_zoom(self._zoom)
            self._zoomed_image_height = self._image.image_height_for_zoom(self._zoom)

        # If we have requested the image to be centered at a given pixel,
        # determine the top left corner of the image on the viewport from it,
        # then adjust so that the viewport is not out of range.
        if (centerx is not None and centery is not None):
            self._viewport_x_on_fullimage \
                = centerx - int(self._viewport_width/2)
            self._viewport_y_on_fullimage \
                = centery - int(self._viewport_height/2)
        if (self._zoomed_image_width is not None and
            self._viewport_x_on_fullimage + self._viewport_width >=
                self._zoomed_image_width):
            self._viewport_x_on_fullimage \
                = self._zoomed_image_width - self._viewport_width
        if (self._zoomed_image_height is not None and
            self._viewport_y_on_fullimage + self._viewport_height >=
                self._zoomed_image_height):
            self._viewport_y_on_fullimage \
                = self._zoomed_image_height - self._viewport_height
        if (self._viewport_x_on_fullimage < 0):
            self._viewport_x_on_fullimage = 0
        if (self._viewport_y_on_fullimage < 0):
            self._viewport_y_on_fullimage = 0

        # if zoom set to fit to window, set the canvas size to the get width
        # and height of zoomed image.
        if (self._zoom == -1):  # fit to viewport
            (self._zoom, self._zoomed_image_width, self._zoomed_image_height) \
                = self._image.fit_to_viewport(
                    self._viewport_width, self._viewport_height
                )
            self._canvas_width = self._zoomed_image_width
            self._canvas_height = self._zoomed_image_height

        # get how many tiles are in the canvas (this may be more than the
        # actual image)
        tiles_across_in_canvas \
            = int(math.ceil(self._viewport_width/self._image.tile_width))
        tiles_down_in_canvas \
            = int(math.ceil(self._viewport_height/self._image.tile_height))

        # add extra tiles each side, whether or not this goes beyond the image
        tiles_across_in_canvas += self._extra_tiles*2
        tiles_down_in_canvas += self._extra_tiles*2

        self._tiles_across_in_canvas = tiles_across_in_canvas
        self._tiles_down_in_canvas = tiles_down_in_canvas

        # determine how many tiles there are in the whole image at this zoom
        # level
        tiles_across = self._image.num_tiles_across(self._zoom)
        tiles_down = self._image.num_tiles_down(self._zoom)

        # get starting tile based on position in full image minus extra files.
        # this may be beyond image boundary
        self._tile_xstart = \
            self._image.x_to_tile(self._viewport_x_on_fullimage) - \
            self._extra_tiles
        self._tile_ystart = \
            self._image.y_to_tile(self._viewport_y_on_fullimage) - \
            self._extra_tiles

        # get end tile based on start tile and number of tiles in canvas
        # (including extra files)
        self._tile_xend = self._tile_xstart + tiles_across_in_canvas
        self._tile_yend = self._tile_ystart + tiles_down_in_canvas

        # get size of canvas
        self._canvas_width = tiles_across_in_canvas*self._image.tile_width
        self._canvas_height = tiles_down_in_canvas*self._image.tile_height

        self._canvas_x = self._image.tile_start_x(self._tile_xstart)
        self._canvas_y = self._image.tile_start_y(self._tile_ystart)

        # load tiles
        self._load_tiles(init_matrix=True)

        # get start of viewport on canvas from start of viewport on full image
        self._viewport_x = self._viewport_x_on_fullimage \
            - self._image.tile_start_x(self._tile_xstart)
        self._viewport_y = self._viewport_y_on_fullimage \
            - self._image.tile_start_y(self._tile_ystart)
        
    def to_qimage(self):
        """
        Return the loaded image as a QImage, along with the QRect that is
        in the viewport The image returned includes the tiles outside the
        viewport.  The QRect is the rectangle within the QImage that
        should be drawn in the window.

        Returns:
            (QImage, QRect) : as described abovex
        """
        if self._pixels is None:
            return (QImage(), QRect(0, 0, 0, 0))

        width = min(self._viewport_width, self._canvas_width)
        height = min(self._viewport_height, self._canvas_height)
        x0 = self._viewport_x
        y0 = self._viewport_y
        qrect = QRect(x0, y0, width, height)
        if self._pixels.dtype == np.uint8:
            x0 = self._viewport_x
            if len(self._pixels.shape) == 2:
                qim = QImage(self._pixels.data, self._pixels.shape[1],
                             self._pixels.shape[0], self._pixels.strides[0],
                             QImage.Format_Indexed8)
                qim.setColorTable(LoadedImage._GRAY_COLOR_TABLE)
                return (qim, qrect)

            elif len(self._pixels.shape) == 3:
                if self._pixels.shape[2] == 3:
                    qformat = QImage.Format_BGR888
                    if (self._image.band_format == BigImage.BGR):
                        qformat = QImage.Format_RGB888
                    qim = QImage(self._pixels.data, self._pixels.shape[1],
                                 self._pixels.shape[0],
                                 self._pixels.strides[0], qformat)
                    return (qim, qrect)

                elif self._pixels.shape[2] == 4:
                    qformat = QImage.Format_BGR32
                    if (self._image.band_format == BigImage.BGR):
                        qformat = QImage.Format_ARGB32
                    qim = QImage(self._pixels.data, self._pixels.shape[1],
                                 self._pixels.shape[0],
                                 self._pixels.strides[0],
                                 qformat)
                    return (qim, qrect)

        raise NotImplementedException

    def scroll(self, dx, dy):
        """ Call this when dragging an image

            Positional arguments:
                fromx -- x coord in the viewport we are dragging from
                fromy -- y coord in the viewport we are dragging from
                tox   -- x coord in the viewport we are dragging to
                toy   -- y coord in the viewport we are dragging to

            Returns:
                True if image needs to be reloaded (ie tiles have been added),
                False otherwise
        """
        new_viewport_x_on_full_image \
            = self._viewport_x_on_fullimage - dx
        new_viewport_y_on_full_image \
            = self._viewport_y_on_fullimage - dy

        return self.scroll_to(new_viewport_x_on_full_image,
                              new_viewport_y_on_full_image)

    def scroll_to(self, top_left_x, top_left_y):
        """ Scroll to the given points on the full image at current scale.
            Load new tiles if needed and update the viewport.

            Positional parameters:
                top_left_x -- x coord of top-left corner on full image at
                              current scale
                top_left_y -- y coord of top-left corner on full image at
                              current scale

            Returns:
                True if image needs to be reloaded (ie tiles have been added),
                False otherwise
        """
        need_redraw = False

        if (top_left_x + self._viewport_width >= self._zoomed_image_width):
            top_left_x = self._zoomed_image_width - self._viewport_width
        if (top_left_y + self._viewport_height >= self._zoomed_image_height):
            top_left_y = self._zoomed_image_height - self._viewport_height
        if (top_left_x < 0):
            top_left_x = 0
        if (top_left_y < 0):
            top_left_y = 0

        xdiff = self._viewport_x_on_fullimage - top_left_x
        ydiff = self._viewport_y_on_fullimage - top_left_y

        if (xdiff == 0 and ydiff == 0):
            return False

        old_viewport_x = self._viewport_x
        old_viewport_y = self._viewport_y
        old_viewport_x_on_fullimage = self._viewport_x_on_fullimage
        old_viewport_y_on_fullimage = self._viewport_y_on_fullimage

        self._viewport_x -= xdiff
        self._viewport_y -= ydiff
        self._viewport_x_on_fullimage = top_left_x
        self._viewport_y_on_fullimage = top_left_y

        # clip viewport on full image - clip viewport on canvas later
        clip_left = 0
        clip_right = 0
        clip_top = 0
        clip_bottom = 0
        if (self._viewport_x_on_fullimage + self._viewport_width >
                self._zoomed_image_width):
            clip_right = self._viewport_x_on_fullimage + \
                self._viewport_width - self._zoomed_image_width
            self._viewport_x_on_fullimage = self._zoomed_image_width - \
                self._viewport_width
        if (self._viewport_y_on_fullimage + self._viewport_height >
                self._zoomed_image_height):
            clip_bottom = self._viewport_y_on_fullimage + \
                self._viewport_height - self._zoomed_image_height
            self._viewport_y_on_fullimage = self._zoomed_image_height - \
                self._viewport_height
        if (self._viewport_x_on_fullimage < 0):
            clip_left = -self._viewport_x_on_fullimage
            self._viewport_x_on_fullimage = 0
            clip_right = 0
        if (self._viewport_y_on_fullimage < 0):
            clip_top = -self._viewport_y_on_fullimage
            self._viewport_y_on_fullimage = 0
            clip_bottom = 0

        new_tile_xstart \
            = self._image.x_to_tile(self._viewport_x_on_fullimage) - \
            self._extra_tiles
        new_tile_ystart \
            = self._image.y_to_tile(self._viewport_y_on_fullimage) - \
            self._extra_tiles
        new_tile_xend = new_tile_xstart + self._tiles_across_in_canvas
        new_tile_yend = new_tile_ystart + self._tiles_down_in_canvas

        # check if new tiles have to be loaded
        if (new_tile_xstart != self._tile_xstart or
                new_tile_ystart != self._tile_ystart or
                new_tile_xend != self._tile_xend or
                new_tile_yend != self._tile_yend):
            need_redraw = True

            old_tile_xstart = self._tile_xstart
            old_tile_ystart = self._tile_ystart
            old_tile_xend = self._tile_xend
            old_tile_yend = self._tile_yend

            extra_tiles_left = 0
            extra_tiles_right = 0
            extra_tiles_top = 0
            extra_tiles_bottom = 0
            if (new_tile_xstart > old_tile_xstart):
                extra_tiles_right = new_tile_xstart - old_tile_xstart
            if (new_tile_ystart > old_tile_ystart):
                extra_tiles_bottom = new_tile_ystart - old_tile_ystart
            if (new_tile_xend < old_tile_xend):
                extra_tiles_left = old_tile_xend - new_tile_xend
            if (new_tile_yend < old_tile_yend):
                extra_tiles_top = old_tile_yend - new_tile_yend

            # move pixels in numpy array
            copy_width = self._canvas_width - \
                self._image.tile_width*(extra_tiles_left + extra_tiles_right)
            copy_height = self._canvas_height - \
                self._image.tile_height*(extra_tiles_top + extra_tiles_bottom)
            old_pixel_xstart = 0
            old_pixel_ystart = 0
            new_pixel_xstart = 0
            new_pixel_ystart = 0
            if (extra_tiles_bottom > 0):  # move up
                old_pixel_ystart = self._image.tile_height*extra_tiles_bottom
                self._viewport_y -= self._image.tile_height*extra_tiles_bottom
            if (extra_tiles_top > 0):  # move down
                new_pixel_ystart = self._image.tile_height*extra_tiles_top
                self._viewport_y += self._image.tile_height*extra_tiles_top
            if (extra_tiles_right > 0):  # move left
                old_pixel_xstart = self._image.tile_width*extra_tiles_right
                self._viewport_x -= self._image.tile_width*extra_tiles_right
            if (extra_tiles_left > 0):  # move down
                new_pixel_xstart = self._image.tile_width*extra_tiles_left
                self._viewport_x += self._image.tile_width*extra_tiles_left
            self._pixels[new_pixel_ystart:new_pixel_ystart+copy_height,
                         new_pixel_xstart:new_pixel_xstart+copy_width] \
                = self._pixels[old_pixel_ystart:old_pixel_ystart+copy_height,
                               old_pixel_xstart:old_pixel_xstart+copy_width]

            # load new tiles
            tiles_across = self._image.num_tiles_across(self._zoom)
            tiles_down = self._image.num_tiles_down(self._zoom)
            self._tile_xstart = new_tile_xstart
            self._tile_xend = new_tile_xend
            self._tile_ystart = new_tile_ystart
            self._tile_yend = new_tile_yend
            self._load_tiles(init_matrix=False, skip_loaded=True,
                             old_tile_xstart=old_tile_xstart,
                             old_tile_ystart=old_tile_ystart,
                             old_tile_xend=old_tile_xend,
                             old_tile_yend=old_tile_yend)

            if (clip_left > 0):
                self._viewport_x += clip_left
            elif (clip_right > 0):
                self._viewport_x -= clip_right
            if (clip_top > 0):
                self._viewport_y += clip_top
            elif (clip_bottom > 0):
                self._viewport_y -= clip_bottom

        return need_redraw

    def get_rect(self):
        """
        Returns the rectangle on the pixel array that should be drawn
        in the viewport
        """
        width = min(self._viewport_width, self._canvas_width)
        height = min(self._viewport_height, self._canvas_height)
        x0 = self._viewport_x
        y0 = self._viewport_y
        return QRect(x0, y0, width, height)

    def _load_tiles(self, init_matrix=False, skip_loaded=False,
                    old_tile_xstart=None, old_tile_ystart=None,
                    old_tile_xend=None, old_tile_yend=None):
        """
        Called internally to load tile from the image into the pixel
        array.

        Keyword arguments:
            init_matrix -- if True, reinitialize the pixel matrix
            slip_loaded -- if True, don't reload tiles that are already
                           loaded (you also need to ass the old_*
                           variables to indicate what what already loaded)
            old_tile_xstart -- the x tile number of the top-left corner
                               of the region of tiles that have already been
                               loaded. None=none already loaded.
            old_tile_ystart -- the y tile number of the top-left corner
                               of the region of tiles that have already beem
                               loaded.  None=none already loaded.
            old_tile_xend   -- the x tile number of the bottom-right corner
                               of the region of tiles that have already been
                               loaded.  None=none already loaded.
            old_tile_yend   -- the y tile number of the bottom-right corner
                               of the region of tiles that have already been
                               loaded.  None=none already loaded.
        """
        tiles_across = self._image.num_tiles_across(self._zoom)
        tiles_down = self._image.num_tiles_down(self._zoom)
        first = True
        for tiley in range(self._tile_ystart, self._tile_yend):
            if (tiley < 0 or tiley >= tiles_down):
                continue
            top_overlap = self._image.top_overlap(tiley)
            bottom_overlap = self._image.bottom_overlap(tiley, self._zoom)
            ypos = self._image.tile_height*(tiley-self._tile_ystart)
            for tilex in range(self._tile_xstart, self._tile_xend):
                if (tilex < 0 or tilex >= tiles_across):
                    continue
                if (skip_loaded and
                        tiley >= old_tile_ystart and tiley < old_tile_yend and
                        tilex >= old_tile_xstart and tilex < old_tile_xend):
                    # we already have this tile so skip it
                    continue

                left_overlap = self._image.left_overlap(tilex)
                right_overlap = self._image.right_overlap(tilex, self._zoom)
                xpos = self._image.tile_width*(tilex-self._tile_xstart)
                img = self._image.load_tile(tilex, tiley, self._zoom)
                height, width, channel = img.shape
                if (init_matrix and first):
                    self._pixels = \
                        np.zeros((self._canvas_height, self._canvas_width,
                                  channel), img.dtype)
                    first = False
                startx_on_tile = left_overlap
                starty_on_tile = top_overlap
                endx_on_tile = width - right_overlap
                endy_on_tile = height - bottom_overlap
                endx_on_canvas = xpos + endx_on_tile - left_overlap
                endy_on_canvas = ypos + endy_on_tile - top_overlap

                self._pixels[ypos:endy_on_canvas, xpos:endx_on_canvas] = \
                    img[starty_on_tile:endy_on_tile,
                        startx_on_tile:endx_on_tile]

    def zoom_to(self, zoom, centerx, centery):
        """
        Set the zoom to the given level, centered on the given viewport coord.
        Redraws the image.

        It is expected that this function wil be called when a user selects
        the zoom function in the image while pointing at a pixl.

        Positional arguments:
            zoom -- zoom level to go to
            centerx -- the pixel at this location within the viewport will be
                       the center of the new image.
            centery -- the pixel at this location within the viewport will be
                       the center of the new image.

            Returns:
                True if image needs to be reloaded (ie tiles have been added),
                False otherwise
        """
        if (zoom < self.min_available_zoom or
                zoom > self.max_available_zoom or
                zoom == self._zoom):
            return False

        # convert viewport coords to fullimage coords
        centerx = centerx+self._viewport_x_on_fullimage
        centery = centery+self._viewport_y_on_fullimage
        zoom_increase = zoom - self._zoom
        if (zoom_increase > 0):
            centerx = centerx << zoom_increase
            centery = centery << zoom_increase
        else:
            centerx = centerx >> -zoom_increase
            centery = centery >> -zoom_increase

        self._zoom = zoom
        self.load_image(centerx, centery)
        return True
