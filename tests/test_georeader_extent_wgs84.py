#! python3  # noqa: E265

"""
Tests for GeoReaderBase.get_extent_wgs84().

Usage from the repo root folder:
    pytest tests/test_georeader_extent_wgs84.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
from pathlib import Path

# 3rd party
import pytest
from osgeo import gdal, ogr, osr

# project
from dicogis.georeaders.base_georeader import GeoReaderBase
from dicogis.georeaders.read_raster import ReadRasters
from dicogis.georeaders.read_vector_flat_dataset import ReadVectorFlatDataset


# ##############################################################################
# ########## Globals ###############
# ##################################

GISDATA = Path(__file__).parent / "fixtures" / "gisdata" / "data" / "good"

# ##############################################################################
# ########## Functions #############
# ##################################


def _srs(epsg: int) -> osr.SpatialReference:
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return srs


def _memory_layer(wkt: str, srs: osr.SpatialReference | None):
    """Build an in-memory layer holding a single geometry.

    Returns:
        the dataset, to keep alive, and its layer
    """
    dataset = gdal.GetDriverByName("MEM").Create("", 0, 0, 0, gdal.GDT_Unknown)
    layer = dataset.CreateLayer("test", srs=srs, geom_type=ogr.wkbUnknown)
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
    layer.CreateFeature(feature)
    return dataset, layer


# ##############################################################################
# ########## Tests ##################
# ##################################


@pytest.fixture
def reader() -> GeoReaderBase:
    return GeoReaderBase(dataset_type="flat_vector", localized_strings={})


def test_layer_in_wgs84_is_returned_as_is(reader):
    _dataset, layer = _memory_layer(
        "MULTIPOINT((-81.5 13.25),(-81.25 13.5))", _srs(4326)
    )

    assert reader.get_extent_wgs84(layer) == (-81.5, 13.25, -81.25, 13.5)


def test_projected_layer_is_reprojected_with_longitude_first(reader):
    _dataset, layer = _memory_layer(
        "MULTIPOINT((652000 6861000),(653000 6862000))", _srs(2154)
    )

    west, south, east, north = reader.get_extent_wgs84(layer)

    assert 2.3 < west < east < 2.4
    assert 48.8 < south < north < 48.9


def test_reprojection_takes_bulging_edges_into_account(reader):
    """In Lambert-93, the top edge of this box reaches further north in its middle
    than at its corners, by about 20 km."""
    _dataset, layer = _memory_layer(
        "MULTIPOINT((100000 6100000),(1200000 7100000))", _srs(2154)
    )

    _west, _south, _east, north = reader.get_extent_wgs84(layer)

    assert north == pytest.approx(50.9958, abs=0.001)


def test_no_crs_means_no_extent(reader):
    _dataset, layer = _memory_layer("POINT(1 2)", None)

    assert reader.get_extent_wgs84(layer) is None


def test_extent_is_more_precise_than_bbox():
    metadataset = ReadVectorFlatDataset().infos_dataset(
        source_path=GISDATA / "vector/san_andres_y_providencia_coastline.shp"
    )

    assert metadataset.bbox == (-81.4, -81.35, 13.32, 13.39)
    assert metadataset.bbox_wgs84 == pytest.approx(
        (-81.396294, 13.320289, -81.349025, 13.385961)
    )


def test_raster_extent_order_does_not_depend_on_gdal_version():
    metadataset = ReadRasters().infos_dataset(
        source_path=GISDATA / "raster/relief_san_andres.tif"
    )

    assert metadataset.bbox_wgs84 == pytest.approx((-84.0, 11.0, -78.0, 15.0))


def test_raster_extent_includes_rotation(reader):
    dataset = gdal.GetDriverByName("MEM").Create("", 10, 10)
    dataset.SetGeoTransform((0.0, 1.0, 1.0, 0.0, 1.0, -1.0))
    dataset.SetSpatialRef(_srs(4326))

    assert reader.get_extent_wgs84(dataset) == (0.0, -10.0, 20.0, 10.0)


def test_raster_without_crs_means_no_extent(reader):
    dataset = gdal.GetDriverByName("MEM").Create("", 10, 10)

    assert reader.get_extent_wgs84(dataset) is None


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    pytest.main([__file__])
