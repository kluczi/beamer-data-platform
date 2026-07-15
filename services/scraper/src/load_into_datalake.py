import os

import duckdb


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
        CREATE OR REPLACE SECRET minio_secret (
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
