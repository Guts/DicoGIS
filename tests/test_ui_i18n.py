#! python3  # noqa: E265


"""
Guards against the GUI translations drifting away from the source strings.

Widget text goes through Qt's own i18n: `self.tr("...")` calls, extracted into
dicogis/ui/i18n/dicogis_{en,fr,es}.ts with pylupdate6 and compiled to .qm with
lrelease (see CLAUDE.md). Nothing enforced that pipeline being re-run, so
strings added by a PR stayed English forever in the FR and ES interfaces.

Reads the sources with `ast` rather than importing them, so this needs neither
PyQt6 nor GDAL. The .qm freshness check does need PyQt6 and skips without it.

Usage from the repo root folder:
    pytest tests/test_ui_i18n.py
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import ast
from pathlib import Path
from xml.etree import ElementTree

# 3rd party
import pytest


# ##############################################################################
# ########## Globals ###############
# ##################################

UI_FOLDER = Path(__file__).parent.parent / "dicogis" / "ui"
I18N_FOLDER = UI_FOLDER / "i18n"
# English is the source language: its .ts is a reference, never compiled nor
# loaded at runtime, so untranslated entries there are expected
TRANSLATED_LOCALES = ("fr", "es")


# ##############################################################################
# ########## Functions #############
# ##################################


def _translatable_sources() -> set[str]:
    """Collect every string literal handed to a `self.tr()` call in the GUI.

    Returns:
        the source strings Qt will look up at runtime
    """
    sources: set[str] = set()
    for module_path in sorted(UI_FOLDER.rglob("*.py")):
        tree = ast.parse(module_path.read_text(encoding="UTF-8"), str(module_path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "tr"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                sources.add(node.args[0].value)
    return sources


def _finished_translations(locale: str) -> dict[tuple[str, str], str]:
    """Read the translations a locale actually provides.

    Args:
        locale: 2 letters language code, lowercase

    Returns:
        (context, source string) -> translation, for finished entries only
    """
    translations: dict[tuple[str, str], str] = {}
    # noqa S314: the parsed file is the project's own translation source,
    # shipped in this repository, not input from anywhere untrusted
    root = ElementTree.parse(  # noqa: S314
        I18N_FOLDER / f"dicogis_{locale}.ts"
    ).getroot()
    for context in root.findall("context"):
        context_name = context.findtext("name") or ""
        for message in context.findall("message"):
            translation = message.find("translation")
            source = message.findtext("source")
            if source is None or translation is None:
                continue
            # pylupdate6 marks entries it added but nobody translated yet
            if translation.get("type") in ("unfinished", "vanished"):
                continue
            if translation.text:
                translations[(context_name, source)] = translation.text
    return translations


# ##############################################################################
# ########## Tests ##################
# ##################################


def test_translatable_sources_are_found():
    """Guard the guard: an extraction returning nothing would make every
    assertion below vacuously true."""
    assert len(_translatable_sources()) > 50


@pytest.mark.parametrize("locale", TRANSLATED_LOCALES)
def test_every_widget_string_is_translated(locale):
    """Every `self.tr()` string must have a translation in each shipped locale.

    Fails when a PR adds widget text without re-running pylupdate6 and filling
    the new entries in -- which is how "Cancel", "Canceling...", the parallel
    scan options and the unsupported-format tooltip ended up displayed in
    English whatever the language selected.
    """
    translated_sources = {source for _, source in _finished_translations(locale)}

    untranslated = sorted(
        source for source in _translatable_sources() if source not in translated_sources
    )

    assert not untranslated, (
        f"{len(untranslated)} string(s) have no {locale.upper()} translation. "
        "Re-run pylupdate6 (see CLAUDE.md), fill the new <translation> entries "
        f"and recompile the .qm: {untranslated}"
    )


@pytest.mark.parametrize("locale", TRANSLATED_LOCALES)
def test_compiled_qm_matches_the_ts(locale):
    """The shipped .qm must carry what the .ts says.

    Only the .qm is loaded at runtime, so a .ts updated without running
    lrelease again changes nothing for the end user.
    """
    qtcore = pytest.importorskip("PyQt6.QtCore", reason="PyQt6 (gui extra) required")

    translator = qtcore.QTranslator()
    assert translator.load(str(I18N_FOLDER / f"dicogis_{locale}.qm"))

    missing_from_qm = sorted(
        f"[{context}] {source}"
        for (context, source), expected in _finished_translations(locale).items()
        if translator.translate(context, source) != expected
    )

    assert not missing_from_qm, (
        f"dicogis_{locale}.qm is out of date with dicogis_{locale}.ts: recompile "
        f"it with lrelease (see CLAUDE.md). Missing: {missing_from_qm}"
    )


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    import sys

    sys.exit(__import__("pytest").main([__file__]))
