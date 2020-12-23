# -*- coding: UTF-8 -*-
#! python3

# Standard library
import logging
from pathlib import Path
import unittest

# package
from dicogis.georeaders import ReadVectorFlatDataset

# variables
extension_pattern = "**/*.shp"
fixtures_folder = "tests/fixtures/gisdata/data/good/vector/"
logging.basicConfig(level=logging.DEBUG)

# list fixtures
fixtures_shp = Path(fixtures_folder).glob(extension_pattern)

# instanciate georeader
georeader_vector = ReadVectorFlatDataset()

for f in fixtures_shp:
    dico_layer = {}
    dico_txt = {}
    georeader_vector.infos_dataset(str(f.resolve()), dico_layer, dico_txt)
    print(dico_layer.keys())
    