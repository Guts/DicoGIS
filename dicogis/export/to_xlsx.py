#! python3  # noqa: E265

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from functools import lru_cache
from os import path
from pathlib import Path
from typing import Union

# 3rd party library
from openpyxl import Workbook
from openpyxl.styles import Alignment, NamedStyle
from openpyxl.utils import get_column_letter

# project
from dicogis.models.dataset import (
    MetaDatabaseTable,
    MetaDataset,
    MetaRasterDataset,
    MetaVectorDataset,
)
from dicogis.utils.formatters import convert_octets

# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Functions #############
# ##################################


def secure_encoding(layer_dict: dict, key_str: str) -> str:
    """Check if dictionary value is compatible with XML encoding.

    Args:
        layer_dict (dict): layer metadata dictionary
        key_str (str): key fo dictionary to check

    Returns:
        str: clean string
    """
    try:
        out_str = layer_dict.get(key_str, "").encode("utf-8", "strict")
        return out_str
    except UnicodeError as err:
        err_msg = "Encoding error spotted in '{}' for layer {}".format(
            key_str, layer_dict.get("name")
        )
        logger.warning(
            "{}. Layer: {}. Trace: {}".format(err_msg, layer_dict.get("name"), err)
        )
        return layer_dict.get(key_str, "").encode("utf8", "xmlcharrefreplace")


# ##############################################################################
# ########## Classes ###############
# ##################################


class MetadataToXlsx(Workbook):
    """Export into a XLSX worksheet."""

    li_cols_vector = [
        "nomfic",
        "path",
        "theme",
        "num_attrib",
        "num_objets",
        "geometrie",
        "srs",
        "srs_type",
        "codepsg",
        "emprise",
        "date_crea",
        "date_actu",
        "format",
        "li_depends",
        "tot_size",
        "li_chps",
        "gdal_warn",
    ]

    li_cols_raster = [
        "nomfic",
        "path",
        "theme",
        "size_Y",
        "size_X",
        "pixel_w",
        "pixel_h",
        "origin_x",
        "origin_y",
        "srs_type",
        "codepsg",
        "emprise",
        "date_crea",
        "date_actu",
        "num_bands",
        "format",
        "compression",
        "coloref",
        "li_depends",
        "tot_size",
        "gdal_warn",
    ]

    li_cols_filedb = [
        "nomfic",
        "path",
        "theme",
        "tot_size",
        "date_crea",
        "date_actu",
        "feats_class",
        "num_attrib",
        "num_objets",
        "geometrie",
        "srs",
        "srs_type",
        "codepsg",
        "emprise",
        "li_chps",
    ]

    li_cols_mapdocs = [
        "nomfic",
        "path",
        "theme",
        "custom_title",
        "creator_prod",
        "keywords",
        "subject",
        "res_image",
        "tot_size",
        "date_crea",
        "date_actu",
        "origin_x",
        "origin_y",
        "srs",
        "srs_type",
        "codepsg",
        "sub_layers",
        "num_attrib",
        "num_objets",
        "li_chps",
    ]

    li_cols_caodao = [
        "nomfic",
        "path",
        "theme",
        "tot_size",
        "date_crea",
        "date_actu",
        "sub_layers",
        "num_attrib",
        "num_objets",
        "geometrie",
        "srs",
        "srs_type",
        "codepsg",
        "emprise",
        "li_chps",
    ]

    li_cols_sgbd = [
        "nomfic",
        "conn_chain",
        "schema",
        "num_attrib",
        "num_objets",
        "geometrie",
        "srs",
        "srs_type",
        "codepsg",
        "emprise",
        "format",
        "li_chps",
        "gdal_err",
    ]

    def __init__(self, translated_texts: dict, opt_size_prettify: bool = True):
        """Store metadata into Excel worksheets.

        Args:
            texts (dict, optional): dictionary of translated texts. Defaults to {}.
            opt_size_prettify (bool, optional): option to prettify size or not. Defaults to False.
        """
        super().__init__(iso_dates=True)
        self.translated_texts = translated_texts

        # options
        self.opt_size_prettify = opt_size_prettify

        # styles
        s_date = NamedStyle(name="date")
        s_date.number_format = "dd/mm/yyyy"
        s_wrap = NamedStyle(name="wrap")
        s_wrap.alignment = Alignment(wrap_text=True)
        self.add_named_style(s_date)
        self.add_named_style(s_wrap)

        # deleting the default worksheet
        ws = self.active
        self.remove(worksheet=ws)

    # ------------ Setting workbook ---------------------

    def set_worksheets(
        self,
        has_vector: bool = False,
        has_raster: bool = False,
        has_filedb: bool = False,
        has_mapdocs: bool = False,
        has_cad: bool = False,
        has_sgbd: bool = False,
    ):
        """Add news sheets depending on present metadata types."""
        # SHEETS & HEADERS
        if (
            has_vector
            and self.translated_texts.get("sheet_vectors") not in self.sheetnames
        ):
            self.ws_v = self.create_sheet(
                title=self.translated_texts.get("sheet_vectors")
            )
            # headers
            self.ws_v.append(
                [self.translated_texts.get(i) for i in self.li_cols_vector]
            )
            # styling
            for i in self.li_cols_vector:
                self.ws_v.cell(row=1, column=self.li_cols_vector.index(i) + 1).style = (
                    "Headline 2"
                )

            # initialize line counter
            self.idx_v = 1
        else:
            pass

        if (
            has_raster
            and self.translated_texts.get("sheet_rasters") not in self.sheetnames
        ):
            self.ws_r = self.create_sheet(
                title=self.translated_texts.get("sheet_rasters")
            )
            # headers
            self.ws_r.append(
                [self.translated_texts.get(i) for i in self.li_cols_raster]
            )
            # styling
            for i in self.li_cols_raster:
                self.ws_r.cell(row=1, column=self.li_cols_raster.index(i) + 1).style = (
                    "Headline 2"
                )

            # initialize line counter
            self.idx_r = 1
        else:
            pass

        if (
            has_filedb
            and self.translated_texts.get("sheet_filedb") not in self.sheetnames
        ):
            self.ws_fdb = self.create_sheet(
                title=self.translated_texts.get("sheet_filedb")
            )
            # headers
            self.ws_fdb.append(
                [self.translated_texts.get(i) for i in self.li_cols_filedb]
            )
            # styling
            for i in self.li_cols_filedb:
                self.ws_fdb.cell(
                    row=1, column=self.li_cols_filedb.index(i) + 1
                ).style = "Headline 2"

            # initialize line counter
            self.idx_f = 1
        else:
            pass

        if (
            has_mapdocs
            and self.translated_texts.get("sheet_maplans") not in self.sheetnames
        ):
            self.ws_mdocs = self.create_sheet(
                title=self.translated_texts.get("sheet_maplans")
            )
            # headers
            self.ws_mdocs.append(
                [self.translated_texts.get(i) for i in self.li_cols_mapdocs]
            )
            # styling
            for i in self.li_cols_mapdocs:
                self.ws_mdocs.cell(
                    row=1, column=self.li_cols_mapdocs.index(i) + 1
                ).style = "Headline 2"

            # initialize line counter
            self.idx_m = 1
        else:
            pass

        if has_cad and self.translated_texts.get("sheet_cdao") not in self.sheetnames:
            self.ws_cad = self.create_sheet(
                title=self.translated_texts.get("sheet_cdao")
            )
            # headers
            self.ws_cad.append(
                [self.translated_texts.get(i) for i in self.li_cols_caodao]
            )
            # styling
            for i in self.li_cols_caodao:
                self.ws_cad.cell(
                    row=1, column=self.li_cols_caodao.index(i) + 1
                ).style = "Headline 2"

            # initialize line counter
            self.idx_c = 1
        else:
            pass

        if has_sgbd and "PostGIS" not in self.sheetnames:
            self.ws_sgbd = self.create_sheet(title="PostGIS")
            # headers
            self.ws_sgbd.append(
                [self.translated_texts.get(i) for i in self.li_cols_sgbd]
            )
            # styling
            for i in self.li_cols_sgbd:
                self.ws_sgbd.cell(
                    row=1, column=self.li_cols_sgbd.index(i) + 1
                ).style = "Headline 2"
            # initialize line counter
            self.idx_s = 1
        else:
            pass

        # end of method
        return

    def tunning_worksheets(self):
        """Clean up and tunning worksheet."""
        for sheet in self.worksheets:
            # Freezing panes
            c_freezed = sheet["B2"]
            sheet.freeze_panes = c_freezed

            # Print properties
            sheet.print_options.horizontalCentered = True
            sheet.print_options.verticalCentered = True
            sheet.page_setup.fitToWidth = 1
            sheet.page_setup.orientation = sheet.ORIENTATION_LANDSCAPE

            # Others properties
            wsprops = sheet.sheet_properties
            wsprops.filterMode = True

            # enable filters
            sheet.auto_filter.ref = "A1:{}{}".format(
                get_column_letter(sheet.max_column), sheet.max_row
            )
            # columns width
            sheet.column_dimensions["A"].bestFit = True
            # sheet.column_dimensions['A'].auto_size = True
            # sheet.column_dimensions['B'].auto_size = True

            # dims = {}
            # for row in sheet.rows:
            #     for cell in row:
            #         if cell.value:
            #             val = cell.value
            #             dims[cell.column] = max((dims.get(cell.column, 0), len(val)))
            # for col, value in dims.items():
            #     sheet.column_dimensions[col].width = value
        # end of method
        return

    @lru_cache(maxsize=128, typed=True)
    def format_as_hyperlink(self, target: Union[str, Path], label: str) -> str:
        """Format a cell hyperlink with a target and a label.

        Args:
            target (Union[str, Path]): link destination
            label (str): display text

        Returns:
            str: cell text formatted with hyperlink
        """
        if isinstance(target, Path):
            target = str(target.resolve())

        return f'=HYPERLINK("{target}", "{label}")'

    def format_feature_attributes(self, metadataset: MetaDataset) -> str:
        """Format vector feature attributes in an unique string.

        Args:
            metadataset (MetaDataset): metadataset

        Returns:
            str: concatenated string with feature attributes informations
        """
        out_attributes_str = ""

        for feature_attribute in metadataset.attribute_fields:
            # field type
            if "integer" in feature_attribute.data_type.lower():
                translated_feature_attribute_type = self.translated_texts.get("entier")
            elif feature_attribute.data_type.lower() == "real":
                translated_feature_attribute_type = self.translated_texts.get("reel")
            elif feature_attribute.data_type.lower() == "string":
                translated_feature_attribute_type = self.translated_texts.get("string")
            elif feature_attribute.data_type.lower() in ("date", "datetime"):
                translated_feature_attribute_type = self.translated_texts.get("date")
            else:
                translated_feature_attribute_type = feature_attribute.data_type
                logger.warning(
                    f"Layer: {metadataset.name} - {feature_attribute.name} has an "
                    f"unstranslated type: {feature_attribute.data_type}"
                )

            # concatenation of field informations
            out_attributes_str = "{} {} ({}{}{}{}{}); ".format(
                out_attributes_str,
                feature_attribute.name,
                translated_feature_attribute_type,
                self.translated_texts.get("longueur"),
                feature_attribute.length,
                self.translated_texts.get("precision"),
                feature_attribute.precision,
            )

        return out_attributes_str

    @lru_cache
    def format_size(self, in_size_in_octets: int = 0) -> str:
        """Format size in octets accordingly to the option.

        Args:
            in_size_in_octets (int): input size in octets

        Returns:
            str: formatted size in octets
        """
        if self.opt_size_prettify:
            return convert_octets(in_size_in_octets)
        else:
            return in_size_in_octets

    # ------------ Writing metadata ---------------------
    def store_md_vector(self, metadataset: MetaVectorDataset):
        """Store metadata about a vector dataset."""
        # increment line
        self.idx_v += 1
        # use a local alias to reduce confusion and facilitate copy/paste between methods
        row_index = self.idx_v

        # in case of a source error
        if metadataset.processing_succeeded is False:
            # sheet.row(line).set_style(self.xls_erreur)
            err_mess = self.translated_texts.get(metadataset.processing_error_type)
            logger.warning(
                "Problem detected: " "{} in {}".format(err_mess, metadataset.name)
            )
            self.ws_v[f"A{row_index}"] = metadataset.name
            self.ws_v[f"A{row_index}"].style = "Warning Text"
            self.ws_v[f"B{row_index}"] = self.format_as_hyperlink(
                target=metadataset.path.parent,
                label=self.translated_texts.get("browse"),
            )
            self.ws_v[f"B{row_index}"].style = "Warning Text"
            self.ws_v[f"C{row_index}"] = err_mess
            self.ws_v[f"C{row_index}"].style = "Warning Text"
            # gdal info
            self.ws_v[f"Q{row_index}"] = (
                f"{metadataset.processing_error_type}: "
                f"{metadataset.processing_error_msg}"
            )
            self.ws_v[f"Q{row_index}"].style = "Warning Text"
            # Interruption of function
            return False
        else:
            pass

        # Name
        self.ws_v[f"A{row_index}"] = metadataset.name

        # Path of parent folder formatted to be a hyperlink
        self.ws_v[f"B{row_index}"] = self.format_as_hyperlink(
            target=metadataset.path.parent, label=self.translated_texts.get("browse")
        )
        self.ws_v[f"B{row_index}"].style = "Hyperlink"

        # Name of parent folder with an exception if this is the format name
        self.ws_v[f"C{row_index}"] = metadataset.parent_folder_name

        # Fields count
        self.ws_v[f"D{row_index}"] = metadataset.attribute_fields_count
        # Objects count
        self.ws_v[f"E{row_index}"] = metadataset.features_count
        # Geometry type
        self.ws_v[f"F{row_index}"] = metadataset.geometry_type

        # Name of srs
        self.ws_v[f"G{row_index}"] = metadataset.crs_name

        # Type of SRS
        self.ws_v[f"H{row_index}"] = metadataset.crs_type
        # EPSG code
        self.ws_v[f"I{row_index}"] = metadataset.crs_registry_code
        # Spatial extent
        self.ws_v[f"J{row_index}"].style = "wrap"
        self.ws_v[f"J{row_index}"] = ", ".join(str(coord) for coord in metadataset.bbox)

        # Creation date
        self.ws_v[f"K{row_index}"] = metadataset.storage_date_created
        # Last update date
        self.ws_v[f"L{row_index}"] = metadataset.storage_date_updated
        # Format of data
        self.ws_v[f"M{row_index}"] = metadataset.format_gdal_long_name
        # dependencies
        self.ws_v[f"N{row_index}"].style = "wrap"
        self.ws_v[f"N{row_index}"] = " |\n ".join(
            str(f.resolve()) for f in metadataset.files_dependencies
        )
        # total size
        self.ws_v[f"O{row_index}"] = self.format_size(
            in_size_in_octets=metadataset.storage_size
        )

        # Field informations
        self.ws_v[f"P{row_index}"] = self.format_feature_attributes(
            metadataset=metadataset
        )

        # end of method
        return

    def store_md_raster(self, metadataset: MetaRasterDataset):
        """Store metadata about a raster dataset."""
        # increment line
        self.idx_r += 1
        # use a local alias to reduce confusion and facilitate copy/paste between methods
        row_index = self.idx_r

        # in case of a source error
        if "error" in metadataset:
            # sheet.row(line).set_style(self.xls_erreur)
            err_mess = self.translated_texts.get(metadataset.get("error"))
            logger.warning(
                "Problem detected: "
                "{} in {}".format(err_mess, metadataset.get("name"))
            )
            self.ws_r[f"A{row_index}"] = metadataset.get("name")
            link = r'=HYPERLINK("{}","{}")'.format(
                metadataset.get("folder"), self.translated_texts.get("browse")
            )
            self.ws_r[f"B{row_index}"] = link
            self.ws_r[f"B{row_index}"].style = "Warning Text"
            self.ws_r[f"C{row_index}"] = err_mess
            self.ws_r[f"C{row_index}"].style = "Warning Text"
            # Interruption of function
            return False
        else:
            pass

        # Name
        self.ws_r[f"A{row_index}"] = metadataset.name

        # Path of parent folder formatted to be a hyperlink
        self.ws_v[f"B{row_index}"] = self.format_as_hyperlink(
            target=metadataset.path.parent, label=self.translated_texts.get("browse")
        )
        self.ws_v[f"B{row_index}"].style = "Hyperlink"

        # Name of parent folder with an exception if this is the format name
        self.ws_r[f"C{row_index}"] = metadataset.parent_folder_name

        # Image dimensions
        self.ws_r[f"D{row_index}"] = metadataset.rows_count
        self.ws_r[f"E{row_index}"] = metadataset.columns_count

        # Pixel dimensions
        self.ws_r[f"F{row_index}"] = metadataset.pixel_width
        self.ws_r[f"G{row_index}"] = metadataset.pixel_height

        # Image dimensions
        self.ws_r[f"H{row_index}"] = metadataset.origin_x
        self.ws_r[f"I{row_index}"] = metadataset.origin_y

        # Type of SRS
        self.ws_r[f"J{row_index}"] = metadataset.crs_type
        # EPSG code
        self.ws_r[f"K{row_index}"] = metadataset.crs_registry_code

        # Creation date
        self.ws_r[f"M{row_index}"] = metadataset.storage_date_created
        # Last update date
        self.ws_r[f"N{row_index}"] = metadataset.storage_date_updated

        # Number of bands
        self.ws_r[f"O{row_index}"] = metadataset.bands_count

        # Format of data
        self.ws_r[f"P{row_index}"] = metadataset.format_gdal_long_name
        # Compression rate
        self.ws_r[f"Q{row_index}"] = metadataset.compression_rate

        # Color referential
        self.ws_r[f"R{row_index}"] = metadataset.color_space

        # Dependencies
        self.ws_r[f"S{row_index}"].style = "wrap"
        self.ws_r[f"S{row_index}"] = " |\n ".join(
            f.resolve() for f in metadataset.files_dependencies
        )

        # total size of file and its dependencies
        self.ws_r[f"O{row_index}"] = self.format_size(
            in_size_in_octets=metadataset.storage_size
        )

        # end of method
        return

    def store_md_fdb(self, filedb):
        """Storing metadata about a file database."""
        # increment line
        self.idx_f += 1

        # in case of a source error
        if "error" in filedb:
            # sheet.row(line).set_style(self.xls_erreur)
            err_mess = self.translated_texts.get(filedb.get("error"))
            logger.warning(
                "Problem detected: " "{} in {}".format(err_mess, filedb.get("name"))
            )
            self.ws_fdb[f"A{self.idx_f}"] = filedb.get("name")
            link = r'=HYPERLINK("{}","{}")'.format(
                filedb.get("folder"), self.translated_texts.get("browse")
            )
            self.ws_fdb[f"B{self.idx_f}"] = link
            self.ws_fdb[f"B{self.idx_f}"].style = "Warning Text"
            self.ws_fdb[f"C{self.idx_f}"] = err_mess
            self.ws_fdb[f"C{self.idx_f}"].style = "Warning Text"
            # gdal info
            if "err_gdal" in filedb:
                logger.warning(
                    "Problem detected by GDAL: "
                    "{} in {}".format(err_mess, filedb.get("name"))
                )
                self.ws_fdb[f"Q{self.idx_v}"] = "{} : {}".format(
                    filedb.get("err_gdal")[0], filedb.get("err_gdal")[1]
                )
                self.ws_fdb[f"Q{self.idx_v}"].style = "Warning Text"
            else:
                pass
            # Interruption of function
            return False
        else:
            pass

        # Name
        self.ws_fdb[f"A{self.idx_f}"] = filedb.get("name")

        # Path of parent folder formatted to be a hyperlink
        link = r'=HYPERLINK("{}","{}")'.format(
            filedb.get("folder"), self.translated_texts.get("browse")
        )
        self.ws_fdb[f"B{self.idx_f}"] = link
        self.ws_fdb[f"B{self.idx_f}"].style = "Hyperlink"

        self.ws_fdb[f"C{self.idx_f}"] = path.basename(filedb.get("folder"))
        self.ws_fdb[f"D{self.idx_f}"] = filedb.get("total_size")
        self.ws_fdb[f"E{self.idx_f}"] = filedb.get("date_crea")
        self.ws_fdb[f"F{self.idx_f}"] = filedb.get("date_actu")
        self.ws_fdb[f"G{self.idx_f}"] = filedb.get("layers_count")
        self.ws_fdb[f"H{self.idx_f}"] = filedb.get("total_fields")
        self.ws_fdb[f"I{self.idx_f}"] = filedb.get("total_objs")

        # parsing layers
        for layer_idx, layer_name in zip(
            filedb.get("layers_idx"), filedb.get("layers_names")
        ):
            # increment line
            self.idx_f += 1
            champs = ""
            # get the layer informations
            try:
                gdb_layer = filedb.get(f"{layer_idx}_{layer_name}")
            except UnicodeError as err:
                logger.error(f"Encoding error. Trace: {err}")
                continue
            # in case of a source error
            if gdb_layer.get("error"):
                err_mess = self.translated_texts.get(gdb_layer.get("error"))
                logger.warning(
                    "Problem detected: {} in {}".format(
                        err_mess, gdb_layer.get("title")
                    )
                )
                self.ws_fdb[f"G{self.idx_f}"] = gdb_layer.get("title")
                self.ws_fdb[f"G{self.idx_f}"].style = "Warning Text"
                self.ws_fdb[f"H{self.idx_f}"] = err_mess
                self.ws_fdb[f"H{self.idx_f}"].style = "Warning Text"
                # Interruption of function
                continue
            else:
                pass

            self.ws_fdb[f"G{self.idx_f}"] = gdb_layer.get("title")
            self.ws_fdb[f"H{self.idx_f}"] = gdb_layer.get("num_fields")
            self.ws_fdb[f"I{self.idx_f}"] = gdb_layer.get("num_obj")
            self.ws_fdb[f"J{self.idx_f}"] = gdb_layer.get("type_geom")
            self.ws_fdb[f"K{self.idx_f}"] = secure_encoding(gdb_layer, "srs")
            self.ws_fdb[f"L{self.idx_f}"] = gdb_layer.get("srs_type")
            self.ws_fdb[f"M{self.idx_f}"] = gdb_layer.get("epsg")

            # Spatial extent
            emprise = "Xmin : {} - Xmax : {} | \nYmin : {} - Ymax : {}".format(
                gdb_layer.get("xmin"),
                gdb_layer.get("xmax"),
                gdb_layer.get("ymin"),
                gdb_layer.get("ymax"),
            )
            self.ws_fdb[f"N{self.idx_f}"].style = "wrap"
            self.ws_fdb[f"N{self.idx_f}"] = emprise

            # Field informations
            fields = gdb_layer.get("fields")
            for chp in fields.keys():
                # field type
                if "Integer" in fields[chp][0]:
                    tipo = self.translated_texts.get("entier")
                elif fields[chp][0] == "Real":
                    tipo = self.translated_texts.get("reel")
                elif fields[chp][0] == "String":
                    tipo = self.translated_texts.get("string")
                elif fields[chp][0] == "Date":
                    tipo = self.translated_texts.get("date")
                else:
                    tipo = "unknown"
                    logger.warning(chp + " unknown type")

                # concatenation of field informations
                try:
                    champs = "{} {} ({}{}{}{}{}) ; ".format(
                        champs,
                        chp.encode("utf8", "replace"),
                        tipo,
                        self.translated_texts.get("longueur"),
                        fields[chp][1],
                        self.translated_texts.get("precision"),
                        fields[chp][2],
                    )
                except UnicodeDecodeError:
                    logger.warning(f"Field name with special letters: {chp}")
                    continue

            # Once all fieds explored, write them
            self.ws_fdb[f"O{self.idx_f}"] = champs

        # end of method
        return

    def store_md_mapdoc(self, mapdoc):
        """To store mapdocs information from DicoGIS."""
        # increment line
        self.idx_m += 1

        # local variables
        champs = ""

        # in case of a source error
        if "error" in mapdoc:
            # sheet.row(line).set_style(self.xls_erreur)
            err_mess = self.translated_texts.get(mapdoc.get("error"))
            logger.warning(
                "Problem detected: " "{} in {}".format(err_mess, mapdoc.get("name"))
            )
            self.ws_mdocs[f"A{self.idx_m}"] = mapdoc.get("name")
            self.ws_mdocs[f"A{self.idx_m}"].style = "Warning Text"
            link = r'=HYPERLINK("{}","{}")'.format(
                mapdoc.get("folder"), self.translated_texts.get("browse")
            )
            self.ws_mdocs[f"B{self.idx_m}"] = link
            self.ws_mdocs[f"B{self.idx_m}"].style = "Warning Text"
            self.ws_mdocs[f"C{self.idx_m}"] = err_mess
            self.ws_mdocs[f"C{self.idx_m}"].style = "Warning Text"
            # Interruption of function
            return False
        else:
            pass

        # Name
        self.ws_mdocs[f"A{self.idx_m}"] = mapdoc.get("name")

        # Path of parent folder formatted to be a hyperlink
        link = r'=HYPERLINK("{}","{}")'.format(
            mapdoc.get("folder"), self.translated_texts.get("browse")
        )
        self.ws_mdocs[f"B{self.idx_m}"] = link
        self.ws_mdocs[f"B{self.idx_m}"].style = "Hyperlink"
        self.ws_mdocs[f"C{self.idx_m}"] = path.dirname(mapdoc.get("folder"))
        self.ws_mdocs[f"D{self.idx_m}"] = mapdoc.get("title")
        self.ws_mdocs[f"E{self.idx_m}"] = mapdoc.get("creator_prod")
        self.ws_mdocs[f"F{self.idx_m}"] = mapdoc.get("keywords")
        self.ws_mdocs[f"G{self.idx_m}"] = mapdoc.get("subject")
        self.ws_mdocs[f"H{self.idx_m}"] = mapdoc.get("dpi")
        self.ws_mdocs[f"I{self.idx_m}"] = mapdoc.get("total_size")
        self.ws_mdocs[f"J{self.idx_m}"] = mapdoc.get("date_crea")
        self.ws_mdocs[f"K{self.idx_m}"] = mapdoc.get("date_actu")
        self.ws_mdocs[f"L{self.idx_m}"] = mapdoc.get("xOrigin")
        self.ws_mdocs[f"M{self.idx_m}"] = mapdoc.get("yOrigin")
        self.ws_mdocs[f"N{self.idx_m}"] = secure_encoding(mapdoc, "srs")
        self.ws_mdocs[f"O{self.idx_m}"] = mapdoc.get("srs_type")
        self.ws_mdocs[f"P{self.idx_m}"] = mapdoc.get("epsg")
        self.ws_mdocs[f"Q{self.idx_m}"] = mapdoc.get("layers_count")
        self.ws_mdocs[f"R{self.idx_m}"] = mapdoc.get("total_fields")
        self.ws_mdocs[f"S{self.idx_m}"] = mapdoc.get("total_objs")

        for layer_idx, layer_name in zip(
            mapdoc.get("layers_idx"), mapdoc.get("layers_names")
        ):
            # increment line
            self.idx_m += 1
            champs = ""

            # get the layer informations
            try:
                mdoc_layer = mapdoc.get(f"{layer_idx}_{layer_name}")
            except UnicodeDecodeError:
                mdoc_layer = mapdoc.get(
                    "{}_{}".format(layer_idx, layer_name.encode("utf8", "replace"))
                )
            # in case of a source error
            if mdoc_layer.get("error"):
                err_mess = self.translated_texts.get(mdoc_layer.get("error"))
                logger.warning(
                    "Problem detected: {} in {}".format(
                        err_mess, mdoc_layer.get("title")
                    )
                )
                self.ws_mdocs[f"Q{self.idx_f}"] = mdoc_layer.get("title")
                self.ws_mdocs[f"Q{self.idx_f}"].style = "Warning Text"
                self.ws_mdocs[f"R{self.idx_f}"] = err_mess
                self.ws_mdocs[f"R{self.idx_f}"].style = "Warning Text"
                # loop must go on
                continue
            else:
                pass
            # layer info
            self.ws_mdocs[f"Q{self.idx_m}"] = mdoc_layer.get("title")
            self.ws_mdocs[f"R{self.idx_m}"] = mdoc_layer.get("num_fields")
            self.ws_mdocs[f"S{self.idx_m}"] = mdoc_layer.get("num_objs")

            # Field informations
            fields = mdoc_layer.get("fields")
            for chp in fields.keys():
                # field type
                if "Integer" in fields[chp][0]:
                    tipo = self.translated_texts.get("entier")
                elif fields[chp][0] == "Real":
                    tipo = self.translated_texts.get("reel")
                elif fields[chp][0] == "String":
                    tipo = self.translated_texts.get("string")
                elif fields[chp][0] == "Date":
                    tipo = self.translated_texts.get("date")
                else:
                    tipo = "unknown"
                    logger.warning(chp + " unknown type")

                # concatenation of field informations
                try:
                    champs = "{} {} ({}{}{}{}{}) ; ".format(
                        champs,
                        chp.decode("utf8", "replace"),
                        tipo,
                        self.translated_texts.get("longueur"),
                        fields[chp][1],
                        self.translated_texts.get("precision"),
                        fields[chp][2],
                    )
                except UnicodeDecodeError:
                    logger.warning(
                        "Field name with special letters: {}".format(
                            chp.decode("latin1")
                        )
                    )
                    # decode the fucking field name
                    champs = (
                        champs
                        + chp.decode("latin1")
                        + " ({}, Lg. = {}, Pr. = {}) ;".format(
                            tipo, fields[chp][1], fields[chp][2]
                        )
                    )
                    # then continue
                    continue

            # Once all fieds explored, write them
            self.ws_fdb[f"T{self.idx_f}"] = champs

        # end of method
        return

    def store_md_cad(self, cad):
        """Store metadata about CAD dataset."""
        # increment line
        self.idx_c += 1

        # local variables
        champs = ""

        # in case of a source error
        if "error" in cad:
            # sheet.row(line).set_style(self.xls_erreur)
            err_mess = self.translated_texts.get(cad.get("error"))
            logger.warning(
                "Problem detected: {} in {}".format(err_mess, cad.get("name"))
            )
            self.ws_cad[f"A{self.idx_c}"] = cad.get("name")
            self.ws_cad[f"A{self.idx_c}"].style = "Warning Text"
            link = r'=HYPERLINK("{}","{}")'.format(
                cad.get("folder"), self.translated_texts.get("browse")
            )
            self.ws_cad[f"B{self.idx_c}"] = link
            self.ws_cad[f"B{self.idx_c}"].style = "Warning Text"
            self.ws_cad[f"C{self.idx_c}"] = err_mess
            self.ws_cad[f"C{self.idx_c}"].style = "Warning Text"
            # Interruption of function
            return False
        else:
            pass

        # Name
        self.ws_cad[f"A{self.idx_c}"] = cad.get("name")

        # Path of parent folder formatted to be a hyperlink
        link = r'=HYPERLINK("{}","{}")'.format(
            cad.get("folder"), self.translated_texts.get("browse")
        )
        self.ws_cad[f"B{self.idx_c}"] = link
        self.ws_cad[f"B{self.idx_c}"].style = "Hyperlink"

        # Name of parent folder with an exception if this is the format name
        self.ws_cad[f"C{self.idx_c}"] = path.basename(cad.get("folder"))
        # total size
        self.ws_cad[f"D{self.idx_c}"] = cad.get("total_size")
        # Creation date
        self.ws_cad[f"E{self.idx_c}"] = cad.get("date_crea")
        # Last update date
        self.ws_cad[f"F{self.idx_c}"] = cad.get("date_actu")
        self.ws_cad[f"G{self.idx_c}"] = cad.get("layers_count")
        self.ws_cad[f"H{self.idx_c}"] = cad.get("total_fields")
        self.ws_cad[f"I{self.idx_c}"] = cad.get("total_objs")

        # parsing layers
        for layer_idx, layer_name in zip(
            cad.get("layers_idx"), cad.get("layers_names")
        ):
            # increment line
            self.idx_c += 1
            champs = ""
            # get the layer informations
            try:
                layer = cad.get(f"{layer_idx}_{layer_name}")
            except UnicodeDecodeError:
                layer = cad.get("{}_{}".format(layer_idx, layer_name.decode("latin1")))
            # in case of a source error
            if layer.get("error"):
                err_mess = self.translated_texts.get(layer.get("error"))
                logger.warning(
                    "Problem detected: " "{} in {}".format(err_mess, layer.get("title"))
                )
                self.ws_cad[f"G{self.idx_c}"] = layer.get("title")
                self.ws_cad[f"G{self.idx_c}"].style = "Warning Text"
                self.ws_cad[f"H{self.idx_c}"] = err_mess
                self.ws_cad[f"H{self.idx_c}"].style = "Warning Text"
                # Interruption of function
                continue
            else:
                pass

            self.ws_cad[f"G{self.idx_c}"] = layer.get("title")
            self.ws_cad[f"H{self.idx_c}"] = layer.get("num_fields")
            self.ws_cad[f"I{self.idx_c}"] = layer.get("num_obj")
            self.ws_cad[f"J{self.idx_c}"] = layer.get("type_geom")
            self.ws_cad[f"K{self.idx_c}"] = layer.get("srs")
            self.ws_cad[f"L{self.idx_c}"] = layer.get("srs_type")
            self.ws_cad[f"M{self.idx_c}"] = layer.get("epsg")

            # Spatial extent
            emprise = "Xmin : {} - Xmax : {} | \nYmin : {} - Ymax : {}".format(
                layer.get("xmin"),
                layer.get("xmax"),
                layer.get("ymin"),
                layer.get("ymax"),
            )
            self.ws_cad[f"N{self.idx_c}"].style = "wrap"
            self.ws_cad[f"N{self.idx_c}"] = emprise

            # Field informations
            fields = layer.get("fields")
            for chp in fields.keys():
                # field type
                if "Integer" in fields[chp][0]:
                    tipo = self.translated_texts.get("entier")
                elif fields[chp][0] == "Real":
                    tipo = self.translated_texts.get("reel")
                elif fields[chp][0] == "String":
                    tipo = self.translated_texts.get("string")
                elif fields[chp][0] == "Date":
                    tipo = self.translated_texts.get("date")
                else:
                    tipo = "unknown"
                    logger.warning(chp + " unknown type")

                # concatenation of field informations
                try:
                    champs = "{} {} ({}{}{}{}{}) ; ".format(
                        champs,
                        chp,
                        tipo,
                        self.translated_texts.get("longueur"),
                        fields[chp][1],
                        self.translated_texts.get("precision"),
                        fields[chp][2],
                    )
                except UnicodeDecodeError:
                    logger.warning(
                        "Field name with special letters: {}".format(
                            chp.decode("latin1")
                        )
                    )
                    # decode the fucking field name
                    champs = (
                        champs
                        + chp.decode("latin1")
                        + " ({}, Lg. = {}, Pr. = {}) ;".format(
                            tipo, fields[chp][1], fields[chp][2]
                        )
                    )
                    # then continue
                    continue

            # Once all fieds explored, write them
            self.ws_cad[f"O{self.idx_c}"] = champs

        # End of method
        return

    def store_md_sgdb(self, metadataset: MetaDatabaseTable):
        """Storing metadata about a file database."""
        # increment line
        self.idx_s += 1
        # use a local alias to reduce confusion and facilitate copy/paste between methods
        row_index = self.idx_s

        # layer name
        self.ws_sgbd[f"A{row_index}"] = metadataset.name

        # connection string
        if metadataset.database_connection.service_name is not None:
            out_connection_string = metadataset.database_connection.pg_connection_uri
        else:
            out_connection_string = (
                f"postgresql://{metadataset.database_connection.user_name}"
                f"@{metadataset.database_connection.host}"
                f":{metadataset.database_connection.port}"
                f"/{metadataset.database_connection.database_name}"
            )
        self.ws_sgbd[f"B{row_index}"] = out_connection_string
        self.ws_sgbd[f"B{row_index}"].style = "Hyperlink"
        # schema
        self.ws_sgbd[f"C{row_index}"] = metadataset.schema_name

        # in case of a source error
        if metadataset.processing_succeeded is False:
            self.ws_sgbd[f"D{row_index}"] = metadataset.processing_error_msg
            self.ws_sgbd[f"A{row_index}"].style = "Warning Text"
            self.ws_sgbd[f"B{row_index}"].style = "Warning Text"
            self.ws_sgbd[f"C{row_index}"].style = "Warning Text"
            self.ws_sgbd[f"D{row_index}"].style = "Warning Text"
            # gdal info
            self.ws_sgbd[f"M{row_index}"] = (
                f"{metadataset.processing_error_type}: "
                f"{metadataset.processing_error_msg}"
            )
            self.ws_sgbd[f"M{row_index}"].style = "Warning Text"
            # interruption of function
            return False

        # structure
        self.ws_sgbd[f"D{row_index}"] = metadataset.attribute_fields_count
        self.ws_sgbd[f"E{row_index}"] = metadataset.features_count
        self.ws_sgbd[f"F{row_index}"] = metadataset.geometry_type

        # SRS
        self.ws_sgbd[f"G{row_index}"] = metadataset.crs_name
        self.ws_sgbd[f"H{row_index}"] = metadataset.crs_type
        self.ws_sgbd[f"I{row_index}"] = metadataset.crs_registry_code

        # Spatial extent
        self.ws_sgbd[f"J{row_index}"].style = "wrap"
        self.ws_sgbd[f"J{row_index}"] = ", ".join(
            str(coord) for coord in metadataset.bbox
        )

        # type
        self.ws_sgbd[f"K{row_index}"] = metadataset.format_gdal_long_name

        # Field informations
        self.ws_sgbd[f"L{row_index}"] = self.format_feature_attributes(
            metadataset=metadataset
        )

        # end of method
        return


# ############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    """Standalone execution and tests"""
    pass
