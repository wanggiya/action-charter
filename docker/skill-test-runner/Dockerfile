FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY docker/skill-test-runner/run_candidate_tests.py \
    /app/run_candidate_tests.py

RUN apt-get update \
    && apt-get install \
        --yes \
        --no-install-recommends \
        libexpat1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install \
    --no-cache-dir \
    ".[gis]" \
    "pytest>=8.2,<9"

RUN groupadd \
    --gid 10001 \
    geoagent \
    && useradd \
    --create-home \
    --uid 10001 \
    --gid 10001 \
    geoagent

USER geoagent

ENTRYPOINT ["python", "/app/run_candidate_tests.py"]

CMD ["/candidate/tests", "-q", "--disable-warnings", "-p", "no:cacheprovider"]

