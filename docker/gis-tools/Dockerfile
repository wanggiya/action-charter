FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python3 -m pip install --break-system-packages --no-cache-dir ".[gis]"

RUN useradd --create-home --uid 10001 geoagent
USER geoagent
WORKDIR /workspace

