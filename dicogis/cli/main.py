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
from dicogis.cli.cmd_inventory import inventory

# ############################################################################
# ########## Globals ###############
# ##################################

dicogis_cli = typer.Typer()
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


@dicogis_cli.callback()
def main(
    verbose: Annotated[
        bool,
        typer.Option(is_flag=True, help="Increase verbosity to show debug logs."),
    ] = False,
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
        verbose: enable verbose mode. Defaults to False.
        version: show version and exit. Defaults to version_callback.
    """
    if verbose:
        state["verbose"] = True
        logger.setLevel = logging.DEBUG

    if version:
        typer.echo(f"{__title__} {__version__}")
        raise typer.Exit()


# integrate subcommands
dicogis_cli.command()(inventory)

# exposed for documentation
click_object = typer.main.get_command(dicogis_cli)

# ############################################################################
# #### Stand alone program ########
# #################################
if __name__ == "__main__":
    """standalone execution"""
    dicogis_cli()
