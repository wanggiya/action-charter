FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
# RUN python3 -m pip install --break-system-packages --no-cache-dir ".[gis]"
RUN python3 -m pip install \
    --break-system-packages \
    --no-cache-dir ".[gis,mcp]"

ARG GEOAGENT_UID=1000
ARG GEOAGENT_GID=1000

RUN mkdir -p /home/geoagent \
    && chown "${GEOAGENT_UID}:${GEOAGENT_GID}" /home/geoagent

ENV HOME=/home/geoagent

USER ${GEOAGENT_UID}:${GEOAGENT_GID}
WORKDIR /workspace
