import os

import httpx


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


def notify_scraper_succeeded(
    scrape_run_id: str,
    rows_loaded: int,
    duration_seconds: float,
    latest_offers: list[dict],
) -> None:
    if latest_offers:
        offer_lines = []
        for index, offer in enumerate(latest_offers[:10], start=1):
            title = (offer.get("title") or "Untitled offer").replace("\n", " ")
            title = title[:55]
            vehicle = " ".join(
                str(value)
                for value in (offer.get("brand"), offer.get("model"), offer.get("year"))
                if value not in (None, "")
            )
            price = " ".join(
                str(value)
                for value in (offer.get("price_amount"), offer.get("price_currency"))
                if value not in (None, "")
            ) or "price unavailable"
            mileage = offer.get("mileage_km")
            mileage_text = f"{mileage} km" if mileage is not None else "mileage unavailable"
            url = str(offer.get("url") or "")[:80]
            details = " | ".join(value for value in (vehicle, price, mileage_text) if value)
            offer_lines.append(f"{index}. {title} — {details}\n{url}".strip())
        offers_text = "\n".join(offer_lines)
    else:
        offers_text = "No offers found in this scrape run."

    send_discord_webhook(
        "\N{WHITE HEAVY CHECK MARK} Beamer scraper completed\n"
        f"Scrape run: `{scrape_run_id}`\n"
        f"Rows loaded into ClickHouse: {rows_loaded}\n"
        f"Duration: {duration_seconds:.1f}s\n\n"
        f"Latest offers:\n{offers_text}"
    )


def notify_scraper_failed(error: Exception, duration_seconds: float) -> None:
    error_message = str(error) or error.__class__.__name__
    send_discord_webhook(
        "\N{CROSS MARK} Beamer scraper failed\n"
        f"Error: `{error.__class__.__name__}: {error_message[:1000]}`\n"
        f"Duration: {duration_seconds:.1f}s"
    )
