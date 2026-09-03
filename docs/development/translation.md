# Manage translations

DicoGIS is shipped in English (source language), French and Spanish. Two
separate mechanisms coexist, split by whether the graphical interface is
involved:

| What you are translating | Mechanism | Files |
| :--- | :--- | :--- |
| Widget text: buttons, labels, tabs, tooltips, message boxes | Qt native translations | `dicogis/ui/i18n/dicogis_{en,fr,es}.ts` → `.qm` |
| Report and CLI output: Excel sheet names, column headers, error messages | `TextsManager` | `dicogis/locale/lang_{EN,FR,ES}.xml` |

The rule of thumb: anything under `dicogis/ui/` uses `self.tr("...")`, anything
reachable from `dicogis-cli` uses `TextsManager`. The command-line interface
must keep working without the `gui` extra installed, which is precisely why the
processing pipeline does not depend on Qt's translation machinery.

## GUI widget text (Qt translations)

### Required tools

`pylupdate6`, which extracts the translatable strings, ships with PyQt6 itself:
installing the `gui` extra is enough.

```sh
python -m pip install -U -e .[gui]
```

`lrelease`, which compiles the translations, and Qt Linguist, the graphical
editor, come from the Qt 6 tools. On Ubuntu:

```sh
sudo apt install qt6-l10n-tools linguist-qt6
```

```{note}
Ubuntu installs those binaries in `/usr/lib/qt6/bin/`, which is not on the
`PATH` by default. Either call them with their full path or add the folder to
your `PATH`:

    export PATH="/usr/lib/qt6/bin:$PATH"
```

### Workflow

1. Write the widget text through `self.tr()`, so it can be extracted:

    ```python
    self.btn_cancel.setText(self.tr("Cancel"))
    ```

1. Update the `.ts` files, once per language. `pylupdate6` merges: existing
    translations are preserved, new strings are added as untranslated entries:

    ```sh
    pylupdate6 dicogis/ui/*.py dicogis/ui/dialogs/*.py --ts dicogis/ui/i18n/dicogis_en.ts
    pylupdate6 dicogis/ui/*.py dicogis/ui/dialogs/*.py --ts dicogis/ui/i18n/dicogis_fr.ts
    pylupdate6 dicogis/ui/*.py dicogis/ui/dialogs/*.py --ts dicogis/ui/i18n/dicogis_es.ts
    ```

1. Translate the new entries, either with Qt Linguist:

    ```sh
    linguist dicogis/ui/i18n/dicogis_fr.ts dicogis/ui/i18n/dicogis_es.ts
    ```

    or directly in the `.ts` files, replacing every
    `<translation type="unfinished" />` with the translated text:

    ```xml
    <message>
        <location filename="../mw_dicogis.py" line="247" />
        <source>Cancel</source>
        <translation>Annuler</translation>
    </message>
    ```

1. Compile the `.qm` files actually loaded at runtime:

    ```sh
    lrelease dicogis/ui/i18n/dicogis_fr.ts -qm dicogis/ui/i18n/dicogis_fr.qm
    lrelease dicogis/ui/i18n/dicogis_es.ts -qm dicogis/ui/i18n/dicogis_es.qm
    ```

1. Check your work:

    ```sh
    pytest tests/test_ui_i18n.py
    ```

    That suite fails, naming the offending strings, when a `self.tr()` string
    has no translation in a shipped locale, or when a `.qm` is out of date with
    its `.ts`.

### English is the source language

`dicogis_en.ts` is kept as a reference of the extracted strings and is
regenerated like the others, but it is **never translated, compiled nor
loaded**: with no translator installed, Qt returns the source string, which is
already English. `DicoGIS._install_qt_translator()` accordingly removes any
installed translator and returns early for `EN`.

This is why `dicogis_en.ts` legitimately shows every entry as unfinished, and
why there is no `dicogis_en.qm`.

## Report and CLI text (`TextsManager`)

Strings written to the output file or printed by the command line live in
`dicogis/locale/lang_{EN,FR,ES}.xml`, one XML element per key:

```xml
<nomfic>Filename</nomfic>
```

`TextsManager.load_texts()` reads the file matching the requested language into
a `localized_strings` dictionary, which is passed explicitly down the pipeline —
to `ProcessingFiles` and to the serializers. Adding a string means adding the
same key to the **three** files: a key missing from one of them silently
serializes as an empty cell, since lookups go through `dict.get()`.

## Add a new language

1. Add it to `AvailableLocales` in `dicogis/constants.py`. That enum feeds the
    GUI language dropdown and the CLI's `--language` option.
1. Create `dicogis/locale/lang_XX.xml`, copying `lang_EN.xml` and translating
    every value.
1. Create and compile `dicogis/ui/i18n/dicogis_xx.ts` / `.qm`, following the
    workflow above. Mind the case: the enum values are uppercase (`FR`), the
    translation filenames lowercase (`dicogis_fr.qm`).
1. Add the matching OS locale to `DicoGIS._apply_locale()` in
    `dicogis/ui/mw_dicogis.py`, which sets `locale.setlocale()` per platform.

## Notes

- Unlike some Qt projects, the compiled `.qm` files **are** tracked in this
    repository. They are declared as package data in `pyproject.toml` and passed
    to PyInstaller with `--add-data` by the GUI builder scripts, so an outdated
    `.qm` ships an outdated interface. Commit them alongside the `.ts` files.
- `.ts` files record the source line of every string, so re-running
    `pylupdate6` after unrelated edits produces `<location>` churn in the diff.
    That is expected.
- Qt matches translations on the exact source string, context included, so
    rewording an existing `self.tr()` string orphans its translation: it comes
    back as a new untranslated entry, and the old one is marked `vanished`.
