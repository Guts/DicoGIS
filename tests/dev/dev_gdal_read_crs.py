from osgeo import gdal

from dicogis.georeaders.base_georeader import GeoReaderBase
from dicogis.georeaders.read_vector_flat_dataset import ReadVectorFlatDataset

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
    f"\n---- VECTOR: {source_dataset} ----\n\n",
    # osr_spatial_ref,
    type(osr_spatial_ref),
    # dir(osr_spatial_ref),
)

srs_name = osr_spatial_ref.GetName()
srs_code = osr_spatial_ref.GetAuthorityCode(None)
srs_registry = osr_spatial_ref.GetAuthorityName(None)

print("is geographic: ", osr_spatial_ref.IsDerivedGeographic())
print("is_dynamic: ", osr_spatial_ref.IsDynamic())
# print(osr_spatial_ref.ExportToPrettyWkt(0))

print(
    hasattr(dataset, "GetGeoTransform"),
    hasattr(dataset, "GetExtent"),
    hasattr(dataset, "GetEnvelope"),
)

print(f"{srs_name=}, {srs_registry=}, {srs_code=}")

print("\n\n-- with dicogis georeader base --\n")
georeader_base = GeoReaderBase(dataset_type="flat_vector")
srs_name, srs_registry, srs_code, srs_type = georeader_base.get_srs_details(
    dataset_or_layer=layer
)
print(f"{srs_name=}, {srs_registry=}:{srs_code=}, {srs_type=}")

print("\n\n-- with dicogis georeader flat vector --\n")
georeader_vector = ReadVectorFlatDataset()
metadataset = georeader_vector.infos_dataset(source_path=source_dataset)
print(
    f"{metadataset.crs_name=}, {metadataset.crs_registry=}, {metadataset.crs_registry_code=}, {metadataset.crs_type=}"
)
srs_name, srs_registry, srs_code, srs_type = georeader_vector.get_srs_details(
    dataset_or_layer=layer
)
print(f"{srs_name=}, {srs_registry=}:{srs_code=}, {srs_type=}")

# # -- RASTER
# source_dataset = (
#     "/home/jmo/Documents/GIS Database/LotR/arda-master/data/rasters/10K.jpg"
# )
# source_dataset = "/home/jmo/Documents/GIS Database/QGIS Training Data/QGIS-Training-Data-release_3.28/exercise_data/forestry/basic_map.tif"
# # source_dataset = "tests/fixtures/gisdata/data/good/raster/relief_san_andres.tif"

# dataset: gdal.Dataset = gdal.OpenEx(
#     source_dataset,
#     gdal.OF_READONLY | gdal.OF_RASTER | gdal.OF_VERBOSE_ERROR,
# )

# osr_spatial_ref = dataset.GetSpatialRef()

# print(
#     f"\n-- RASTER: {source_dataset} --\n\n",
#     osr_spatial_ref,
#     type(osr_spatial_ref),
#     dir(osr_spatial_ref),
# )

# print(osr_spatial_ref.GetAuthorityCode(None))
# print(osr_spatial_ref.GetAuthorityName(None))
# print(osr_spatial_ref.IsDerivedGeographic())
# print(osr_spatial_ref.ExportToPrettyWkt(0))

# print(
#     hasattr(dataset, "GetGeoTransform"),
#     hasattr(dataset, "GetExtent"),
#     hasattr(dataset, "GetEnvelope"),
# )
