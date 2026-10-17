#! python3  # noqa: E265


"""
Guards the boundary between the CLI and the rest of the package.

`dicogis/cli` holds the Typer commands only: the GUI, which must also run
inside QGIS where Typer and Rich aren't installed, and the core modules must
never import it. Shared logic belongs in the core packages (export, listing,
publishing...), which the CLI imports, not the other way around.

Reads the sources with `ast`: needs neither GDAL nor PyQt6.

Usage from the repo root folder:
    pytest tests/test_cli_isolation.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import ast
import sys
from pathlib import Path

# 3rd party
import pytest


# ##############################################################################
# ########## Globals ###############
# ##################################

PACKAGE_FOLDER = Path(__file__).parent.parent / "dicogis"
CLI_FOLDER = PACKAGE_FOLDER / "cli"

# ##############################################################################
# ########## Tests ##################
# ##################################


def test_only_the_cli_imports_the_cli() -> None:
    offenders: list[str] = []
    for module_path in sorted(PACKAGE_FOLDER.rglob("*.py")):
        if CLI_FOLDER in module_path.parents:
            continue
        tree = ast.parse(module_path.read_text(encoding="UTF-8"), str(module_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            else:
                continue
            offenders.extend(
                f"{module_path.relative_to(PACKAGE_FOLDER)}:{node.lineno} {name}"
                for name in names
                if name == "dicogis.cli" or name.startswith("dicogis.cli.")
            )

    assert not offenders, (
        f"Move the shared logic out of dicogis.cli instead of importing it: {offenders}"
    )


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
