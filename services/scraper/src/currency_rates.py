import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

import clickhouse_connect
import httpx


NBP_API_URL = "https://api.nbp.pl/api/exchangerates/rates/a/{currency}/"
CURRENCIES = ("EUR", "USD")


@dataclass(frozen=True)
class CurrencyRate:
    effective_date: date
    base_currency: str
    quote_currency: str
    rate_to_pln: Decimal
    provider: str
    source_table: str
    fetched_at: datetime


def fetch_currency_rate(client: httpx.Client, currency: str) -> CurrencyRate:
    currency = currency.upper()
    url = NBP_API_URL.format(currency=currency.lower())
    response = client.get(url, headers={"Accept": "application/json"})
    response.raise_for_status()
    payload = json.loads(response.text, parse_float=Decimal)
    latest_rate = payload["rates"][-1]

    if payload["code"].upper() != currency:
        raise ValueError(f"NBP returned {payload['code']} for requested {currency}")
    if latest_rate["mid"] <= 0:
        raise ValueError(f"NBP returned a non-positive {currency}/PLN rate")

    return CurrencyRate(
        effective_date=date.fromisoformat(latest_rate["effectiveDate"]),
        base_currency=currency,
        quote_currency="PLN",
        rate_to_pln=latest_rate["mid"],
        provider="NBP",
        source_table=latest_rate["no"],
        fetched_at=datetime.now(timezone.utc),
    )


def get_clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "clickhouse"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
    )


def initialize_currency_rates_table(client) -> str:
    database = os.getenv("CLICKHOUSE_DB", "beamer_warehouse")
    client.command(f"create database if not exists {database}")
    client.command(
        f"""
        create table if not exists {database}.raw_currency_rates (
            effective_date Date,
            base_currency LowCardinality(String),
            quote_currency LowCardinality(String),
            rate_to_pln Decimal64(8),
            provider LowCardinality(String),
            source_table String,
            fetched_at DateTime64(3, 'UTC')
        )
        engine = ReplacingMergeTree(fetched_at)
        partition by toYYYYMM(effective_date)
        order by (effective_date, base_currency, quote_currency, provider)
        """
    )
    return f"{database}.raw_currency_rates"


def load_currency_rates() -> None:
    with httpx.Client(timeout=10.0, follow_redirects=True) as http_client:
        rates = [fetch_currency_rate(http_client, currency) for currency in CURRENCIES]

    clickhouse_client = get_clickhouse_client()
    try:
        table = initialize_currency_rates_table(clickhouse_client)
        clickhouse_client.insert(
            table,
            [
                [
                    rate.effective_date,
                    rate.base_currency,
                    rate.quote_currency,
                    rate.rate_to_pln,
                    rate.provider,
                    rate.source_table,
                    rate.fetched_at,
                ]
                for rate in rates
            ],
            column_names=[
                "effective_date",
                "base_currency",
                "quote_currency",
                "rate_to_pln",
                "provider",
                "source_table",
                "fetched_at",
            ],
        )
    finally:
        clickhouse_client.close()
