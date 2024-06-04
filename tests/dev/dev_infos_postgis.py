from osgeo import gdal, ogr

# gdal.SetConfigOption("PG_LIST_ALL_TABLES", "YES")

pg_service_name = "my_pg_service_name"

conn: gdal.Dataset = gdal.OpenEx(
    f"postgresql://?service={pg_service_name}",
    gdal.OF_READONLY | gdal.OF_VECTOR | gdal.OF_VERBOSE_ERROR,
)

print(f"{conn.GetLayerCount()} tables found in PostGIS database.")

for idx_layer in range(conn.GetLayerCount()):
    layer: ogr.Layer = conn.GetLayerByIndex(idx_layer)
    print(f"\nLayer: {layer.GetName()}")
    print(f"{layer.GetFeatureCount()} features")
    geom_type = layer.GetGeomType()
    print(f"Geometry Type: {ogr.GeometryTypeToName(geom_type)}")
    layer_def = layer.GetLayerDefn()
    print(f"{layer_def.GetFieldCount()} feature attributes")
    spatial_ref = layer.GetSpatialRef()
    print(f"Spatial reference from layer: {spatial_ref}")
    feature = layer.GetNextFeature()
    if not feature:
        continue
    geometry = feature.GetGeometryRef()
    spatial_ref = geometry.GetSpatialReference()
    print(f"Spatial reference from geometry: {spatial_ref}")

    # Get the index of the geometry field
    geom_field_index = layer_def.GetGeomFieldIndex("geom")
    if geom_field_index == -1:
        raise Exception(f"Geometry column 'geom' not found in table {table_name}")

    # Get the geometry field definition
    geom_field_defn = layer_def.GetGeomFieldDefn(geom_field_index)
    # Get the SRID from the geometry field definition
    print(geom_field_defn.GetSpatialRef())
    print(f"Geometry column: {layer.GetGeometryColumn()}")

    # sql_command = (
    #     "SELECT ST_SRID('the_geom') AS srid FROM " + f'"{layer.GetName()}"' + "LIMIT 1;"
    # )
    # result = conn.ExecuteSQL(sql_command)
    # print(result)

    del layer, layer_def, geom_field_defn
