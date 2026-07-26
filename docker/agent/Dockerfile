FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY agents ./agents
RUN python -m pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 geoagent
USER geoagent

ENTRYPOINT ["geoagent"]
CMD ["--help"]

