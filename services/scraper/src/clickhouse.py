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
        conn.command(f"create database if not exists {database}")
        conn.command(
            f"""
            create table if not exists {database}.raw_offers_observations (
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
            engine = MergeTree
            partition by toYYYYMM(observed_at)
            order by (source_offer_id, observed_at)
            """
        )
        conn.command(
            f"""
            create table if not exists {database}.warehouse_loads (
                scrape_run_id String,
                loaded_at DateTime64(3, 'UTC'),
                rows_loaded UInt64
            )
            engine = ReplacingMergeTree
            order by scrape_run_id
            """
        )
        conn.command(
            f"""
            create table if not exists {database}.raw_currency_rates (
                effective_date Date,
                base_currency LowCardinality(String),
                quote_currency LowCardinality(String),
                rate_to_pln Decimal64(8),
                provider LowCardinality(String),
                source_table String,
                fetched_at DateTime64(3, 'UTC')
            )
            engine = ReplacingMergeTree(fetched_at)
            partition by toYYYYMM(effective_date)
            order by (effective_date, base_currency, quote_currency, provider)
            """
        )
    finally:
        conn.close()
