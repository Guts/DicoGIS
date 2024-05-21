#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from os import path
from pathlib import Path
from typing import Optional, Union

# 3rd party
from osgeo import ogr

# project
from dicogis.models.dataset import MetaDataset
from dicogis.utils.check_path import check_var_can_be_path

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class GeoreadersUtils:
    """TO DOC"""

    def __init__(self, ds_type="flat"):
        """Instanciate Utils class."""
        self.ds_type = ds_type

    def list_dependencies(
        self,
        main_file_path: Union[Path, str],
    ) -> list[Path]:
        """List dependant files around a main file."""
        if isinstance(main_file_path, str):
            check_var_can_be_path(input_var=main_file_path, raise_error=True)
            main_file_path = Path(main_file_path)

        file_dependencies: list[Path] = []
        for f in main_file_path.parent.iterdir():
            if not f.is_file():
                continue
            if f.stem == main_file_path.stem and f.suffix != main_file_path.suffix:
                file_dependencies.append(f)

        return file_dependencies

    def sizeof(
        self, source_path: Union[Path, str], dependencies: Optional[list[Path]] = None
    ) -> int:
        """Calculate size of dataset and its dependencies.

        Args:
            source_path (str): path to the dataset or a folder.
            dependencies (list, optional): list of dataset's dependencies.
                Defaults to None.

        Returns:
            int: size in octets
        """
        if isinstance(source_path, str):
            check_var_can_be_path(input_var=source_path, raise_error=True)
            source_path = Path(source_path)

        if dependencies is None:
            dependencies = list

        if source_path.is_file():
            dependencies.append(source_path)
            total_size = sum(f.stat().st_size for f in dependencies)
        elif source_path.is_dir():
            total_size = sum(
                f.stat().st_size for f in source_path.rglob("*") if f.is_file()
            )
        else:
            total_size = 0

        return total_size

    def erratum(
        self,
        target_container: Union[dict, MetaDataset],
        src_path: Optional[str] = None,
        src_dataset_layer: Optional[ogr.Layer] = None,
        err_type: int = 1,
        err_msg: str = "",
    ):
        """Store error messages in container object.

        Args:
            target_container (Union[dict, MetaDataset]): object where to store error message and type
            src_path (Optional[str], optional): source path. Defaults to None.
            src_dataset_layer (Optional[ogr.Layer], optional): source dataset layer. Defaults to None.
            err_type (int, optional): _description_. Defaults to 1.
            err_msg (str, optional): _description_. Defaults to "".
        """
        if self.ds_type == "flat":
            # local variables
            target_container.name = path.basename(src_path)
            target_container.parent_folder_name = path.dirname(src_path)
            target_container.processing_error_type = err_type
            target_container.processing_error_msg = err_msg
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
