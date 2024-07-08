# {{ title }} - Documentation

> **Description:** {{ description }}  
> **Author and contributors:** {{ author }}  
> **Version:** {{ version }}  
> **Source code:** {{ repo_url }}  
> **License:** {{ license }}  
> **Last documentation build:** {{ date_update }}

----

```{figure} ./static/img/DicoGIS_CLI_GUI.png
:align: center
_DicoGIS CLI and GUI side by side_
```

## Whats is it?

A self-porting utility that generates a spreadsheet with technical metadata from a geographic data source. Features:

- supports a set of main GIS file formats and PostGIS databases
- serializes results as MS Excel spreadsheet (.xlsx) or JSON files
- (experimental) publish metadata to an [udata](https://github.com/opendatateam/udata) instance (used by the well-known French open data portal <https://data.gouv.fr>)
- usable through a minimalist graphical interface (GUI) or as command-line (CLI)
- open source (Apache 2)
- free to use, not to develop/test/document ([sponsorhips and tips welcome!](./misc/funding.md))
- embeds a version of GDAL/OGR to read data (no reinvented wheel here)
- compatible with various operating systems (official support for Ubuntu LTS and Windows)
- embraces the [KISS principle](https://en.wikipedia.org/wiki/KISS_principle) and follows [SemVer](https://semver.org/)

### Use cases

- quick and dirty lookup on data sources (audit...)
- simple knowledge sharing about GIS data
- creating an appendix to a deliverable (study, atlas...) containing geographic data
- publish metadata to external catalog
- starter kit for data governance policy

## Try it

1. Go to the [latest releases on GitHub](https://github.com/Guts/DicoGIS/releases/latest)
1. Below `Assets` dropdown, download the flavor you want: CLI (command-line) or GUI (graphical)
1. Give it permission to run:
    - `chmod +x DicoGIS-*.exe` on Linux
    - tell Windows it's safe (if you think so ;) )
1. Run it

## Like it ? Fund it

```{include} misc/_fund_section.md

```

Thanks and look at the previous [sponsors](./misc/funding.md#sponsors).

## Screencast

> This screen cast has been made with an old version but the workflow is still pretty much the same

<iframe width="100%" height="400" src="https://www.youtube.com/embed/3d6xiInUXIU" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

### Blog posts

- [DicoGIS : le dictionnaire de données SIG](https://geotribu.fr/dicogis/) (Geotribu, 2014, French)
- [DicoGIS: el diccionario de datos GIS](https://mappinggis.com/2014/10/dicogis-el-diccionario-de-datos-gis/) (MappingGIS, 2014, Spanish)

----

## Table of contents

```{toctree}
---
maxdepth: 1
caption: Global tour
---
introduction/en
introduction/fr
introduction/es
```

```{toctree}
---
maxdepth: 1
caption: Usage
---
usage/cli
usage/settings
```

```{toctree}
---
maxdepth: 2
caption: Miscellaneous
titlesonly: true
---
misc/funding
misc/formats_matrix
misc/compatibility
misc/credits
```

----

## Contribute

```{toctree}
---
maxdepth: 1
---
misc/funding
development/contribute
development/windows
development/ubuntu
development/tests
development/documentation
development/packaging
development/releasing
Code documentation <_apidoc/modules>
```
