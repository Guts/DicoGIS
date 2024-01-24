#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
from pathlib import Path
from typing import Annotated, Optional

# 3rd party
import typer

# project
from dicogis.__about__ import __title__, __version__

# ############################################################################
# ########## Globals ###############
# ##################################

cli_dicogis = typer.Typer()
state = {"verbose": False}


# ############################################################################
# ########## Functions #############
# ##################################


def version_callback(value: bool):
    """Special callback to show verison and exit.

    See: https://typer.tiangolo.com/tutorial/options/version/

    Raises:
        typer.Exit: CLI exit
    """
    if value:
        typer.echo(f"{__title__} {__version__}")
        raise typer.Exit()


@cli_dicogis.callback()
def main(
    verbose: bool = False,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
):
    """Common options to commands or option only applicable to the main command.

    Args:
        verbose (bool, optional): enable verbose mode. Defaults to False.
        version (Annotated[ Optional[bool], typer.Option, optional): show version and
            exit. Defaults to version_callback.
    """
    if verbose:
        state["verbose"] = True
    if version:
        typer.echo(f"{__title__} {__version__}")
        raise typer.Exit()


@cli_dicogis.command(
    help="List geodata and extract metadata into an Excel (.xlsx) spreadsheet file."
)
def inventory(
    input_folder: Annotated[
        Optional[Path],
        typer.Option(dir_okay=True, file_okay=False, readable=True, resolve_path=True),
    ]
):
    """Command to list geodata starting from a

    Args:
        input_folder (Annotated[Optional[Path], typer.Option): _description_
    """
    typer.echo(f"Analysing geodata stored in {input_folder}")


@cli_dicogis.command(help="Send metadata to a database.")
def sync():
    """Command in charge of sending metadata to an external database."""
    typer.echo("Syncing metadata")


# ############################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """standalone execution"""
    cli_dicogis()
