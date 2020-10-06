# Develop on Windows

Tested on:

- Windows 10 2004 Professional

## Install Python and Git

Install system requirements:

```bash
sudo apt install git python3-pip python3-tk python3-virtualenv python3-venv virtualenv
```

Clone the repository where you want:

```bash
git clone https://github.com/Guts/DicoGIS.git
# or using ssh
git clone git@github.com:Guts/DicoGIS.git
```

Create and enter virtual environment (change the path at your convenience):

```bash
virtualenv -p /usr/bin/python3 ~/pyvenvs/dicogis
source ~/pyvenvs/dicogis/bin/activate
```

## Install project requirements

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -U -r requirements/ubuntu.txt
```

## Install project

```bash
python -m pip install -e .
```

Happy coding!
