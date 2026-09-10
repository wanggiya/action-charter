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

RUN set -eux; \
    if ! getent group "${GEOAGENT_GID}" >/dev/null; then \
        groupadd --gid "${GEOAGENT_GID}" geoagent; \
    fi; \
    existing_user="$(getent passwd "${GEOAGENT_UID}" | cut -d: -f1 || true)"; \
    if [ -n "${existing_user}" ]; then \
        usermod \
            --login geoagent \
            --home /home/geoagent \
            --move-home \
            --gid "${GEOAGENT_GID}" \
            "${existing_user}"; \
    else \
        useradd \
            --create-home \
            --uid "${GEOAGENT_UID}" \
            --gid "${GEOAGENT_GID}" \
            geoagent; \
    fi

USER geoagent
WORKDIR /workspace
