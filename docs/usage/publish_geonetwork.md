# Publishing to GeoNetwork

DicoGIS publishes metadata to a GeoNetwork 4.4 catalog through its REST API, in two steps: export the metadata as ISO 19139 files, then publish the folder holding them.

## Export the metadata

From the GUI, pick _ISO 19139 XML files_ as output format: at the end of the analysis, the `Publish` tab points at the output folder. From the command line:

```sh
dicogis-cli inventory --input-folder ./my_data --language FR --output-format iso19139 --output-path ./my_records
```

Each dataset makes one XML file, a file geodatabase (GeoPackage, Esri FileGDB, SpatiaLite) making one record covering all its layers. A dataset which can't be opened makes no record.

Records are identified by a UUID derived from the location of the dataset: publishing again updates the same record. The same dataset seen through two locations (drive letter and UNC path, two PostgreSQL services) makes two records.

The contact of the records comes from `DICOGIS_ISO_CONTACT_ORGANISATION` and `DICOGIS_ISO_CONTACT_EMAIL` (see [settings](./settings.md)). The location of the datasets only ends up in the records with `--opt-include-original-path`.

## Publish them

The account needs at least the `Editor` profile. The group is mandatory and given by its numeric identifier, listed by `GET /srv/api/groups` on the instance, with an `Accept: application/json` header (without it, GeoNetwork answers `500 Service not found`):

```sh
dicogis-cli publish --target geonetwork --input-folder ./my_records --geonetwork-url-base https://catalogue.example/geonetwork --geonetwork-group 2
```

The username and the password are asked for unless given through their options or environment variables. From the GUI, pick _GeoNetwork_ in the `Publish` tab.

## Records already in the catalog

Two modes deal with a record the catalog already has:

- `overwrite` (default) replaces it: what was changed by hand in the catalog is lost.
- `complete` retrieves it, fills its empty fields and leaves everything else as is. The report lists the fields added to each record. It's only sent back if there's something to add. A record the catalog holds in another schema than ISO 19139 (ISO 19115-3 for example) is left as is and reported.

When the workflow of GeoNetwork is enabled, updates go to a working copy to be validated in the catalog, and records aren't made visible to everyone.

Reading a record in `complete` mode looks at what an editor sees, the working copy if there's one, and doesn't raise its popularity.

## Validity

With `--geonetwork-reject-if-invalid`, the catalog refuses the records invalid against the XSD and tells why in the report. Records valid against the XSD can still be reported by the Schematron rules of the catalog (ISO, INSPIRE): DicoGIS targets the XSD only.

## Inside QGIS

The publication goes through the network stack of QGIS, with its proxy settings, and runs in a task of its task manager. In the `Publish` tab, the identifier of a configuration of the QGIS authentication manager can replace the username and the password. Behind a single sign-on (Keycloak, CAS...), GeoNetwork may not accept a basic authentication: such a configuration may cover it, to be tested on the instance. Outside QGIS, only the basic authentication is available.
