#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from os import listdir, path, walk
from typing import Optional, Union

# 3rd party
from osgeo import ogr

# project
from dicogis.models.dataset import MetaDataset

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class Utils:
    """TO DOC"""

    def __init__(self, ds_type="flat"):
        """Instanciate Utils class."""
        self.ds_type = ds_type
        super().__init__()

    def list_dependencies(self, main_file_path, exclude=""):
        """List dependant files around a main file."""
        if exclude == "auto":
            exclude = path.splitext(path.abspath(main_file_path).lower())[1]
        else:
            pass
        # dependencies
        dependencies = [
            f
            for f in listdir(path.dirname(main_file_path))
            if path.splitext(path.abspath(f))[0] == path.splitext(main_file_path)[0]
            and not path.splitext(path.abspath(f).lower())[1] == exclude
        ]

        return dependencies

    def sizeof(self, source_path: str, dependencies: list = None) -> int:
        """Calculate size of dataset and its dependencies.

        Args:
            source_path (str): path to the dataset
            dependencies (list, optional): list of dataset's dependencies. Defaults to None.

        Returns:
            int: size in octets
        """
        if path.isfile(source_path):
            dependencies.append(source_path)
            total_size = sum([path.getsize(f) for f in dependencies])
            dependencies.pop(-1)
        elif path.isdir(source_path):
            # sum files size
            total_size = 0
            for chemins in walk(path.realpath(source_path)):
                for file in chemins[2]:
                    chem_complete = path.join(chemins[0], file)
                    if path.isfile(chem_complete):
                        total_size = total_size + path.getsize(chem_complete)
                    else:
                        pass
        else:
            return None

        return total_size

    def erratum(
        self,
        target_container: Union[dict, MetaDataset],
        src_path: Optional[str] = None,
        src_dataset_layer: Optional[ogr.Layer] = None,
        err_type: int = 1,
        err_msg: str = "",
    ):
        """Handle errors message and store it into __dict__.

        mess_type allowed values:
          1: impossible to read dataset (corruption, format...)
          2: dataset no contains any feature object
          3: no SRS
        """
        if self.ds_type == "flat":
            # local variables
            target_container["name"] = path.basename(src_path)
            target_container["folder"] = path.dirname(src_path)
            target_container["error"] = err_msg
            # method end
            return target_container
        elif self.ds_type == "postgis":
            if isinstance(src_dataset_layer, ogr.Layer):
                target_container.name = src_dataset_layer.GetName()
            else:
                target_container.name = "No OGR layer."
            target_container.processing_error_type = err_type
            target_container.processing_error_msg = err_msg
            # method end
            return target_container
        else:
            pass
