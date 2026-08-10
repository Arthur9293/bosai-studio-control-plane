FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir .

CMD ["python", "-m", "bosai_studio.cloud_run_runtime_app"]
