#! python3  # noqa: E265

"""
Set a GeoNetwork up for the publication scenarios, like a catalog in production: the
ISO and GeoNetwork Schematron rules stay required, the DataCite and DCAT-AP HVD ones
only report.

On a fresh GeoNetwork 4.4, every Schematron rule set is required, unless its file name
ends with .report_only or .disabled: rejectIfInvalid then refuses any record that
doesn't describe a DataCite publication and a High Value Dataset of the European
Union, which is out of reach of DicoGIS and of most datasets.

Talks to the catalog with requests, not with the HTTP clients of DicoGIS: the setup
doesn't depend on the code under test. Idempotent.

Usage from the repo root folder, a GeoNetwork running:
    python -m tests.fixtures.geonetwork_setup http://localhost:8080/geonetwork
"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# standard library
import argparse
from collections.abc import Iterable

# 3rd party
import requests
from lxml import etree


# ##############################################################################
# ########## Globals ###############
# ##################################

REPORT_ONLY_SCHEMATRONS: frozenset[str] = frozenset(
    {"schematron-rules-datacite", "schematron-rules-dcat-ap-hvd"}
)

# ##############################################################################
# ########## Functions #############
# ##################################


def report_only_schematrons(
    url_base: str,
    username: str,
    password: str,
    rule_names: Iterable[str] = REPORT_ONLY_SCHEMATRONS,
    timeout: float = 60.0,
) -> list[str]:
    """Have the catalog report the failures of some Schematron rule sets instead of
    refusing the records, whatever the metadata schema.

    Goes through the services of the administration console: GeoNetwork 4.4 has no
    REST API for it.

    Args:
        url_base: URL of the catalog, up to its context path
        username: login of an administrator
        password: password of the administrator
        rule_names: names of the rule sets, as listed by the catalog
        timeout: timeout of each request, in seconds

    Raises:
        RuntimeError: if the catalog has none of the rule sets of a name, or doesn't
            confirm a change

    Returns:
        rule sets changed, as "rule name (schema)"
    """
    url_base = url_base.rstrip("/")
    session = requests.Session()
    session.auth = (username, password)

    # the first answer sets the CSRF token, expected back on any POST
    session.get(
        f"{url_base}/srv/api/me",
        headers={"Accept": "application/json"},
        timeout=timeout,
    ).raise_for_status()
    csrf_token = session.cookies.get("XSRF-TOKEN")

    response = session.get(
        f"{url_base}/srv/eng/admin.schematroncriteriagroup.list",
        params={"includeSchematron": "true"},
        timeout=timeout,
    )
    response.raise_for_status()
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    groups = etree.fromstring(response.content, parser)

    wanted = set(rule_names)
    changed: list[str] = []
    for group in groups.findall("record"):
        rule_name = group.findtext("schematron/rulename")
        if rule_name not in wanted:
            continue
        update = session.post(
            f"{url_base}/srv/eng/admin.schematroncriteriagroup.update",
            data={
                "schematronId": group.findtext("id/schematronid"),
                "groupName": group.findtext("id/name"),
                "requirement": "REPORT_ONLY",
            },
            headers={"X-XSRF-TOKEN": csrf_token or ""},
            timeout=timeout,
        )
        update.raise_for_status()
        if etree.fromstring(update.content, parser).tag != "ok":
            raise RuntimeError(f"{rule_name} not changed: {update.text[:500]}")
        changed.append(f"{rule_name} ({group.findtext('schematron/schemaname')})")

    missing = wanted - {name.split(" ")[0] for name in changed}
    if missing:
        raise RuntimeError(
            f"No Schematron rule set named {', '.join(sorted(missing))} in the "
            "catalog: its version may have renamed them."
        )
    return changed


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    arguments_parser = argparse.ArgumentParser(
        description="Make the DataCite and DCAT-AP HVD rules of a GeoNetwork report only."
    )
    arguments_parser.add_argument("url_base", help="URL of the catalog")
    arguments_parser.add_argument("--username", default="admin")
    arguments_parser.add_argument("--password", default="admin")
    arguments = arguments_parser.parse_args()
    for rule_set in report_only_schematrons(
        arguments.url_base, arguments.username, arguments.password
    ):
        print(f"Report only: {rule_set}")
