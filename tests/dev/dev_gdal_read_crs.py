from osgeo import gdal

source_dataset = "tests/fixtures/gisdata/data/good/vector/san_andres_y_providencia_administrative.shp"

dataset: gdal.Dataset = gdal.OpenEx(
    source_dataset,
    gdal.OF_READONLY | gdal.OF_VECTOR | gdal.OF_VERBOSE_ERROR,
)

# from Layer
layer = dataset.GetLayer()
osr_spatial_ref = layer.GetSpatialRef()


print(osr_spatial_ref, type(osr_spatial_ref), dir(osr_spatial_ref))

print(osr_spatial_ref.GetAuthorityCode(None))
print(osr_spatial_ref.GetAuthorityName(None))
print(osr_spatial_ref.IsDerivedGeographic())
print(osr_spatial_ref.ExportToPrettyWkt(0))
