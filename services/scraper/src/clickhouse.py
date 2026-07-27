import os

import clickhouse_connect


def initialize_warehouse() -> None:
    database = os.getenv("CLICKHOUSE_DB", "beamer_warehouse")
    conn = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
    )

    try:
        conn.command(f"CREATE DATABASE IF NOT EXISTS {database}")
        conn.command(
            f"""
            CREATE TABLE IF NOT EXISTS {database}.raw_offers_observations (
                        source_offer_id String,
                        url String,
                        title String,
                        brand Nullable(String),
                        model Nullable(String),
                        year Nullable(Int32),
                        mileage_km Nullable(Int32),
                        fuel_type Nullable(String),
                        transmission Nullable(String),
                        price_amount Nullable(Float64),
                        price_currency Nullable(String),
                        observed_at DateTime64(3, 'UTC'),
                        scrape_run_id String
                    )
            ENGINE = MergeTree
            PARTITION BY toYYYYMM(observed_at)
            ORDER BY (source_offer_id, observed_at)
            """
        )
        conn.command(
            f"""
            CREATE TABLE IF NOT EXISTS {database}.warehouse_loads (
                scrape_run_id String,
                loaded_at DateTime64(3, 'UTC'),
                rows_loaded UInt64
            )
            ENGINE = ReplacingMergeTree
            ORDER BY scrape_run_id
            """
        )
    finally:
        conn.close()
