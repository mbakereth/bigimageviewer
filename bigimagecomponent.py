"""
Qt module for image viewer widget.

Classes:
    BigImageComponent -- Qt widget that displays an image,
                         with scrolling and zooming
    ImageLabel -- Holds the image pixmap.  Used internally by ImageViewer
"""
import sys

from PySide6.QtCore import QSize, Qt, QRect, QEvent, QObject, Signal
from PySide6.QtWidgets import QLabel, QFrame, QSizePolicy
from PySide6.QtGui import QColorSpace, QPixmap, QCursor

from dzimage import *
from loadedimage import *


class ImageLabel(QLabel):
    """
    This class holds the image pixap.

    It is a separate class from the ImageViewer that contains it because, out
    of efficiency reasons, a larger image is loaded than fits inside the
    viewport.
    """
    def __init__(self, parent=None, width=512, height=512):
        super().__init__(parent)
        # self.setStyleSheet("background-color: blue")
        self._initial_width = width
        self._initial_height = height

    def sizeHint(self):
        return QSize(self._initial_width, self._initial_height)


class BigImageComponent(QLabel):
    """
    Qt widget for displaying an image

    Allows scrolling, with click and drag, zooming in with the + key and out
    with the - key.  Zooming will be centered on the point in the image 
    under the mouse where the key was pressed.

    Pressing the q key exits the application.

    You can change this behaviour with the zoom_in_key, zoom_out_key and
    exit_key properties.
    """

    # keyPressed = Signal(QEvent)

    MIN_WIDTH = 32
    MIN_HEIGHT = 32

    """ Pressing this will zoom the image. """
    DEFAULT_ZOOM_IN_KEY = Qt.Key.Key_Plus
    DEFAULT_ZOOM_OUT_KEY = Qt.Key.Key_Minus
    DEFAULT_EXIT_KEY = Qt.Key.Key_Q


    def __init__(self, parent=None, width=512, height=512):
        """
        Constructs the image viewer widget.

        Keyword arguments:
            parent -- Qt widget to make this a child of
            width  -- initial width of the widget and image viewport it
                      contains (it can be resized after)
            height -- initial height of the widget and image viewport it
                      contains (it can be resized after)
        """
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        # self.setStyleSheet("background-color: yellow")
        self._initial_width = width
        self._initial_height = height
        self._image_label = ImageLabel(self, width, height)
        self._image_label.setAlignment(Qt.AlignLeft)
        self._image = None
        self._loaded_image = None
        self._qimage = None
        self._mouse_drag_from_pos = None
        self.setMinimumSize(BigImageComponent.MIN_WIDTH,
                            BigImageComponent.MIN_HEIGHT)
        self._current_width = None
        self._current_height = None

        self._zoom_in_key = BigImageComponent.DEFAULT_ZOOM_IN_KEY
        self._zoom_out_key = BigImageComponent.DEFAULT_ZOOM_OUT_KEY
        self._exit_key = BigImageComponent.DEFAULT_EXIT_KEY

    @property
    def zoom_in_key(self):
        """ Returns the key that zooms in, or None if none set (default + )"""
        return self._zoom_in_key

    @zoom_in_key.setter
    def zoom_in_key(self, value):
        """
        Sets the key that zooms in.  None means no key

        Positional parameters:
            value -- a QKey.  If set to None, zoom in is disabled
        """
        self.zoom_in_key = value

    @property
    def zoom_out_key(self):
        """ Returns the key that zooms out, or None if none set (default - )"""
        return self._zoom_out_key

    @zoom_out_key.setter
    def zoom_out_key(self, value):
        """
        Sets the key that zooms out.  None means no key

        Positional parameters:
            value -- a QKey.  If set to None, zoom out is disabled
        """
        self.zoom_out_key = value

    @property
    def exit_key(self):
        """ Returns the key exits the app, or None if none set (default - )"""
        return self._exit_key

    @zoom_out_key.setter
    def exit_key(self, value):
        """
        Sets the key that exits the app.  None means no key

        Positional parameters:
            value -- a QKey.  If set to None, exit by key press is disabled
        """
        self.exit_key = value

    def sizeHint(self):
        """
        Tells Qt the initial size of the viewer, which is specified in the
        constructor
        """
        return QSize(self._initial_width, self._initial_height)

    def load_image(self, filename, zoom=-1):
        """
        Loads and displays the image at the given filename, with the given
        zoom.

        Positional arguments:
            filename -- filename of image to load.  Only DZI supported
                        currently

        Keyword arguments:
            zoom -- Initial zoom level with 0 being most zoomed out and greater
                    numbers being zoomed in.
                    There is no way to determine the maximum zoom other than
                    querying the image.
                    A zoom of -1 means choose the maximum zoom that completel
                    fits within the widget
        """
        self._image = DZImage(filename)
        self._loaded_image = LoadedImage(self._image)
        self._loaded_image.viewport_on_fullimage = (0, 0)
        self._loaded_image.zoom = zoom
        viewport_geom = self._image_label.geometry()
        self._loaded_image.viewport_size \
            = (viewport_geom.width(), viewport_geom.height())
        self._loaded_image.load_image()

        return self._redraw_image()

    def _redraw_image(self):
        self._qimage, qrect = self._loaded_image.to_qimage()
        if self._qimage.colorSpace().isValid():
            self._qimage.convertToColorSpace(QColorSpace.SRgb)
        self._image_label.setPixmap(QPixmap.fromImageInPlace(self._qimage))
        self._image_label.setGeometry(
            -qrect.x(), -qrect.y(),
            qrect.width() + qrect.x(),
            qrect.height() + qrect.y()
        )
        self._current_width = self.size().width()
        self._current_height = self.size().height()
        return True

    def mouseMoveEvent(self, e):
        """
        A click and drag scrolls the image (there are no scrollbars)
        """
        if (e.buttons() == Qt.LeftButton):
            fromx = int(self._mouse_drag_from_pos.x())
            fromy = int(self._mouse_drag_from_pos.y())
            tox = int(e.position().x())
            toy = int(e.position().y())
            if (fromx == tox and fromy == toy):
                return
            self._mouse_drag_from_pos = e.position()
            dx = tox - fromx
            dy = toy - fromy
            self._scroll(dx, dy)

    def _scroll(self, dx, dy):
        need_redraw = self._loaded_image.scroll(dx, dy)
        if (need_redraw):
            self._qimage, qrect = self._loaded_image.to_qimage()
            self._image_label.setPixmap(
                QPixmap.fromImageInPlace(self._qimage)
            )
            self._image_label.setGeometry(
                -qrect.x(), -qrect.y(),
                qrect.width() + qrect.x(),
                qrect.height()+qrect.y()
            )
        else:
            qrect = self._loaded_image.get_rect()
            self._image_label.setGeometry(
                -qrect.x(), -qrect.y(),
                qrect.width() + qrect.x(),
                qrect.height() + qrect.y())

    def mousePressEvent(self, e):
        """
        Clicking focuses the window so that it can receive keystrokes.

        It also remembers the point it was clicked at to start the scrolling
        """
        if (e.buttons() == Qt.LeftButton):
            self._mouse_drag_from_pos = e.position()
        self.setFocus()

    def mouseReleaseEvent(self, e):
        """ Stops scrolling """
        self._mouse_drag_from_pos = None

    def wheelEvent(self, e):
        """
        Same as a click and drag - scrolls the image
        """
        dx = e.pixelDelta().x()
        dy = e.pixelDelta().y()
        if (dx != 0 or dy != 0):
            self._scroll(dx, dy)

    def keyPressEvent(self, event):
        """ Handles zoom in, zoom out and exit key presses """
        key = event.key()
        pos = self.mapFromGlobal(QCursor.pos())
        x = pos.x()
        y = pos.y()
        changed = False
        if (self._zoom_out_key is not None and key == self._zoom_out_key):
            changed \
                = self._loaded_image.zoom_to(self._loaded_image.zoom-1, x, y)
        elif (self._zoom_in_key is not None and key == self._zoom_in_key):
            changed \
                = self._loaded_image.zoom_to(self._loaded_image.zoom+1, x, y)
        elif (self._exit_key is not None and key == self._exit_key):
            sys.exit(0)

        if (changed):
            self._qimage, qrect = self._loaded_image.to_qimage()
            self._image_label.setPixmap(QPixmap.fromImageInPlace(self._qimage))
            self._image_label.setGeometry(
                -qrect.x(), -qrect.y(),
                qrect.width() + qrect.x(),
                qrect.height()+qrect.y()
            )

    def resizeEvent(self, event):
        """ Ensures the right amount of image is loaded as the window is
            resized.

            Doesn't change the zoom.
        """
        if (self._loaded_image is None):
            return
        new_width = event.size().width()
        new_height = event.size().height()
        self._loaded_image.viewport_size = (new_width, new_height)
        self._loaded_image.load_image()
        self._redraw_image()

    @property
    def image_width(self):
        if (self._loaded_image is None):
            return None
        return self._image.width_for_zoom(self._loaded_image.zoom)

    @property
    def image_height(self):
        if (self._loaded_image is None):
            return None
        return self._image.height_for_zoom(self._loaded_image.zoom)
