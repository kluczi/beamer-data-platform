FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir \
    "dbt-core>=1.10,<1.11" \
    "dbt-clickhouse>=1.10,<1.11"

ENTRYPOINT ["dbt"]
