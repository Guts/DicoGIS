# Tests

## System requirements

- Git
- Docker >= 22

## Testing setup

In your virtual environment:

1. Install development requirements ([Ubuntu](./ubuntu.md#requirements) or [Windows](./windows.md#requirements))
2. Install data fixtures:

    ```sh
    git clone --depth=1 https://github.com/qgis/QGIS-Training-Data.git ./tests/fixtures/qgisdata
    python -m pip install -U gisdata -t ./tests/fixtures
    ```

3. Launch PostGIS container:

    ```sh
    docker compose -f "tests/container/docker-compose.dev.yml" up -d --build
    ```

## Try it out on test dataset

```sh
dicogis-cli inventory --verbose --input-folder tests/fixtures
```

## Run tests suite

```sh
pytest
```
