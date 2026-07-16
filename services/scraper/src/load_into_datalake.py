import os
import pandas as pd
import duckdb
from src.fetch_listing import scrape_listing_urls
from src.models import Offer


def get_connection():
    conn = duckdb.connect("pipeline.duckdb")

    postgres_user = os.environ["POSTGRES_USER"]
    postgres_password = os.environ["POSTGRES_PASSWORD"]
    postgres_db = os.environ["POSTGRES_DB"]

    minio_root_user = os.environ["MINIO_ROOT_USER"]
    minio_root_password = os.environ["MINIO_ROOT_PASSWORD"]
    minio_bucket = os.environ["MINIO_BUCKET"]

    conn.sql("INSTALL ducklake; LOAD ducklake;")
    conn.sql("INSTALL postgres; LOAD postgres;")
    conn.sql("INSTALL httpfs; LOAD httpfs;")

    conn.sql(f"""
        IF NOT EXISTS CREATE SECRET minio_secret (
            TYPE s3,
            PROVIDER config,
            KEY_ID '{minio_root_user}',
            SECRET '{minio_root_password}',
            REGION 'eu-central-1',
            ENDPOINT 'minio:9000',
            URL_STYLE 'path',
            USE_SSL false
        );
    """)

    conn.sql(f"""
        ATTACH 'ducklake:postgres:host=postgres port=5432 dbname={postgres_db} user={postgres_user} password={postgres_password}'
        AS beamer_lake
        (DATA_PATH 's3://{minio_bucket}/ducklake/');
    """)

    conn.sql("USE beamer_lake;")

    return conn


def create_observed_table(conn):
    conn.sql("""
        IF NOT EXISTS CREATE TABLE lake.raw.otomoto_offer_observations (
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
    df = pd.DataFrame(rows)  # make table like in sql
    conn.register("offers_batch", df)  # make temporary table from data frame
    conn.sql("""
        INSERT INTO lake.raw.otomoto_offers_observations
        SELECT
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
            observed_at
        FROM offers_batch
    """)
    conn.unregister("offers_batch", df)


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
    }


def batch_urls(conn, urls: list[str]):
    BATCH_SIZE = 100
    batch = []
    for url in urls:
        batch.append(url)
    if len(batch >= BATCH_SIZE):
        load_offers(conn, batch)
        batch.clear()
    if batch:
        load_offers(conn, batch)


def scrape_and_load_offers(conn) -> None:
    pass
