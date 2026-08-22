FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install \
    --no-cache-dir \
    ".[mcp,workflow]"

RUN useradd \
    --create-home \
    --uid 10001 \
    geoagent

USER geoagent

WORKDIR /workspace/snakemake-exports

ENTRYPOINT ["snakemake"]
CMD ["--help"]

