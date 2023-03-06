"""
Main window and executable application for viewing DZI images using Qt.

Usage:
    bigimageviewer  [options] [filename]
      -z or --zoom n   : specify the zoom (0=smallest, 1=twice as big, etc)
      -W or --width n  : set initial max with of main viewer (default 512)
      -W or --height n : set initial max height of main viewer (default 512)
      -F or --fit      : fit window to size of image

Window interaction:
    Scrolling is done with click-drag or wheel/two finger gestures.
    Zooming in is with the + key or double-click.  Zooming is centered
    at the point the mouse was at.
    Zooming out is with the - key or shift-double-click, also centered
    where the mouse was at.
    The q key exits.
    The image can be resized.  It won't change the zoom but will load more
    picture, or discard some of the picture, as needed.

Classes:
    MainWindow - Top-level Qt window containing the viewer
"""
import pathlib

from PySide6.QtCore import QDir, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog
from PySide6.QtGui import QAction, QKeySequence

from .bigimagecomponent import BigImageComponent


class MainWindow(QMainWindow):
    """
    Top-level Qt window for displaying an image.

    Most functionality is in bigimagecomponent.BigImageComponent
    """

    DEFAULT_WIDTH = 512
    DEFAULT_HEIGHT = 512

    def __init__(self, parent=None, viewport_width=None, viewport_height=None):
        """
        Creates the image viewer window

        Keyword arguments:
            parent -- Qt component this is a child of
            viewport_width -- initial width of viewport (not window)
            viewport_height -- initial height of viewport (not window)
        """
        super().__init__(parent)

        # image viewer
        if (viewport_width == -1 or viewport_width is None):
            viewport_width = MainWindow.DEFAULT_WIDTH
        if (viewport_height == -1 or viewport_height is None):
            viewport_height = MainWindow.DEFAULT_HEIGHT

        self._viewer = BigImageComponent(width=viewport_width,
                                         height=viewport_height)
        self._viewer.exit_key = Qt.Key.Key_Q
        self.setCentralWidget(self._viewer)

        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("&File")
        open = QAction("&Open", self, triggered=self._open)
        open.setShortcuts(QKeySequence.Open)
        self.menu_file.addAction(open)
        app = QApplication.instance()
        exit = QAction("E&xit", self, triggered=app.quit)
        self.menu_file.addAction(exit)
        self._first_file_dialog = True

    def _open(self):
        dialog = QFileDialog(self, "Open File")
        self._initialize_image_filedialog(dialog, QFileDialog.AcceptOpen)
        while (dialog.exec() == QDialog.Accepted and not
               self.load_file(dialog.selectedFiles()[0])):
            pass

    def load_file(self, filename, zoom=-1):
        """
        Loads an image into the viewer.

        Positional arguments:
            filename -- filename to load.  Only DZI images supported at
                        present.  If it doesn't end in .dzi, .dzi is added.
        """
        ret = self._viewer.load_image(filename, zoom)
        path = pathlib.Path(filename)
        self.setWindowTitle(path.stem)
        return ret

    def resize_viewer(self, width, height):
        """ Resizes the image view to the given dimensions """
        self._viewer.resize(width, height)

    def _initialize_image_filedialog(self, dialog, acceptMode):
        if self._first_file_dialog:
            self._first_file_dialog = False
            directory = QDir.currentPath()
            dialog.setDirectory(directory)
        dialog.setMimeTypeFilters(["image/dzi"])
        dialog.selectMimeTypeFilter("image/dzi")
        dialog.setAcceptMode(acceptMode)
        if acceptMode == QFileDialog.AcceptSave:
            dialog.setDefaultSuffix("dzi")

    def fit_to_image(self):
        """ Resizes the viewer to exactly fit the loaded image """
        width = self._viewer.image_width
        height = self._viewer.image_height
        self._centralWidgetResize(width, height)

    def _centralWidgetResize(self, x, y):
        # If the window is not visible, it doesn't keep its layout up to date,
        # so force it.
        if not self.isVisible():
            self.layout().update()
        # Does nothing if the layout is already up to date (and the window is
        # visible).
        self.layout().activate()
        size = self.size()
        childsize = self.centralWidget().size()
        dx = size.width() - childsize.width()
        dy = size.height() - childsize.height()
        self.resize(x + dx, y + dy)

    def focusViewer(self):
        """ Puts the window focus on the viewer """
        self._viewer.setFocus()
