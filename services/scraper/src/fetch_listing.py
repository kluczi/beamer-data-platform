import os
import httpx
import json
from selectolax.parser import HTMLParser
from src.models import Offer
from datetime import datetime, timezone


EXTENSIONS = {
    "persistedQuery": {
        "sha256Hash": "249637cf7043dc3a315a8c7c4654da5ca30a6883a8bb3010b84be0bf3367e84f",
        "version": 1,
    }
}

URL = os.getenv("GRAPHQL_URL")


def build_variables(page: int = 1) -> dict:
    return {
        "filters": [
            {"name": "category_id", "value": "29"},
            {"name": "make_model_generation", "value": "porsche|911"},
            {"name": "filter_enum_leasing_concession", "value": "1"},
        ],
        "includeCepik": False,
        "includeFiltersCounters": False,
        "includeNewPromotedAds": False,
        "includePriceEvaluation": False,
        "includePromotedAds": False,
        "includeRatings": False,
        "includeSortOptions": False,
        "includeSuggestedFilters": False,
        "itemsPerPage": 9,
        "maxAge": 60,
        "page": page,
        "promotedInput": {},
    }


def fetch_listing_page(page: int = 1) -> dict:
    datadome_client_id = os.environ.get("DATADOME_CLIENT_ID")
    datadome_cookie = os.environ.get("DATADOME_COOKIE")

    headers = {
        "accept": "application/graphql-response+json, application/graphql+json, application/json",
        "referer": os.getenv("REFERER_URL"),
        "sitecode": "otomotopl",
        "user-agent": (
            "Mozilla/5.0 (Linux; Android 15; Pixel 9) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Mobile Safari/537.36"
        ),
    }

    if datadome_client_id:
        headers["x-datadome-clientid"] = datadome_client_id

    if datadome_cookie:
        headers["cookie"] = f"datadome={datadome_cookie}"

    params = {
        "operationName": "financingListingScreen",
        "variables": json.dumps(
            build_variables(page), separators=(",", ":"), ensure_ascii=False
        ),
        "extensions": json.dumps(EXTENSIONS, separators=(",", ":"), ensure_ascii=False),
    }

    with httpx.Client(headers=headers, timeout=30.0, follow_redirects=True) as client:
        response = client.get(URL, params=params)

    # print("status:", response.status_code)
    # print("content-type:", response.headers.get("content-type"))
    # print("preview:")
    # print(response.text[:1000])

    response.raise_for_status()
    return response.json()


def find_advert_search_output(obj):
    if isinstance(obj, dict):
        if obj.get("__typename") == "AdvertSearchOutput":
            return obj

        for value in obj.values():
            try:
                return find_advert_search_output(value)
            except ValueError:
                pass

    elif isinstance(obj, list):
        for item in obj:
            try:
                return find_advert_search_output(item)
            except ValueError:
                pass

    raise ValueError("Nie znaleziono AdvertSearchOutput")


def extract_offer_urls(data: dict) -> list[str]:
    search_output = find_advert_search_output(data)

    return [
        edge["node"]["url"]
        for edge in search_output.get("edges", [])
        if edge.get("node", {}).get("url")
    ]


def scrape_listing_urls() -> list[str]:
    all_urls = []
    for page in range(1, 5):
        data = fetch_listing_page(page)
        curr_page_urls = extract_offer_urls(data)
        all_urls.append(curr_page_urls)
    return all_urls
