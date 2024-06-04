import requests

api_key = ""
api_version = "1"
api_url_base = "https://demo.data.gouv.fr/api/"

headers = {"Content-Type": "application/json", "X-API-KEY": api_key}

metadata = {
    "description": "Syntaxe Markdown supportée avec du texte en **gras** et même des tableaux\n\n| A | B|\n| - | - |\n| touché | coulé|",
    "title": "chromecast",
    "slug": "test-slug-unique",
    "extras": {"dicogis_version": "test-dev"},
}

req_session = requests.Session()
req_session.headers = headers

result = req_session.post(
    url=f"{api_url_base}{api_version}/datasets", json=metadata
).json()
print(result.get("id"), result.get("slug"))

my_datasets = req_session.get(url=f"{api_url_base}{api_version}/me/datasets/").json()
# print(my_datasets)
for d in my_datasets:
    # req_session.delete(url=f"{api_url_base}{api_version}/datasets/{d.get('id')}")
    print(d.get("extras"))
