FROM apache/airflow:3.3.1-python3.12

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=airflow:0 services /opt/beamer/services
COPY --chown=airflow:0 dbt /opt/beamer/dbt

USER airflow

RUN pip install --no-cache-dir \
    /opt/beamer/services/scraper \
    "python-dotenv>=1.0,<2" \
    "dbt-core>=1.10,<1.11" \
    "dbt-clickhouse>=1.10,<1.11"

RUN npm --prefix /opt/beamer/dbt/reports ci

ENV PYTHONPATH=/opt/beamer
WORKDIR /opt/beamer
