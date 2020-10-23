# Documentation

Project uses Sphinx to generate documentation from docstrings (documentation in-code) and custom pages (markdown or rst).

## Build documentation website

To build it:

```powershell
# install aditionnal dependencies
python -m pip install -U -r docs/requirements.txt
# build it
sphinx-build -b html docs docs/_build
```

Open `docs/_build/index.html` in a web browser.
