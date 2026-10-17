#! python3  # noqa: E265

"""
Check what users read in the CLI's --help pages.

Usage from the repo root folder:
    pytest tests/test_cli_help.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# 3rd party
import pytest
from typer.testing import CliRunner

# package
from dicogis.cli.main import dicogis_cli


# #############################################################################
# ########## Globals ###############
# ##################################

runner = CliRunner()


# #############################################################################
# ########## Functions #############
# ##################################


def _help_of(*command: str) -> str:
    """Return the --help page of a (sub)command, wide enough not to be wrapped."""
    result = runner.invoke(
        dicogis_cli, [*command, "--help"], env={"COLUMNS": "200", "NO_COLOR": "1"}
    )
    assert result.exit_code == 0, result.output
    return result.output


# #############################################################################
# ########## Tests ##################
# ##################################


@pytest.mark.parametrize("command", ["inventory", "publish"])
def test_verbose_option_is_bound_to_dicogis_debug(command):
    """Every option is configurable by an environment variable: --verbose is
    documented as DICOGIS_DEBUG, the subcommands' one included."""
    assert "DICOGIS_DEBUG" in _help_of(command)
