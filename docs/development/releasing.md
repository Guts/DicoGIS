# Release workflow

1. Change the version number in `__about__.py`
1. Commit changes with a message like `release: bump version to X.x.x` to the main branch
1. Apply a git tag with the relevant version: `git tag -a 0.3.0 {git commit hash} -m "New awesome feature"`
1. Push commit and tag to main branch: `git push --tags`

Pushing the tag triggers the CI/CD workflows. Among them, `pypi_publisher.yml` builds the source and wheel distributions, runs `twine check --strict` and checks that the tag matches the version declared in `__about__.py` (compared as [PEP 440](https://peps.python.org/pep-0440/) versions: `4.0.0-beta9` and `4.0.0b9` are the same version), then publishes them to [PyPI](https://pypi.org/project/dicogis/).

The workflow can also be started manually from the _Actions_ tab to build and check the distributions without publishing anything.

## PyPI publication

The publication relies on [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OpenID Connect): no API token is stored in the repository.

One-time setup, before the first release:

1. On PyPI, in the account's [publishing settings](https://pypi.org/manage/account/publishing/), add a _pending publisher_ with the project name `dicogis`, the owner `Guts`, the repository `DicoGIS`, the workflow `pypi_publisher.yml` and the environment `pypi`
1. On GitHub, in the repository settings, create an environment named `pypi` (optionally with required reviewers, to confirm each publication)

The first successful publication turns the pending publisher into a regular one.

> A version can be published only once on PyPI: even deleted, a file can't be uploaded again under the same name, so moving the tag and re-running the workflow doesn't fix a faulty release. [Yank it](https://pypi.org/help/#yanked) and publish a new version.

## Unpublish a tag

```sh
git tag -d old
git push origin :refs/tags/old
git push --tags
```

## Manual upload to PyPi

> This method requires an API token on PyPi

If the CI/CD fails for any reason, here comes the manual procedure:

1. Install required packages:

    ```sh
    python -m pip install -U build twine
    ```

1. Clean previous builds and build package artifacts (source and wheel distributions, in `dist/`):

    ```sh
    rm -rf dist/
    python -m build
    ```

1. Check built artifacts:

    ```sh
    twine check --strict dist/*
    ```

1. Upload built artifacts to PyPi:

    ```sh
    twine upload -u __token__ dist/*
    ```
