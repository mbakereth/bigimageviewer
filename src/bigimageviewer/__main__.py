import sys
import logging
import argparse

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from .app import MainWindow

parser = argparse.ArgumentParser(
    prog='bigimageviewer',
    description='Displays a tiled image')

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

if (filename is not None):
    w.resize_viewer(width, height)
    w.load_file(filename, zoom)
    if (fit):
        w.fit_to_image()

w.show()
QTimer.singleShot(1, w.focusViewer)

sys.exit(app.exec())
