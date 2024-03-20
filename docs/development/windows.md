# Develop on Windows

Tested on:

- Windows 10 Professional - build 19041 (= version 2004)
- Windows 11 Professional - build 22621.3007

## Common

### Enable remote scripts (for virtual environment)

Open a Powershell prompt as **administrator** inside any folder:

```powershell
# if not already done, enable scripts - required by virtualenv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

----

## Using pre-built wheel

### Requirements

- Python 3.10+ installed with the Windows MSI installer (version from the Windows store is not working)

### Download GDAL wheel

1. Go to <https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal> or to <https://github.com/cgohlke/geospatial-wheels/releases/latest>
1. Download the appropriate package for the Python environment (version, type...). For example: `GDAL-3.8.4-cp310-cp310-win_amd64`
1. Move downloaded wheel to the `lib` subfolder
1. Make sure there is only one wheel of GDAL in the `lib` subfolder

### Installation steps

Typically, you can run these commands:

```powershell
# create a virtual env - change with your Python version
py -3.10 -m venv .venv

# enable virtual env
.\.venv\Scripts\activate
```

## Install project requirements

> Within the virtual environment just created before

```powershell
python -m pip install -U pip setuptools wheel
python -m pip install -U -r requirements/development.txt
python -m pip install -U -r requirements/windows.txt
```

## Install project

```sh
python -m pip install -U -e .[dev]
```

### Try it

CLI:

```sh
dicogis-cli --help
```

GUI:

```sh
python dicogis/dicogis.py
```

## Install git hooks

```sh
pre-commit install
```

Happy coding!

----

## Using conda

### Requirements for conda

- conda >= 4.8

### Installation steps with conda

Open the Anaconda Powershell Prompt in the repository folder, then:

```powershell
# add conda-forge to channels
conda config --add channels conda-forge

# ensure pip, setuptools and wheel are added
conda config --set add_pip_as_python_dependency true

# create conda environment
conda env create -f .\requirements\conda-env-dev.yml

# enter the conda virtual environment
conda activate dicogis-dev

# finally, install the package in editable mode
python -m pip install -e .
```

Happy coding!
