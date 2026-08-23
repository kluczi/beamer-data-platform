import os
import sys
import pandas as pd
import duckdb
import httpx
from src.fetch_listing import scrape_listing_urls
from src.fetch_offer import scrape_offer_from_listing
from src.models import Offer
import uuid


def get_connection():
    conn = duckdb.connect("pipeline.duckdb")

    postgres_host = os.getenv("POSTGRES_HOST", "postgres")
    postgres_user = os.environ["POSTGRES_USER"]
    postgres_password = os.environ["POSTGRES_PASSWORD"]
    postgres_db = os.environ["POSTGRES_DB"]

    minio_root_user = os.environ["MINIO_ROOT_USER"]
    minio_root_password = os.environ["MINIO_ROOT_PASSWORD"]
    minio_bucket = os.environ["MINIO_BUCKET"]
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")

    conn.sql("install ducklake; load ducklake;")
    conn.sql("install postgres; load postgres;")
    conn.sql("install httpfs; load httpfs;")

    conn.sql(f"""
        create secret if not exists minio_secret (
            type s3,
            provider config,
            key_id '{minio_root_user}',
            secret '{minio_root_password}',
            region 'eu-central-1',
            endpoint '{minio_endpoint}',
            url_style 'path',
            use_ssl false
        );
    """)

    conn.sql(f"""
        attach 'ducklake:postgres:host={postgres_host} port=5432 dbname={postgres_db} user={postgres_user} password={postgres_password}'
        as beamer_lake
        (data_path 's3://{minio_bucket}/ducklake/');
    """)

    conn.sql("use beamer_lake;")

    return conn


def create_raw_schema(conn):
    conn.sql("""
        create schema if not exists raw;
    """)


def create_observed_table(conn):
    conn.sql("""
        create table if not exists beamer_lake.raw.offers_observations (
            source_offer_id VARCHAR,
            url VARCHAR,
            title VARCHAR,
            brand VARCHAR,
            model VARCHAR,
            year INTEGER,
            mileage_km INTEGER,
            fuel_type VARCHAR,
            transmission VARCHAR,
            price_amount DOUBLE,
            price_currency VARCHAR,
            observed_at TIMESTAMP,
            scrape_run_id VARCHAR
        );
    """)


def load_offers(conn, batch: list[Offer]) -> None:
    if not batch:
        return
    rows = [offer_to_row(o) for o in batch]
    df = pd.DataFrame(rows)  # make table like in sql or excel
    conn.register("offers_batch", df)  # make temporary table from data frame
    conn.sql("""
        insert into beamer_lake.raw.offers_observations
        select
            source_offer_id,
            url,
            title,
            brand,
            model,
            year,
            mileage_km,
            fuel_type,
            transmission,
            price_amount,
            price_currency,
            observed_at,
            scrape_run_id
        from offers_batch
    """)
    conn.unregister("offers_batch")


def offer_to_row(offer: Offer) -> dict:
    return {
        "source_offer_id": offer.source_offer_id,
        "url": offer.url,
        "title": offer.title,
        "brand": offer.brand,
        "model": offer.model,
        "year": offer.year,
        "mileage_km": offer.mileage_km,
        "fuel_type": offer.fuel_type,
        "transmission": offer.transmission,
        "price_amount": offer.price_amount,
        "price_currency": offer.price_currency,
        "observed_at": offer.observed_at,
        "scrape_run_id": offer.scrape_run_id,
    }


def scrape_and_load_offers(conn) -> str:
    create_raw_schema(conn)
    create_observed_table(conn)
    scrape_run_id = str(uuid.uuid4())
    BATCH_SIZE = 100
    batch = []
    urls = scrape_listing_urls()
    for idx, url in enumerate(urls):
        try:
            offer = scrape_offer_from_listing(url, scrape_run_id)
        except (
            httpx.HTTPError,
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            print(f"Skipping offer {url}: {error}", file=sys.stderr)
            continue

        batch.append(offer)
        if len(batch) >= BATCH_SIZE:
            load_offers(conn, batch)
            batch.clear()

    if batch:
        load_offers(conn, batch)
    return scrape_run_id


def main():
    conn = get_connection()

    try:
        return scrape_and_load_offers(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
