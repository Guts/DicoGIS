# Documentation

Project uses Sphinx to generate documentation from docstrings (documentation in-code) and custom pages (markdown or rst).

## Build documentation website

To build it:

```powershell
# install aditionnal dependencies
python -m pip install -U -r docs/requirements.txt
# build it
sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/index.html` in a web browser.

----

## Deploy documentation website

Documentation website is hosted on GitHub Pages. Deployment takes advantage of [`ghp-import` library](https://pypi.org/project/ghp-import/).
It's automatically triggered on CI but it's stille possible to deploy it manually:

```powershell
ghp-import --force --no-jekyll --push ./docs/_build/html
```

Files are uploaded to the branch `gh-pages` of the repository: <https://github.com/Guts/DicoGIS/tree/gh-pages>.
