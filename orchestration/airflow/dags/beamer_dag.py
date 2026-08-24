from datetime import datetime
from airflow.sdk import dag, task

from services.dbt.src.run_dbt import build_dbt
from services.scraper.src.run_scraper_loader import run_scraper_and_loader
from services.evidence.src.run_evidence import build_evidence_sources
from services.scraper.src.currency_rates import load_currency_rates

DAG_ID = "beamer_pipeline"


@dag(
    dag_id=DAG_ID,
    schedule="@daily",
    start_date=datetime(2026, 8, 20),
    catchup=False,
    max_active_runs=1,
    tags=["beamer"],
)
def beamer_pipeline():

    @task
    def ingest_source_data() -> None:
        run_scraper_and_loader()

    @task
    def update_currency_rates() -> None:
        load_currency_rates()

    @task
    def transform_warehouse() -> None:
        build_dbt()

    @task
    def refresh_evidence_sources() -> None:
        build_evidence_sources()

    ingestion = ingest_source_data()
    currency_rates = update_currency_rates()
    transformations = transform_warehouse()
    reporting = refresh_evidence_sources()

    [ingestion, currency_rates] >> transformations >> reporting


beamer_pipeline()
