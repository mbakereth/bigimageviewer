# Simple Python script to show how to create DeepZoom and tiled TIFF
# images using pyvips

import pyvips
image = pyvips.Image.new_from_file("BlackMarble_2016_C1_geo.tif")
image.write_to_file("test.tif", pyramid=True, tile=True, compression="jpeg")
image.dzsave("test_dzi")
# or:
# image.dzsave("test_dzi", depth="onetile")
