#! python3  # noqa: E265

"""
Check what users read in the CLI's --help pages.

Usage from the repo root folder:
    pytest tests/test_cli_help.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# standard library
import importlib
import warnings

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


@pytest.mark.parametrize(
    "module_name",
    ["dicogis.cli.main", "dicogis.cli.cmd_inventory", "dicogis.cli.cmd_publish"],
)
def test_cli_options_use_no_deprecated_typer_parameter(module_name):
    """Typer warns about parameters it will remove (e.g. is_flag) when the
    options are declared, i.e. when the command modules are imported."""
    module = importlib.import_module(module_name)
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        importlib.reload(module)
