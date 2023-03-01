Big Image Viewer
================

This is a Python package to display potentially very large image.  Currently
the only supported format is DeepZoom (.dzi).

It can be used as a standalone application or as a Qt widget in your own
Qt application.  The component supports panning by click and drag.  It also
supports zooming with the + button (zoom is centered on the point where the
mouse is) and zooming out with the - button (again, centerd on the mouse
location.)  Pressing q exits the application.  These keys can be customized
or switched off.

For an example of how to use the component, see `bigimageviewer.py`
