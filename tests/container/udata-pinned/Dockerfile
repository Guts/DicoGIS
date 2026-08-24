# Minimal, version-pinned uData image used to test DicoGIS's publish command
# against a specific uData major version in CI.
#
# The official `udata/udata:latest` Docker Hub image doesn't expose which
# exact `udata` PyPI release it bundles (and its "last pushed" metadata lags
# far behind uData's actual release cadence), so it can't be trusted to
# represent a known major version. This image instead builds from the
# official `udata/system` base (same base the real udata/udata image is
# built from) and pip-installs a specific `udata==${UDATA_VERSION}` release,
# giving a reproducible target for each major version tested.
#
# It intentionally skips uwsgi/static assets/themes (front, gouvfr...): the
# CI test only exercises the core REST API (dataset creation/listing), for
# which the plain `udata serve` dev server is enough.
ARG PYTHON_BASE_TAG=py3.11
FROM udata/system:${PYTHON_BASE_TAG}

ARG UDATA_VERSION

RUN test -n "${UDATA_VERSION}" || (echo "UDATA_VERSION build-arg is required" >&2 && exit 1)

RUN pip install --no-cache-dir "udata==${UDATA_VERSION}"

RUN mkdir -p /udata/fs
COPY udata.cfg /udata/udata.cfg
WORKDIR /udata
ENV UDATA_SETTINGS=/udata/udata.cfg

EXPOSE 7000

ENTRYPOINT ["udata"]
CMD ["serve", "--host", "0.0.0.0"]
