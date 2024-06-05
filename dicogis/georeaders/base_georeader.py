#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from locale import getlocale
from os import path
from pathlib import Path
from typing import Literal, Optional, Union

# 3rd party libraries
from osgeo import gdal, ogr, osr

# project
from dicogis.constants import GDAL_POSTGIS_OPEN_OPTIONS
from dicogis.georeaders.gdal_exceptions_handler import GdalErrorHandler
from dicogis.models.feature_attributes import AttributeField
from dicogis.models.metadataset import MetaDataset
from dicogis.utils.check_path import check_var_can_be_path
from dicogis.utils.texts import TextsManager

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class GeoReaderBase:
    """Base class for geographic dataset readers."""

    def __init__(
        self,
        dataset_type: Literal[
            "flat_cad",
            "flat_database",
            "flat_database_esri",
            "flat_raster",
            "flat_vector",
            "sgbd_postgis",
        ],
        localized_strings: Optional[dict] = None,
    ) -> None:
        """Initialization.

        Args:
            dataset_type: type of dataset to read
            localized_strings: translated strings
        """
        # store args as attributes
        self.dataset_type = dataset_type

        # i18n
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts(
                language_code=getlocale()
            )
        # attributes to be used later
        self.counter_alerts: int = 0

        # GDAL customization and error handling
        gdal.AllRegister()
        self.gdal_err = GdalErrorHandler()
        errhandler = self.gdal_err.handler
        gdal.PushErrorHandler(errhandler)
        gdal.UseExceptions()
        ogr.UseExceptions()

    def calc_size_full_dataset(
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
            dependencies = []

        if source_path.is_file():
            total_size = (
                sum(f.stat().st_size for f in dependencies) + source_path.stat().st_size
            )
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
        if self.dataset_type == "flat":
            # local variables
            target_container.name = path.basename(src_path)
            target_container.parent_folder_name = path.dirname(src_path)
            target_container.processing_error_type = err_type
            target_container.processing_error_msg = err_msg
            # method end
            return target_container
        elif self.dataset_type == "postgis":
            if isinstance(src_dataset_layer, ogr.Layer):
                target_container.name = src_dataset_layer.GetName()
            else:
                target_container.name = "No OGR layer."
            target_container.processing_error_type = err_type
            target_container.processing_error_msg = err_msg
            # method end
            return target_container

    def get_extent_as_tuple(
        self, dataset_or_layer: Union[ogr.Layer, gdal.Dataset]
    ) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Get spatial extent (bounding box)."""
        if hasattr(dataset_or_layer, "GetExtent"):
            return (
                round(dataset_or_layer.GetExtent()[0], 2),
                round(dataset_or_layer.GetExtent()[1], 2),
                round(dataset_or_layer.GetExtent()[2], 2),
                round(dataset_or_layer.GetExtent()[3], 2),
            )
        elif hasattr(dataset_or_layer, "GetGeoTransform"):
            """
            Returns the minimum and maximum coordinate values in the sequence expected
            by, e.g., the `-te` switch in various GDAL utiltiies:
            (xmin, ymin, xmax, ymax).
            """
            gt = dataset_or_layer.GetGeoTransform()
            xsize = dataset_or_layer.RasterXSize  # Size in the x-direction
            ysize = dataset_or_layer.RasterYSize  # Size in the y-direction
            xr = abs(gt[1])  # Resolution in the x-direction
            yr = abs(gt[-1])  # Resolution in the y-direction
            return (gt[0], gt[3] - (ysize * yr), gt[0] + (xsize * xr), gt[3])
        else:
            return (None, None, None, None)

    def get_fields_details(
        self, ogr_layer_definition: ogr.FeatureDefn
    ) -> tuple[AttributeField]:
        """Get feature attributes from layer definition."""
        li_feature_attributes: list[AttributeField] = []
        for i in range(ogr_layer_definition.GetFieldCount()):
            field = ogr_layer_definition.GetFieldDefn(i)  # fields ordered
            li_feature_attributes.append(
                AttributeField(
                    name=field.GetName(),
                    data_type=field.GetTypeName(),
                    length=field.GetWidth(),
                    precision=field.GetPrecision(),
                )
            )

        # end of function
        return tuple(li_feature_attributes)

    def get_geometry_type(self, layer: ogr.Layer) -> str | None:
        """Get geometry type for a given ogr layer.

        Args:
            layer: OGR layer

        Returns:
            geometry type or None
        """
        geometry_type: str | None = None
        try:
            geometry_type = ogr.GeometryTypeToName(layer.GetGeomType())
        except Exception as err:
            logger.info(
                f"Unable to determine geometry type using 'ogr.GeometryTypeToName' on "
                f"'layer.GetGeomType()'. Trace: {err}"
            )

        if (
            geometry_type is not None
            and isinstance(geometry_type, str)
            and "unknown" not in geometry_type.lower()
        ):
            return geometry_type

        try:
            first_feature_object: ogr.Feature = layer.GetNextFeature()
        except AttributeError as err:
            logger.error(
                f"Impossible to get next feature on layer {layer.GetName()}. "
                f"Trace: {err}"
            )
            return None

        if not hasattr(first_feature_object, "GetGeometryRef"):
            logger.warning(
                "Unable to determine GeoMetryRef for object "
                f"{first_feature_object.GetFID()} in {layer.GetName()}."
            )
            return None

        layer_geometry_ref = first_feature_object.GetGeometryRef()
        if hasattr(layer_geometry_ref, "GetGeometryName"):
            return layer_geometry_ref.GetGeometryName()

        return None

    def get_srs_details(
        self, dataset_or_layer: Union[ogr.Layer, gdal.Dataset]
    ) -> tuple[str, str, str, str]:
        """Get coordinates system name, type and registry code.

        Args:
            dataset_or_layer (Union[ogr.Layer, gdal.Dataset]): input dataset or OGR
                layer

        Returns:
            crs_name, crs_registry, crs_code, crs_type
        """
        layer_spatial_ref: osr.SpatialReference | None = None
        srs_code: str | None = None
        srs_name: str | None = None
        srs_registry: str | None = None
        srs_type: str | None = None

        try:
            layer_spatial_ref: osr.SpatialReference = dataset_or_layer.GetSpatialRef()
        except Exception as err:
            logger.error(
                "Error occurred getting spatial reference for "
                f"'{dataset_or_layer.GetName()}'. Trace: {err}"
            )
        if not layer_spatial_ref:
            return (
                "srs_undefined",
                "srs_undefined",
                "srs_no_epsg",
                "srs_nr",
            )

        layer_spatial_ref.AutoIdentifyEPSG()
        srs_code = layer_spatial_ref.GetAuthorityCode(None)
        if not srs_code:
            if layer_spatial_ref.GetAttrValue("AUTHORITY", 1):
                srs_code = layer_spatial_ref.GetAttrValue("AUTHORITY", 1)
            else:
                srs_code = "srs_no_epsg"

        srs_registry = layer_spatial_ref.GetAuthorityName(None)

        # srs type
        srs_type = self.get_srs_type(object_spatial_reference=layer_spatial_ref)

        # handling exceptions in srs names'encoding
        srs_name = self.get_srs_name(object_spatial_reference=layer_spatial_ref)

        return (srs_name, srs_registry, srs_code, srs_type)

    def get_srs_name(self, object_spatial_reference: osr.SpatialReference) -> str:
        """Get SRS name from an osr object.

        Args:
            object_spatial_reference: osr object. Typically obtained with
                ogr.Layer.GetSpatialReference()

        Returns:
            name of spatial reference
        """

        if object_spatial_reference.GetName() is not None:
            srs_name = object_spatial_reference.GetName()
        elif (
            object_spatial_reference.IsGeographic()
            and object_spatial_reference.GetAttrValue("GEOGCS")
        ):
            srs_name = object_spatial_reference.GetAttrValue("GEOGCS").replace("_", " ")
        elif (
            object_spatial_reference.IsProjected()
            and object_spatial_reference.GetAttrValue("PROJCS")
        ):
            srs_name = object_spatial_reference.GetAttrValue("PROJCS").replace("_", " ")
        else:
            srs_name = object_spatial_reference.GetAttrValue("PROJECTION").replace(
                "_", " "
            )

        return srs_name

    def get_srs_type(self, object_spatial_reference: osr.SpatialReference) -> str:
        """Get SRS type from an osr object.

        Args:
            object_spatial_reference: osr object. Typically obtained with
                ogr.Layer.GetSpatialReference()

        Returns:
            type of spatial reference
        """
        srs_type = "srs_nr"
        # srs type
        srs_types_matrix = (
            (object_spatial_reference.IsDynamic(), "srs_dyna"),
            (object_spatial_reference.IsCompound(), "srs_comp"),
            (object_spatial_reference.IsDerivedGeographic(), "srs_derg"),
            (object_spatial_reference.IsGeocentric(), "srs_geoc"),
            (object_spatial_reference.IsGeographic(), "srs_geog"),
            (object_spatial_reference.IsLocal(), "srs_loca"),
            (object_spatial_reference.IsProjected(), "srs_proj"),
            (object_spatial_reference.IsVertical(), "srs_vert"),
        )
        # searching for a match with one of srs types
        for srs_type_check in srs_types_matrix:
            if srs_type_check[0] == 1:
                srs_type = srs_type_check[1]
                break

        return srs_type

    def list_dependencies(
        self,
        main_dataset: Union[Path, str, gdal.Dataset],
    ) -> list[Path]:
        """List dependant files around a main file.

        Args:
            main_dataset: gdal.Dataset or ogr.Layer or path to the source dataset

        Returns:
            list of file paths related to the main dataset
        """
        if isinstance(main_dataset, str):
            check_var_can_be_path(input_var=main_dataset, raise_error=True)
            main_dataset = Path(main_dataset)

        file_dependencies: list[Path] = []

        if isinstance(main_dataset, Path):
            for f in main_dataset.parent.iterdir():
                if not f.is_file():
                    continue
                if f.stem == main_dataset.stem and f != main_dataset:
                    file_dependencies.append(f)
        elif isinstance(main_dataset, gdal.Dataset):
            file_dependencies = [
                Path(filepath) for filepath in main_dataset.GetFileList()
            ]
            # GetFileList includes the main dataset file in first position
            if len(file_dependencies):
                file_dependencies.pop(0)

        return file_dependencies

    def open_dataset_with_gdal(self, source_dataset: Union[Path, str]) -> gdal.Dataset:
        """Open dataset with GDAL (OGR).

        Args:
            source_dataset (Union[Path, str]): path or connection string to the dataset

        Returns:
            gdal.Dataset: opened dataset
        """
        if isinstance(source_dataset, Path):
            source_dataset = str(source_dataset.resolve())

        # customize GDAL flags
        gdal_flags = gdal.OF_READONLY | gdal.OF_VERBOSE_ERROR
        if self.dataset_type in (
            "flat_cad",
            "flat_database_esri",
            "flat_vector",
            "sgbd_postgis",
        ):
            gdal_flags += gdal.OF_VECTOR
        elif self.dataset_type in ("flat_raster",):
            gdal_flags += gdal.OF_RASTER

        # customize GDAL open options
        gdal_open_options = []
        if self.dataset_type == "sgbd_postgis":
            gdal_open_options.extend(GDAL_POSTGIS_OPEN_OPTIONS)
            if self.views_included:
                gdal_open_options.append("SKIP_VIEWS=NO")
                logger.info("PostgreSQL views enabled.")
            else:
                gdal_open_options.append("SKIP_VIEWS=YES")
                logger.info("PostgreSQL views disabled.")

        # open it
        dataset: gdal.Dataset = gdal.OpenEx(
            source_dataset, gdal_flags, gdal_open_options
        )
        logger.debug(
            f"Opening '{source_dataset}' with GDAL "
            f"{dataset.GetDriver().LongName} succeeded."
        )
        return dataset
