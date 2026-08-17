import os
import duckdb


POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]

MINIO_ROOT_USER = os.environ["MINIO_ROOT_USER"]
MINIO_ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]
MINIO_BUCKET = os.environ["MINIO_BUCKET"]


con = duckdb.connect()

con.execute("install ducklake; load ducklake;")
con.execute("install postgres; load postgres;")
con.execute("install httpfs; load httpfs;")

con.execute(f"""
    create or replace secret minio_secret (
        type s3,
        provider config,
        key_id '{MINIO_ROOT_USER}',
        secret '{MINIO_ROOT_PASSWORD}',
        region 'us-east-1',
        endpoint 'minio:9000',
        url_style 'path',
        use_ssl false
    );
""")

con.execute(f"""
    attach 'ducklake:postgres:host=postgres port=5432 dbname={POSTGRES_DB} user={POSTGRES_USER} password={POSTGRES_PASSWORD}'
    as beamer_lake
    (data_path 's3://{MINIO_BUCKET}/ducklake/');
""")

con.execute("use beamer_lake;")

con.execute("create schema if not exists bronze;")

con.execute("""
    create table if not exists bronze.offers (
        source VARCHAR,
        source_offer_id VARCHAR,
        brand VARCHAR,
        model VARCHAR,
        year INTEGER,
        mileage_km INTEGER,
        price_amount DOUBLE,
        price_currency VARCHAR,
        scraped_at TIMESTAMP
    );
""")

con.execute("""
    insert into bronze.offers values
    (
        'demo',
        'demo-001',
        'BMW',
        '3 Series',
        2021,
        73000,
        31900.0,
        'EUR',
        now()
    );
""")

print(
    con.execute("""
    select *
    from bronze.offers
    order by scraped_at desc
""").fetchdf()
)
