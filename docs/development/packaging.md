# Packaging into an executable

The project takes advantage of [PyInstaller](https://pyinstaller.readthedocs.io/) to package the application into an executable.

## Windows

> Comply with [development requirements](windows) before to run.

```powershell
# Generates MS Version Info
python .\builder\version_info_templater.py

# Generates MS Executable
python -O .\builder\pyinstaller_build_windows.py
```

## Ubuntu

> Comply with [development requirements](ubuntu) before to run.

```bash
# Generates binary executable
python -O ./builder/pyinstaller_build_ubuntu.py
```
