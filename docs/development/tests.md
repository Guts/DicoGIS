# Tests

## System requirements

- Docker >= 22

## Testing setup

In your virtual environment:

1. Install development requirements ([Ubuntu](./ubuntu.md#requirements) or [Windows](./windows.md#requirements))
2. Install data fixtures:

    ```bash
    python -m pip install -U gisdata -t ./tests/fixtures
    ```

3. Launch PostGIS container:

    ```sh
    docker compose -f "tests/container/docker-compose.dev.yml" up -d --build
    ```

## Run tests suite

```sh
pytest
```
