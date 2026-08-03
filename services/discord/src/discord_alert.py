import os
import time

import clickhouse_connect
import httpx


def get_latest_offers() -> list[dict]:
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
        database=os.getenv("CLICKHOUSE_DB", "beamer_warehouse"),
    )
    try:
        result = client.query(
            """
            SELECT title, brand, model, year, mileage_km, price_amount,
                   price_currency, url, observed_at
            FROM raw_offers_observations
            ORDER BY observed_at DESC
            LIMIT 10
            """
        )
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    finally:
        client.close()


def format_latest_offers_message(rows: list[dict]) -> str:
    if not rows:
        return "No offers have been observed yet."

    offers = ["Top 10 latest offers"]
    for index, row in enumerate(rows, start=1):
        vehicle = " ".join(
            str(value) for value in (row["brand"], row["model"], row["year"])
            if value is not None
        )
        price = " ".join(
            str(value) for value in (row["price_amount"], row["price_currency"])
            if value is not None
        )
        mileage = f" | {row['mileage_km']} km" if row["mileage_km"] is not None else ""
        offer = f"{index}. {row['title']} — {vehicle}{mileage} | {price}\n{row['url']}"
        if len("\n".join([*offers, offer])) > 2000:
            break
        offers.append(offer)

    return "\n".join(offers)


def send_discord_webhook(content: str) -> None:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL must be set")

    response = httpx.post(
        webhook_url,
        json={"content": content},
        timeout=10,
    )
    response.raise_for_status()


def main():
    interval_seconds = int(os.getenv("DISCORD_ALERT_INTERVAL_SECONDS", "86400"))
    while True:
        send_discord_webhook(format_latest_offers_message(get_latest_offers()))
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
