import os
from datetime import datetime, timezone

import clickhouse_connect
import duckdb


COLUMNS = [
    "source_offer_id",
    "url",
    "title",
    "brand",
    "model",
    "year",
    "mileage_km",
    "fuel_type",
    "transmission",
    "price_amount",
    "price_currency",
    "observed_at",
    "scrape_run_id",
]
BATCH_SIZE = 1_000


def get_clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
    )


def load_scrape_run(conn: duckdb.DuckDBPyConnection, scrape_run_id: str) -> int:
    database = os.getenv("CLICKHOUSE_DB", "beamer_warehouse")
    table = f"{database}.raw_offers_observations"
    loads_table = f"{database}.warehouse_loads"
    client = get_clickhouse_client()

    try:
        already_loaded = client.query(
            f"select count() from {loads_table} where scrape_run_id = {{run_id:String}}",
            parameters={"run_id": scrape_run_id},
        ).result_rows[0][0]
        if already_loaded:
            return 0

        cursor = conn.execute(
            """
            select source_offer_id, url, title, brand, model, year, mileage_km,
                   fuel_type, transmission, price_amount, price_currency,
                   observed_at, scrape_run_id
            from beamer_lake.raw.offers_observations
            where scrape_run_id = ?
            order by source_offer_id
            """,
            [scrape_run_id],
        )

        rows_loaded = 0
        while rows := cursor.fetchmany(BATCH_SIZE):
            client.insert(table, rows, column_names=COLUMNS)
            rows_loaded += len(rows)

        client.insert(
            loads_table,
            [[scrape_run_id, datetime.now(timezone.utc), rows_loaded]],
            column_names=["scrape_run_id", "loaded_at", "rows_loaded"],
        )
        return rows_loaded
    finally:
        client.close()


def load_pending_scrape_runs(conn: duckdb.DuckDBPyConnection) -> int:
    scrape_run_ids = conn.execute(
        """
        select distinct scrape_run_id
        from beamer_lake.raw.offers_observations
        order by scrape_run_id
        """
    ).fetchall()

    return sum(
        load_scrape_run(conn, scrape_run_id) for (scrape_run_id,) in scrape_run_ids
    )
