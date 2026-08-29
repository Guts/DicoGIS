# syntax=docker/dockerfile:1

# DicoGIS CLI container image.
#
# Based on the official GDAL images (https://github.com/OSGeo/gdal/tree/master/docker),
# which ship GDAL's Python bindings (the osgeo module) built against the exact
# libgdal version they bundle -- so there is no separate "gdal" extra to compile
# or version-match here, unlike a plain pip/pipx install (see
# docs/usage/installation.md).
ARG GDAL_VERSION=3.11.0

FROM ghcr.io/osgeo/gdal:ubuntu-small-${GDAL_VERSION} AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# --system-site-packages lets the venv see the base image's pre-built osgeo
# (GDAL) module instead of trying to build/install its own.
RUN python3 -m venv --system-site-packages /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /src
COPY . .
RUN python3 -m pip install --no-cache-dir -U pip setuptools wheel \
    && python3 -m pip install --no-cache-dir .

FROM ghcr.io/osgeo/gdal:ubuntu-small-${GDAL_VERSION} AS runtime

LABEL org.opencontainers.image.title="DicoGIS" \
      org.opencontainers.image.description="Create Excel/JSON inventories of geographic datasets from a folder tree or a PostGIS database." \
      org.opencontainers.image.source="https://github.com/Guts/DicoGIS" \
      org.opencontainers.image.licenses="Apache-2.0"

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin dicogis \
    && mkdir -p /data \
    && chown dicogis:dicogis /data

USER dicogis
WORKDIR /data

ENTRYPOINT ["dicogis-cli"]
CMD ["--help"]
