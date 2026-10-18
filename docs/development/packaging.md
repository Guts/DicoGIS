# Packaging into an executable

The project takes advantage of [PyInstaller](https://pyinstaller.readthedocs.io/) to package the application into an executable.

The output binary and all embedded dependencies is located into a subfolder named: `dist/DicoGIS_{version}_{operating-system}_Python{python-version}`.

## Windows

> Comply with [development requirements](windows) before to run.

```powershell
# Generates MS Executable for CLI
python -O .\builder\pyinstaller_build_windows_cli.py

# Generates MS Executable for GUI
python -O .\builder\pyinstaller_build_windows_gui.py
```

Both scripts embed a version resource in the executable (its file properties in Windows: version, author, description…), built from `dicogis/__about__.py` by `builder/win_version_info.py`.

To run it, double-click on the executable file (*.exe).

## Ubuntu

> Comply with [development requirements](ubuntu) before to run.

```bash
# Generates binary executable
python -O ./builder/pyinstaller_build_ubuntu.py
```

To run it, for example:

```bash
cd dist/DicoGIS_3-0-0_Ubuntu20-04_64bit_Python3-8-5/
./DicoGIS_3-0-0_Ubuntu20-04_64bit_Python3-8-5
```
