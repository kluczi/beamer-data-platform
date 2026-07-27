from src.load_into_datalake import get_connection, main as load_into_datalake
from src.clickhouse import initialize_warehouse
from src.load_into_warehouse import load_pending_scrape_runs


def main():
    initialize_warehouse()
    load_into_datalake()
    conn = get_connection()
    try:
        rows_loaded = load_pending_scrape_runs(conn)
        print(f"Loaded {rows_loaded} row(s) from DuckLake into ClickHouse.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
