import os
import httpx

from datetime import datetime, timezone


def format_new_offer_message(row: dict) -> str:
    return (
        f"new offer arrived!\n"
        f"{row['title']}\n"
        f"{row['brand']} {row['model']} | {row['year']} | {row['mileage_km']} km\n"
        f"price: {row['price_amount']} {row['price_currency']}\n"
        f"{row['url']}"
    )


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
    row = {
        "title": "Porsche 911",
        "brand": "Porsche",
        "model": "911",
        "year": "2024",
        "mileage_km": "50000",
        "price_amount": "5000000",
        "price_currency": "EUR",
        "url": "test",
    }

    message = format_new_offer_message(row)
    send_discord_webhook(message)


if __name__ == "__main__":
    main()
