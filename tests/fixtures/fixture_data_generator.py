import random
from datetime import datetime
from pathlib import Path
from string import ascii_letters

from osgeo import ogr, osr

# -- GLOBALS --

# Create a spatial reference object
spatial_ref = osr.SpatialReference()
spatial_ref.ImportFromEPSG(4326)


def create_random_polygon(num_vertices: int):
    ring = ogr.Geometry(ogr.wkbLinearRing)
    # Add random points
    for _ in range(num_vertices):
        lon = random.uniform(-180, 180)
        lat = random.uniform(-90, 90)
        ring.AddPoint(lon, lat)
    # Ensure the polygon is closed by adding the first point at the end
    ring.AddPoint(ring.GetPoint(0)[0], ring.GetPoint(0)[1])

    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return poly


def generate_random_dataset_vector(
    gdal_format: str,
    output_path: Path,
    features_number: int = 100,
    geometry_type=ogr.wkbPoint,
) -> Path:
    # initiate driver
    driver: ogr.Driver = ogr.GetDriverByName(gdal_format)

    output_path.parent.mkdir(exist_ok=True, parents=True)

    if output_path.exists():
        output_path.unlink()
        driver.DeleteDataSource(
            f"{output_path.resolve()}"
        )  # make sure a file does not exist already

    # create a new shapefiles datasource
    data_source: ogr.DataSource = driver.CreateDataSource(f"{output_path.resolve()}")

    # add a layer
    layer: ogr.Layer = data_source.CreateLayer(
        f"random_{str(geometry_type).removeprefix('ogr.')}",
        spatial_ref,
        geom_type=geometry_type,
    )

    # -- Attribute Fields --

    # ID
    field_id = ogr.FieldDefn("ID", ogr.OFTInteger)
    layer.CreateField(field_id)

    # integer
    field_value = ogr.FieldDefn("Value", ogr.OFTInteger)
    layer.CreateField(field_value)

    # string
    field_comment = ogr.FieldDefn("COMMENT", ogr.OFTString)
    field_comment.SetWidth(150)
    layer.CreateField(field_comment)

    # Date
    field_date = ogr.FieldDefn("DateField", ogr.OFTDate)
    layer.CreateField(field_date)

    # DateTime
    field_datetime = ogr.FieldDefn("DateTimeField", ogr.OFTDateTime)
    layer.CreateField(field_datetime)

    # float (real)
    field_real = ogr.FieldDefn("FloatField", ogr.OFTReal)
    field_real.SetPrecision(8)
    field_real.SetNullable(False)
    layer.CreateField(field_real)

    # -- Features objects --
    for i in range(features_number):
        # create a new feature
        feature = ogr.Feature(layer.GetLayerDefn())

        if geometry_type == ogr.wkbPoint:
            # create a point geometry
            point = ogr.Geometry(geometry_type)

            # generate random coordinates
            x = random.uniform(-180, 180)
            y = random.uniform(-90, 90)
            point.AddPoint(x, y)

            feature.SetGeometry(point)

            # add attribute fields to the feature object
            feature.SetField("ID", i)
            feature.SetField("Value", random.randint(1, 100))
            feature.SetField(
                2,
                "".join(
                    random.choices(
                        population=ascii_letters,
                        weights=None,
                        cum_weights=None,
                        k=random.randint(1, 150),
                    )
                ),
            )
            feature.SetField(3, datetime.today().isoformat())
            feature.SetField2(4, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            feature.SetField2(5, random.uniform(-5000, 15000))

            # add feature to the layer
            layer.CreateFeature(feature)

        if geometry_type == ogr.wkbPolygon:
            polygon = create_random_polygon(random.randint(2, 10))

            feature.SetField("ID", i)
            feature.SetGeometry(polygon)

            # add attribute fields to the feature object
            feature.SetField("ID", i)
            feature.SetField("Value", random.randint(1, 100))
            feature.SetField(
                2,
                "".join(
                    random.choices(
                        population=ascii_letters,
                        weights=None,
                        cum_weights=None,
                        k=random.randint(1, 150),
                    )
                ),
            )
            feature.SetField(3, datetime.today().isoformat())
            feature.SetField2(4, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            feature.SetField2(5, random.uniform(-5000, 15000))

        layer.CreateFeature(feature)
        # free memory by destroying the feature
        feature.Destroy()

    # save and free file lock
    data_source.FlushCache()
    data_source = None


# #############################################################################
# ##### Main #######################
# ##################################
if __name__ == "__main__":
    generate_random_dataset_vector(
        "ESRI Shapefile",
        features_number=5000,
        geometry_type=ogr.wkbPoint,
        output_path=Path("tests/dev/tmp/random_points_5000_4326.shp"),
    )

    # polygons
    generate_random_dataset_vector(
        "ESRI Shapefile",
        features_number=5000,
        geometry_type=ogr.wkbPolygon,
        output_path=Path("tests/dev/tmp/random_polygons_5000_4326.shp"),
    )
