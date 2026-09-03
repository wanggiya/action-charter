FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install \
    --no-cache-dir \
    ".[mcp,workflow]"

ARG GEOAGENT_UID=1000
ARG GEOAGENT_GID=1000

RUN groupadd \
    --gid "${GEOAGENT_GID}" \
    geoagent \
    && useradd \
    --create-home \
    --uid "${GEOAGENT_UID}" \
    --gid "${GEOAGENT_GID}" \
    geoagent

USER geoagent

WORKDIR /workspace/snakemake-exports

ENTRYPOINT ["snakemake"]
CMD ["--help"]
