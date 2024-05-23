import os
import random
from datetime import datetime
from string import ascii_letters

from osgeo import gdal, ogr, osr

# Create a spatial reference object
spatial_ref = osr.SpatialReference()

# Set the spatial reference using an EPSG code
# For example, EPSG:4326 corresponds to WGS84
spatial_ref.ImportFromEPSG(4326)


# GDAL >= 3.8 from official documentation
# with gdal.GetDriverByName("ESRI Shapefile").Create(
#     "test.shp", 0, 0, 0, gdal.GDT_Unknown
# ) as ds:

#     print(gdal.VectorInfo(ds))

# GDAL < 3.8

# shp_driver: gdal.Driver = gdal.GetDriverByName("ESRI Shapefile")
# shp_driver.
# shp: gdal.Dataset = shp_driver.Create("test-shp.shp", 0, 0, 0, gdal.GDT_Unknown)
# layer= shp.CreateLayer("states_convexhull", geom_type=ogr.wkbPolygon)

# # Add an ID field

# idField = ogr.FieldDefn("id", ogr.OFTInteger)
# layer.CreateField(idField)


# initiate shapefiles driver
driver: ogr.Driver = ogr.GetDriverByName("ESRI Shapefile")

# create a new shapefiles datasource
shapefile_path = "shapefile_points_100.shp"
if os.path.exists("shapefile_points_100.shp"):
    driver.DeleteDataSource(shapefile_path)  # make sure a file does not exist already
data_source: ogr.DataSource = driver.CreateDataSource(shapefile_path)

# add a layer
layer: ogr.Layer = data_source.CreateLayer(
    "random_points", spatial_ref, geom_type=ogr.wkbPoint
)

# create attribute fields

# ID
field_id = ogr.FieldDefn("ID", ogr.OFTInteger)
layer.CreateField(field_id)
# string
field_comment = ogr.FieldDefn("COMMENT", ogr.OFTString)
field_comment.SetWidth(150)
layer.CreateField(field_comment)

# integer
field_value = ogr.FieldDefn("Value", ogr.OFTInteger)
layer.CreateField(field_value)
# Date
field_date = ogr.FieldDefn("DateField", ogr.OFTDate)
layer.CreateField(field_date)
# DateTime
field_datetime = ogr.FieldDefn("DateTimeField", ogr.OFTDateTime)
layer.CreateField(field_datetime)
# Floating-point field
field_real = ogr.FieldDefn("FloatField", ogr.OFTReal)
field_real.SetPrecision(8)
field_real.SetNullable(False)
layer.CreateField(field_real)


# Générer 100 points avec des données aléatoires
for i in range(100):
    # create a point geometry
    point = ogr.Geometry(ogr.wkbPoint)

    # generate random coordinates
    x = random.uniform(-180, 180)
    y = random.uniform(-90, 90)
    point.AddPoint(x, y)

    # create a new feature
    feature = ogr.Feature(layer.GetLayerDefn())

    # add data to the feature object
    feature.SetGeometry(point)
    feature.SetField("ID", i)
    feature.SetField(
        1,
        "".join(
            random.choices(
                population=ascii_letters,
                weights=None,
                cum_weights=None,
                k=random.randint(1, 150),
            )
        ),
    )
    feature.SetField("Value", random.randint(1, 100))
    feature.SetField(3, datetime.today().isoformat())
    feature.SetField2(4, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    feature.SetField2(5, random.uniform(-5000, 15000))

    # add feature to the layer
    layer.CreateFeature(feature)

    # free memory by destroying the feature
    feature.Destroy()

# save and free file lock
data_source.FlushCache()
data_source = None
