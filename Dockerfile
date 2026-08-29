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

# Runtime dependency versions below are pinned exactly (matching what pip
# resolves from pyproject.toml's ranges at the time of writing) so the image
# is reproducible instead of re-resolving floating ranges on every build.
# Regenerate by rebuilding the image and copying the versions pip resolves.
WORKDIR /src
COPY . .
RUN python3 -m pip install --no-cache-dir \
        pip==26.2.1 \
        setuptools==84.0.0 \
        wheel==0.48.0 \
        annotated-doc==0.0.5 \
        certifi==2026.7.22 \
        charset-normalizer==3.5.1 \
        et-xmlfile==2.0.0 \
        idna==3.19 \
        jeepney==0.9.0 \
        loguru==0.6.0 \
        lxml==6.1.2 \
        markdown-it-py==4.2.0 \
        mdurl==0.1.2 \
        notify-py==0.3.43 \
        numpy==2.5.2 \
        openpyxl==3.1.5 \
        pgserviceparser==2.5.0 \
        pygments==2.21.0 \
        requests==2.34.2 \
        rich==15.0.0 \
        shellingham==1.5.4 \
        typer==0.27.2 \
        urllib3==2.7.0 \
    && python3 -m pip install --no-cache-dir --no-deps . \
    && python3 -c "import dicogis.cli.main" \
    && find /opt/venv/lib/*/site-packages/dicogis -maxdepth 1

FROM ghcr.io/osgeo/gdal:ubuntu-small-${GDAL_VERSION} AS runtime

LABEL org.opencontainers.image.title="DicoGIS" \
      org.opencontainers.image.description="Create Excel/JSON inventories of geographic datasets from a folder tree or a PostGIS database." \
      org.opencontainers.image.source="https://github.com/Guts/DicoGIS" \
      org.opencontainers.image.licenses="Apache-2.0"

RUN useradd --create-home --shell /usr/sbin/nologin dicogis \
    && mkdir -p /data \
    && chown dicogis:dicogis /data

# --chown so the venv is readable/executable by the non-root `dicogis` user
# this image runs as (COPY --from otherwise preserves the builder's root
# ownership, which the base image's umask can leave too restrictive for
# a different user to traverse).
COPY --chown=dicogis:dicogis --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Build-time sanity check, as the user the image actually runs as.
USER dicogis
RUN python3 -c "import dicogis.cli.main"

WORKDIR /data

ENTRYPOINT ["dicogis-cli"]
CMD ["--help"]
