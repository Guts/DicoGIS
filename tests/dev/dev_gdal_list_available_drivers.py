from pprint import pprint

from osgeo import gdal, ogr

print(gdal.GetDriverCount())
driver_list = []
for i in range(gdal.GetDriverCount()):
    driver = gdal.GetDriver(i)
    driver_list.append(driver.GetDescription())

# list comprehension
driver_list = [
    (
        gdal.GetDriver(i).LongName,
        gdal.GetDriver(i).ShortName,
        gdal.GetDriver(i).GetDescription(),
    )
    for i in range(gdal.GetDriverCount())
]

# to get name as string
pprint(sorted(driver_list))
