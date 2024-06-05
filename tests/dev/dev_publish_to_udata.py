from os import getenv

import requests

api_key = getenv("DICOGIS_UDATA_API_KEY")
api_version = "1"
api_url_base = "https://demo.data.gouv.fr/api/"
organization_id: str | None = "6660470af6d866033bfc1bb4"
organization_id = None

headers = {"Content-Type": "application/json", "X-API-KEY": api_key}

metadata = {
    "description": "Syntaxe Markdown supportée avec du texte en **gras** et même des tableaux\n\n| A | B|\n| - | - |\n| touché | coulé|",
    "title": "chromecast",
    "slug": "test-slug-unique",
    "extras": {"dicogis_version": "test-dev"},
}

if organization_id is not None and len(organization_id):
    metadata["organization"] = organization_id

req_session = requests.Session()
req_session.headers = headers

result = req_session.post(url=f"{api_url_base}{api_version}/datasets", json=metadata)
result.raise_for_status()

result = result.json()

print(result.get("id"), result.get("slug"))

if organization_id is not None and len(organization_id):
    already_published_datasets = req_session.get(
        url=f"{api_url_base}{api_version}/organizations/{organization_id}/datasets/"
    )

else:
    already_published_datasets = req_session.get(
        url=f"{api_url_base}{api_version}/me/datasets/"
    )

already_published_datasets.raise_for_status()
already_published_datasets = already_published_datasets.json().get("data")

print(already_published_datasets)
# print(my_datasets)
for d in already_published_datasets:
    # req_session.delete(url=f"{api_url_base}{api_version}/datasets/{d.get('id')}")
    print(d.get("extras"))
