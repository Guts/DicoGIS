#! python3

"""
    Usage from the repo root folder:

        python -m unittest tests.test_georeader_postgis
"""

# #############################################################################
# ########## Libraries #############
# ##################################


# Standard library
import unittest
from os import environ
from pathlib import Path

# package
from dicogis.georeaders.Infos_PostGIS import ReadPostGIS

# #############################################################################
# ######## Globals #################
# ##################################

fixture_pgservice_conf = Path("tests/fixtures/database/pg_service.conf")

# #############################################################################
# ########## Classes ###############
# ##################################


class TestGeoReaderPostgis(unittest.TestCase):
    """Test info extractor for PostGIS datasets."""

    def setUp(self) -> None:
        self.assertTrue(fixture_pgservice_conf.exists())
        self.textos = {
            "srs_comp": "Compound",
            "srs_geoc": "Geocentric",
            "srs_geog": "Geographic",
            "srs_loca": "Local",
            "srs_proj": "Projected",
            "srs_vert": "Vertical",
            "geom_point": "Point",
            "geom_ligne": "Line",
            "geom_polyg": "Polygon",
        }

        return super().setUp()

    def test_open_connection(self):
        environ["PGSERVICEFILE"] = f"{fixture_pgservice_conf.resolve()}"
        dico_dataset = {}
        pg_reader = ReadPostGIS(
            service="dicogis_test", txt=self.textos, dico_dataset=dico_dataset
        )
