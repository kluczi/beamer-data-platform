import os
import duckdb


POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]

MINIO_ROOT_USER = os.environ["MINIO_ROOT_USER"]
MINIO_ROOT_PASSWORD = os.environ["MINIO_ROOT_PASSWORD"]
MINIO_BUCKET = os.environ["MINIO_BUCKET"]


con = duckdb.connect()

con.execute("INSTALL ducklake; LOAD ducklake;")
con.execute("INSTALL postgres; LOAD postgres;")
con.execute("INSTALL httpfs; LOAD httpfs;")

con.execute(f"""
    CREATE OR REPLACE SECRET minio_secret (
        TYPE s3,
        PROVIDER config,
        KEY_ID '{MINIO_ROOT_USER}',
        SECRET '{MINIO_ROOT_PASSWORD}',
        REGION 'us-east-1',
        ENDPOINT 'minio:9000',
        URL_STYLE 'path',
        USE_SSL false
    );
""")

con.execute(f"""
    ATTACH 'ducklake:postgres:host=postgres port=5432 dbname={POSTGRES_DB} user={POSTGRES_USER} password={POSTGRES_PASSWORD}'
    AS beamer_lake
    (DATA_PATH 's3://{MINIO_BUCKET}/ducklake/');
""")

con.execute("USE beamer_lake;")

con.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

con.execute("""
    CREATE TABLE IF NOT EXISTS bronze.offers (
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
    INSERT INTO bronze.offers VALUES
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
    SELECT *
    FROM bronze.offers
    ORDER BY scraped_at DESC
""").fetchdf()
)
