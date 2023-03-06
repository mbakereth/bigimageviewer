Big Image Viewer
================

Big Image Viewer is a package to displayed tiled image pyramids.  It's 
purpose is efficiently to pan and zoom very large images in real time.
It is designed for low memory footprint and fast response.

It only supports tiled pyramid images.  It reads DeepZoom (.dvi) files
natively and other formats using the large_image package (with TIFF being
the only format that has been tested, and only the TIFF library being
loaded automatically in the dependencies).  If the image is not tiled, it will
exit.

Images are only displayed at the resolution of one of the images already in the
pyramid.  Therefore it is recommended that users create an image pyramid to
meet their requirements before viewing it with this package.

Big Image Viewer can be used as a standalone application or as a Qt widget in 
your own Qt application.  The component supports panning by click and drag.
It also supports zooming with the + button (zoom is centered on the point
where the mouse is) and zooming out with the - button (again, centerd on the
mouse location.)  Pressing q exits the application.  These keys can be 
customized or switched off.

DeepZoom images are supported natively.  Other tiled image formats are 
supported through the large_image package.  The package dependencies include
large_image with the `tiff` source.

Installation
------------

As for all python packages. we recommend you create a virtual environment, eg:

```bash
virtualenv venv
venv/bin/activate
```
If you make make, you can build and install with

```bash
make
make install
```

If you don't have make, install with

```bash
pip install -r requirements.txt
python3 -m pip install --upgrade build
python3 -m build
pip install dist/bigimageviewer-VERSION-py3-none-any.whl
```
where substituting `VERSION` for the version you built.

Example Usage
-------------

```python
from bigimageviewer import BigImageComponent

layout = QVBoxLayout()
viewer = BigImageComponent(width=512, height=512)
layout.addWidget(viewer)
viewer.load_image("myimage.dzi")  # or a .tif file
```

This will load the image at the biggest available zoom that fits in the 512x512
window.  

In DZI images, the minimum available zoom is 0.  How big that is
varies according to the parameters used when it was created - it may be 1x1
pixel, it may be bigger.  The maximum zoom depends on original dimensions
and the minimum zoom that was selected.  To determine the range of possible
zooms, you can do the following:

```python
from bigimageviewer import DZImage
image = DZImage("myimage.dzi")
min_zoom = image.min_zoom
max_zoom = image.max_zoom
min_width = image.width_for_zoom(min_zoom)
min_height = image.height_for_zoom(min_zoom)
```

The same applies for TIFF images (or potentially other tiled formats
supported by the large_image package).  Replace the first two lines above with

```python
from bigimageviewer import LIImage
image = LIImage("myimage.tif")
```

To load an image with a different zoom, do the following:

```python
viewer.zoom = 4
viewer.load_image("myimage.dzi")
```

`zoom` should be between `min_zoom` and `max_room` inclusively, or `-1` for
maximum that fits in the window.

Navigation in the image
-----------------------

You can pan around the image by click-dragging or mouse wheel/Mac two finger
gestures.

You can zoom in by double-clicking - the zoomed image will be centred on the
clicked pixedl.  Zoom out with shift-double-click.  Again, the zoomed-out image
will be centred at the clicked pixel.

By default, the `+` and `-` keys also zoom, though this can be configured or
switched off.  In the standalone application, the `q` quits the viewer but
this is not enabled by default when you just use the component in your
application.

Creating Images
---------------

The package `libvips` can be used to create DZI files from TIFF, JPEG, PNG
etc.  For example

```bash
vips dzsave input.tiff outimage
```

This will create a file called `outimage.dzi` and a directory `outimage_files`
with tiles of size 254 with an overlap of 1 pixel either side, a minimum zoom
of 1x1 and a maximum zoom of the original image size.

Alternatively, the Python wrapper for vips, pyvips, can be used:

```python
import pyvips
image = pyvips.Image.new_from_file("myimages.tif")
image.dzsave("test_dzi")
```

Alternatively, TIFF images can be saved.  In Python, replace the last line
above with

```python
image.write_to_file("test.tif", pyramid=True, tile=True, compression="jpeg")
```

Command Line Viewer
-------------------

This package also includes a simple command line viewer:

```bash
python -m bigimageviewer [options] [filename]
```

Command line Options:

|Option           |Description                                               |  
|:----------------|:---------------------------------------------------------|
|--zoom or -z n   | set the zoom to n (-1 for fit to window)                 |
|--width or -W n  | sets the initial width of the viewer                     |
|--height or -H n | sets the initial height of the viewer                    |
|--fit or -F      | after loading the image, reduce the window size to fit it|

