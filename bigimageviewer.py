"""
Main window and executable application for viewing DZI images using Qt.

Usage:
    bigimageviewer  --zoom n [filename]

Classes:
    MainWindow - Top-level Qt window containing the viewer
"""
import sys
import logging
import pathlib
import argparse

from PySide6.QtCore import QDir, QSize, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog
from PySide6.QtGui import QAction, QKeySequence

from bigimagecomponent import BigImageComponent


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
        self.setCentralWidget(self._viewer)

        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("&File")
        open = QAction("&Open", self, triggered=self._open)
        open.setShortcuts(QKeySequence.Open)
        self.menu_file.addAction(open)
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

    def load_and_focus(self, filename=None, zoom=-1, fit=False):
        """
        Call this after the window has displayed to load an image
        (eg using QTimer.singleshot()) and focus the component.

        Keyword arguments:
            filename -- if not None, load that image
            zoom -- set the initial zoom to this value (-1=fit to window)
            fit -- If true, window will be shaped to fit the image

        If if either width or height is -1, the window will be resized in
        both directions.

        The image is loaded to fit the window size that was specified
        in the constructor.  If fit is True, it will then be reduced to
        exactly fit that image.
        """
        if (filename is not None):
            self.load_file(filename, zoom)
        if (fit):
            width = self._viewer.image_width
            height = self._viewer.image_height
            size = self.size()
            childsize = self.centralWidget().size()
            dx = width - childsize.width()
            dy = height - childsize.height()
            self.resize(size.width() + dx, size.height() + dy)

        self._viewer.setFocus()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog='bigimageviewer',
        description='Displays a DZI image')

    parser.add_argument('filename', nargs='?')
    parser.add_argument(
        '-z', '--zoom', default=-1, type=int,
        help="Initial zoom (-1=fit to window, 0=zoomed out, 1=double " +
             "size, etc)")
    parser.add_argument(
        '-W', '--width', default=MainWindow.DEFAULT_WIDTH, type=int,
        help="Initial width of image viewport (not of window)")
    parser.add_argument(
        '-H', '--height', default=MainWindow.DEFAULT_HEIGHT, type=int,
        help="Initial height of image viewport (not of window)")
    parser.add_argument(
        '-F', '--fit', action="store_true",
        help="If set, window will be reduced to the image size")

    args = parser.parse_args()
    filename = args.filename
    zoom = args.zoom
    width = args.width
    height = args.height
    fit = args.fit

    logging.getLogger().setLevel(logging.INFO)
    app = QApplication()
    w = MainWindow(viewport_width=width, viewport_height=height)

    w.show()
    QTimer.singleShot(1, lambda: w.load_and_focus(filename, zoom, fit))

    sys.exit(app.exec())
