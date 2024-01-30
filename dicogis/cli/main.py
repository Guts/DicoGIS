#! python3  # noqa: E265

# ############################################################################
# ########## Libraries #############
# ##################################

# standard lib
import logging
from typing import Annotated, Optional

# 3rd party
import typer

# project
from dicogis.__about__ import __title__, __version__
from dicogis.cli.cmd_list import cli_list

# ############################################################################
# ########## Globals ###############
# ##################################

cli_dicogis = typer.Typer()
state = {"verbose": False}
APP_NAME = __title__
logger = logging.getLogger(__name__)


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


# integrate subcommands
cli_dicogis.add_typer(cli_list, name="list")


# ############################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """standalone execution"""
    cli_dicogis()
