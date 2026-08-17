import sys
from time import monotonic

from src.load_into_datalake import get_connection, main as load_into_datalake
from src.clickhouse import initialize_warehouse
from src.load_into_warehouse import load_pending_scrape_runs
from src.notifications import notify_scraper_failed, notify_scraper_succeeded


def main():
    started_at = monotonic()
    try:
        initialize_warehouse()
        scrape_run_id = load_into_datalake()
        conn = get_connection()
        try:
            latest_offers = [
                {
                    "title": row[0],
                    "brand": row[1],
                    "model": row[2],
                    "year": row[3],
                    "mileage_km": row[4],
                    "price_amount": row[5],
                    "price_currency": row[6],
                    "url": row[7],
                }
                for row in conn.execute(
                    """
                    select title, brand, model, year, mileage_km,
                           price_amount, price_currency, url
                    from beamer_lake.raw.offers_observations
                    where scrape_run_id = ?
                    order by observed_at desc
                    limit 10
                    """,
                    [scrape_run_id],
                ).fetchall()
            ]
            rows_loaded = load_pending_scrape_runs(conn)
            print(f"Loaded {rows_loaded} row(s) from DuckLake into ClickHouse.")
        finally:
            conn.close()
    except Exception as error:
        duration_seconds = monotonic() - started_at
        try:
            notify_scraper_failed(error, duration_seconds)
        except Exception as notification_error:
            print(
                f"Failed to send Discord failure alert: {notification_error}",
                file=sys.stderr,
            )
        raise

    notify_scraper_succeeded(
        scrape_run_id,
        rows_loaded,
        monotonic() - started_at,
        latest_offers,
    )


if __name__ == "__main__":
    main()
