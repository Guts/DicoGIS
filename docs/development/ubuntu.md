# Develop on Ubuntu

Tested on:

- Ubuntu 22.04

## Requirements

- GDAL >= 3.4.1
- Python >= 3.9
- Network access to:
    - Python Package Index: <https://pypi.org/>

## Install system requirements

### Install GDAL

> As stipulated on [official GDAL Python wrapper](https://pypi.org/project/GDAL/), libgdal-dev and numpy are required to build it.

#### Choose your PPA

We listed here 2 options but it might be non up to date.

Some packages may be required to perform PPA operations:

```sh
sudo apt install ca-certificates gnupg lsb-release software-properties-common
sudo apt update
```

##### QGIS PPA

If you use QGIS, it's recomended to use the same GDAL version by setting the QGIS PPA:

```sh
sudo mkdir -p /etc/apt/keyrings
sudo wget -O /etc/apt/keyrings/qgis-archive-keyring.gpg https://download.qgis.org/downloads/qgis-archive-keyring.gpg
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/qgis-archive-keyring.gpg] https://qgis.org/ubuntu-ltr \
$(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/qgis.list > /dev/null
sudo apt update
```

##### UbuntuGIS

If you want to use a specific version and get access to newer GDAL versions, UbuntuGIS is a good choice:

```sh
sudo add-apt-repository ppa:ubuntugis/ubuntugis-unstable
sudo apt update
```

#### Installation

To use the latest GDAL version available in the PPA you set up:

```sh
sudo apt-get install gdal-bin libgdal-dev
```

Or, optionally, you can define which exact GDAL version you want to use. For example:

```sh
export GDAL_VERSION=3.4.1
sudo apt install gdal-bin=$GDAL_VERSION libgdal-dev=$GDAL_VERSION
```

Check it:

```sh
gdal-config --version
```

Expose some paths used for wheel build as environment variables:

```sh
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
```

### Install Python and Git

Install system requirements:

```sh
sudo apt install git python3-pip python3-tk python3-venv unifont
```

Clone the repository where you want:

```sh
git clone https://github.com/Guts/DicoGIS.git
# or using ssh
git clone git@github.com:Guts/DicoGIS.git
```

Move into the cloned folder:

```sh
cd DicoGIS
```

Create and enter virtual environment (change the path at your convenience):

```sh
python3 -m venv .venv
source .venv/bin/activate
```

## Install project requirements

> Within the virtual environment just created before

```sh
python -m pip install -U pip setuptools wheel
python -m pip install -U gdal=="$(gdal-config --version).*"
python -m pip install -U -r requirements/base.txt
```

## Install project

```sh
python -m pip install -U -e .[gdal,dev]
```

### Try it

CLI:

```sh
dicogis-cli --help
```

GUI:

```sh
dicogis-gui
# or
python dicogis/ui/main.py
```

## Install git hooks

```sh
pre-commit install
```

Happy coding!
