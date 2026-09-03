FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install --no-cache-dir ".[mcp]"

RUN useradd \
    --create-home \
    --uid 10001 \
    geoagent

USER geoagent

ENTRYPOINT ["geoagent"]
CMD ["--help"]
