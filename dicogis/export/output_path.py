#! python3  # noqa: E265

"""Default output path of an inventory, shared by the CLI and the GUI."""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
from datetime import date
from pathlib import Path

# project
from dicogis.utils.slugger import sluggy


# ############################################################################
# ########## Globals ###############
# ##################################

# formats writing one file per dataset, hence a folder as their output
FOLDER_OUTPUT_FORMATS: tuple[str, ...] = ("json", "udata", "iso19139")

# ############################################################################
# ########## Functions #############
# ##################################


def determine_output_path(
    output_path: Path | str | None,
    output_format: str = "excel",
    input_folder: Path | None = None,
    pg_services: list[str] | None = None,
) -> Path:
    """Get the output path depending on options passed.

    Args:
        output_path: output path passed to inventory CLI
        output_format: input output format passed to inventory CLI
        input_folder: input folder passed to inventory CLI
        pg_services: list of postgres services names to use

    Raises:
        ValueError: if output format is not supported

    Returns:
        output path to use. A folder for a format writing one file per dataset,
            a file if output_format=='excel'
    """
    final_output_path = None
    if isinstance(pg_services, list):
        pg_srv_names = "__".join(
            sluggy(pg_service_name) for pg_service_name in pg_services
        )

    # output file path
    if output_path is None:
        if output_format == "excel":
            if isinstance(input_folder, Path):
                final_output_path = Path(
                    f"DicoGIS_{input_folder.name}_{date.today()}.xlsx"
                )
            elif isinstance(pg_services, list):
                final_output_path = Path(
                    f"DicoGIS_PostGIS_{pg_srv_names}_{date.today()}.xlsx"
                )
        elif output_format in FOLDER_OUTPUT_FORMATS:
            if isinstance(input_folder, Path):
                final_output_path = Path(f"DicoGIS_{input_folder.name}_{date.today()}")
            elif isinstance(pg_services, list):
                final_output_path = Path(f"DicoGIS_{pg_srv_names}_{date.today()}")
        else:
            raise ValueError(f"Unsupported output format: {output_format}.")
    else:
        final_output_path = output_path

    return final_output_path


def match_output_path_to_format(output_path: Path, output_format: str) -> Path:
    """Adapt an output path to an output format: an Excel workbook is a `.xlsx`
    file, the formats writing one file per dataset a folder.

    Only the `.xlsx` extension is added or removed, so a name the user typed is
    otherwise kept as is (including dots in a folder name).

    Args:
        output_path: output path to adapt
        output_format: output format (see `dicogis.constants.OutputFormats`)

    Raises:
        ValueError: if output format is not supported

    Returns:
        output path matching the output format
    """
    is_xlsx = output_path.suffix.lower() == ".xlsx"
    if output_format == "excel":
        return (
            output_path
            if is_xlsx
            else output_path.with_name(f"{output_path.name}.xlsx")
        )
    if output_format in FOLDER_OUTPUT_FORMATS:
        return output_path.with_suffix("") if is_xlsx else output_path

    raise ValueError(f"Unsupported output format: {output_format}.")
