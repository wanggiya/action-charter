FROM python:3.11-slim
LABEL org.actioncharter.worker.protocol="dataset-profile-v1"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
COPY geoagent_harness /app/geoagent_harness
RUN mkdir -p /job/data/input /scratch && chmod 755 /job /job/data /job/data/input /scratch
USER 65534:65534
WORKDIR /scratch
ENTRYPOINT ["python", "-I", "-B", "-c", "import sys;sys.path.insert(0,'/app');from geoagent_harness.workspaces.sandbox.worker import main;main()"]
