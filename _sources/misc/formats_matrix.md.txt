# Informations gathered depending on format

## Vectors

| Column  | Description | Shapefile | MapInfo tables | GeoJSON | GML | KML | DWG |
| ------- | ----------- | --------- | -------------- | ------- | --- | --- | --- |
| Filename  | with its extension  | X | X | X | X | X | X |
| Path  |  Link to parent folder (only clikable on Excel) | X | X | X | X | X | X |
| Parent folder  | Name of parent folder | X | X | X | X | X | X |
| # fields  | Fields count | X | X | X | X | X | |
| # objects  | Features count | X | X | X | X | X | |
| Geometry type  | Can be: polygon, line or point | X | X | X | X | X | |
| Coordinate system (SRS)  | Spatial Reference System (see: http://epsg.io/) | X | X | X | X | X | |
| SRS type  | Can be: projected, geographic, compound | X | X | X | X | X | |
| EPSG  | EPSG reference code | X | X | X | X | X | |
| Spatial extent  | bounding box: Xmin, Xmax, Ymin, Ymax | X | X | X | X | X | |
| Creation (computer date)  | Creation date on the computer | X | X | X | X | X | X |
| Last update  | Last update date | X | X | X | X | X | X |
| Format  | file format | X | X | X | X | X | X |
| Field definitions  | fields properties list: `fieldName (fieldType, fieldLength=XX, fieldPrecision=X) ; etc.` | X | X | X | X | X | |
| Dependencies  | list of file dependencies | X | X | X | X | X | |
| Total size  | cumulated size of file and its dependencies | X | X | X | X | X | |

## Rasters

| Column  | Description | ECW | GeoTiff | JPEG |
| ------- | ----------- | ----| ------- | ---- |
| Filename  | with its extension  | X | X | X |
| Path  |  Link to parent folder (only clikable on Excel) | X | X | X |
| Parent folder  | Name of parent folder | X | X | X |
| # rows  | Fields count | X | X | X |
| # columns  | Features count | X | X | X |
| Pixel width  | Can be: polygon, line or point | X | X | X |
| Pixel height system (SRS)  | Spatial Reference System (see: http://epsg.io/) | X | X | X |
| X origin  | Can be: projected, geographic, compound | X | X | X |
| Y origin  | EPSG reference code | X | X | X |
| SRS type  | bounding box: Xmin, Xmax, Ymin, Ymax | X | X | X |
| EPSG  | Creation date on the computer | X | X | X |
| Spatial extent  | Last update date | X | X | X |
| Creation (computer date)  | file format | X | X | X |
| Last update  | Last update date | X | X | X | X | X |
| # bands  | Features count | X | X | X |
| Format  | file format | X | X | X |
| Compression rate  | file format |  |  | X |
| Color system  | file format |  |  | X |
| Dependencies  | list of file dependencies | X | X | X |
| Total size  | cumulated size of file and its dependencies | X | X | X |
| GDAL warnings  | file format | X | X | X |
