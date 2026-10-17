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
        output path to use. A folder if output_format=='json',
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
        elif output_format in ("json", "udata"):
            if isinstance(input_folder, Path):
                final_output_path = Path(f"DicoGIS_{input_folder.name}_{date.today()}")
            elif isinstance(pg_services, list):
                final_output_path = Path(f"DicoGIS_{pg_srv_names}_{date.today()}")
        else:
            raise ValueError(f"Unsupported output format: {output_format}.")
    else:
        final_output_path = output_path

    return final_output_path
