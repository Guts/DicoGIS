from osgeo import gdal

# VECTOR

source_dataset = "tests/fixtures/gisdata/data/good/vector/san_andres_y_providencia_administrative.shp"

dataset: gdal.Dataset = gdal.OpenEx(
    source_dataset,
    gdal.OF_READONLY | gdal.OF_VECTOR | gdal.OF_VERBOSE_ERROR,
)

# from Layer
layer = dataset.GetLayer()
osr_spatial_ref = layer.GetSpatialRef()

print(
    f"\n-- VECTOR: {source_dataset} --\n\n",
    osr_spatial_ref,
    type(osr_spatial_ref),
    dir(osr_spatial_ref),
)

print(osr_spatial_ref.GetAuthorityCode(None))
print(osr_spatial_ref.GetAuthorityName(None))
print(osr_spatial_ref.IsDerivedGeographic())
print(osr_spatial_ref.ExportToPrettyWkt(0))

print(
    hasattr(dataset, "GetGeoTransform"),
    hasattr(dataset, "GetExtent"),
    hasattr(dataset, "GetEnvelope"),
)

# -- RASTER
source_dataset = (
    "/home/jmo/Documents/GIS Database/LotR/arda-master/data/rasters/10K.jpg"
)
source_dataset = "/home/jmo/Documents/GIS Database/QGIS Training Data/QGIS-Training-Data-release_3.28/exercise_data/forestry/basic_map.tif"
# source_dataset = "tests/fixtures/gisdata/data/good/raster/relief_san_andres.tif"

dataset: gdal.Dataset = gdal.OpenEx(
    source_dataset,
    gdal.OF_READONLY | gdal.OF_RASTER | gdal.OF_VERBOSE_ERROR,
)

osr_spatial_ref = dataset.GetSpatialRef()

print(
    f"\n-- RASTER: {source_dataset} --\n\n",
    osr_spatial_ref,
    type(osr_spatial_ref),
    dir(osr_spatial_ref),
)

print(osr_spatial_ref.GetAuthorityCode(None))
print(osr_spatial_ref.GetAuthorityName(None))
print(osr_spatial_ref.IsDerivedGeographic())
print(osr_spatial_ref.ExportToPrettyWkt(0))

print(
    hasattr(dataset, "GetGeoTransform"),
    hasattr(dataset, "GetExtent"),
    hasattr(dataset, "GetEnvelope"),
)
