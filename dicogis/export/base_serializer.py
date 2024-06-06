#! python3  # noqa: E265


# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
from __future__ import annotations

import logging
from pathlib import Path

# project
from dicogis import export
from dicogis.constants import OutputFormats
from dicogis.utils.texts import TextsManager

# ############################################################################
# ######### Globals ############
# ##############################

logger = logging.getLogger(__name__)

# ##############################################################################
# ########## Classes ###############
# ##################################


class MetadatasetSerializerBase:
    """Base class for metadataset serializers."""

    def __init__(
        self,
        localized_strings: dict | None = None,
        output_path: Path | None = None,
        opt_raw_path: bool = False,
        opt_size_prettify: bool = True,
    ) -> None:
        """Initialize object."""
        self.localized_strings = localized_strings
        if self.localized_strings is None:
            self.localized_strings = TextsManager().load_texts()

        # output path
        self.output_path = output_path

        # options
        self.opt_raw_path = opt_raw_path
        self.opt_size_prettify = opt_size_prettify

    def pre_serializing(self, **kwargs):
        """Operations to run before serialization."""
        pass

    def post_serializing(self, **kwargs):
        """Operations to run after serialization."""
        pass

    @classmethod
    def get_serializer_from_parameters(
        cls,
        format_or_serializer: (
            str
            | OutputFormats.excel
            | OutputFormats.json
            | OutputFormats.udata
            | MetadatasetSerializerBase
        ),
        output_path: Path | None = None,
        opt_raw_path: bool = False,
        opt_prettify_size: bool = True,
        localized_strings: dict | None = None,
    ) -> (
        export.to_json.MetadatasetSerializerJson
        | export.to_xlsx.MetadatasetSerializerXlsx
    ):
        """Initiate the adequat serializer depending on parameters.

        Args:
            format_or_serializer: output format or serializer
            output_path: output path
            opt_raw_path: option to serialize dataset raw path without any sugar syntax
            opt_prettify_size: option to prettify size in octets (typically: 1 ko instead
                of 1024 octects)
            localized_strings: localized texts. Defaults to None.

        Returns:
            serializer already initialized
        """
        print("ho", type(format_or_serializer))
        if isinstance(format_or_serializer, MetadatasetSerializerBase):
            return format_or_serializer

        if isinstance(format_or_serializer, str):
            format_or_serializer = OutputFormats(format_or_serializer)

        if format_or_serializer == OutputFormats.excel:
            # creating the Excel workbook
            output_serializer = export.to_xlsx.MetadatasetSerializerXlsx(
                localized_strings=localized_strings,
                opt_raw_path=opt_raw_path,
                opt_size_prettify=opt_prettify_size,
                output_path=output_path,
            )
        elif format_or_serializer == OutputFormats.json:
            output_serializer = export.to_json.MetadatasetSerializerJson(
                localized_strings=localized_strings,
                opt_size_prettify=opt_prettify_size,
                output_path=output_path,
            )
        elif format_or_serializer == OutputFormats.udata:
            output_serializer = export.to_json.MetadatasetSerializerJson(
                flavor="udata",
                localized_strings=localized_strings,
                opt_size_prettify=opt_prettify_size,
                output_path=output_path,
            )
        else:
            raise NotImplementedError(
                f"Specified output format '{format_or_serializer}' is not available."
            )

        return output_serializer
