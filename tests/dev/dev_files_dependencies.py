from pathlib import Path

from osgeo import gdal

# VECTOR

source_dataset = "tests/fixtures/gisdata/data/good/vector/san_andres_y_providencia_administrative.shp"


dataset: gdal.Dataset = gdal.OpenEx(
    source_dataset,
    gdal.OF_READONLY | gdal.OF_VECTOR | gdal.OF_VERBOSE_ERROR,
)

print(dataset.GetFileList())
file_dependencies = [Path(filepath) for filepath in dataset.GetFileList()]
if len(file_dependencies):
    file_dependencies.pop(0)
print(file_dependencies)

# RASTER
source_dataset = (
    "/home/jmo/Documents/GIS Database/LotR/arda-master/data/rasters/10K.jpg"
)
source_dataset = "tests/fixtures/gisdata/data/good/raster/relief_san_andres.tif"

dataset: gdal.Dataset = gdal.OpenEx(
    source_dataset,
    gdal.OF_READONLY | gdal.OF_RASTER | gdal.OF_VERBOSE_ERROR,
)
file_dependencies = [Path(filepath) for filepath in dataset.GetFileList()]
if len(file_dependencies):
    file_dependencies.pop(0)
print(file_dependencies)
