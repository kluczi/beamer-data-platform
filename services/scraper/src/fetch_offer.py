import httpx
import json
from time import sleep
from selectolax.parser import HTMLParser
from src.models import Offer
from datetime import datetime, timezone


MAX_FETCH_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504, 520}


def fetch_offer_html(url: str) -> str:
    headers = {
        "User-Agent": "...",
        "Accept": "...",
        "Accept-Language": "...",
    }
    with httpx.Client(headers=headers, timeout=20.0, follow_redirects=True) as client:
        for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
            response = client.get(url)

            if (
                response.status_code in RETRYABLE_STATUS_CODES
                and attempt < MAX_FETCH_ATTEMPTS
            ):
                sleep(attempt)
                continue

            response.raise_for_status()
            return response.text

    raise RuntimeError(f"Failed to fetch offer after {MAX_FETCH_ATTEMPTS} attempts: {url}")


"""extract data from script#__NEXT_DATA__ tag"""


def extract_next_data(html: str) -> dict:
    html_tree = HTMLParser(html)
    data_tag = html_tree.css_first("script#__NEXT_DATA__")
    data = data_tag.text()
    return json.loads(data)


def get_param(parameters: dict, key: str, field: str = "value") -> str | None:
    param = parameters.get(key)

    if not param:
        return None

    values = param.get("values")

    if not values:
        return None

    first_value = values[0]

    return first_value.get(field)


def get_advert(next_data: dict) -> dict:
    return next_data["props"]["pageProps"]["advert"]


def map_advert_to_offer(advert: dict, scrape_run_id: str) -> Offer:

    offer_id = advert["id"]
    url = advert["url"]
    title = advert["title"]
    price_amount = advert["price"]["value"]
    price_currency = advert["price"]["currency"]

    parameters = advert["parametersDict"]

    brand = get_param(parameters, "make", "label")
    model = get_param(parameters, "model", "label")
    year = get_param(parameters, "year", "value")
    mileage = get_param(parameters, "mileage", "value")
    fuel_type = get_param(parameters, "fuel_type", "value")
    transmission = get_param(parameters, "gearbox", "value")

    return Offer(
        source_offer_id=offer_id,
        url=url,
        title=title,
        brand=brand,
        model=model,
        year=int(year),
        mileage_km=int(mileage),
        fuel_type=fuel_type,
        transmission=transmission,
        price_amount=float(price_amount),
        price_currency=price_currency,
        observed_at=datetime.now(timezone.utc),
        scrape_run_id=scrape_run_id,
    )


def scrape_offer_from_listing(url: str, scrape_run_id: str) -> Offer:
    html_code = fetch_offer_html(url)
    next_data = extract_next_data(html_code)
    advert = get_advert(next_data)
    offer = map_advert_to_offer(advert, scrape_run_id)

    return offer
