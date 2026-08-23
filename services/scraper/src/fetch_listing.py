import os
import httpx
import json


EXTENSIONS = {
    "persistedQuery": {
        "sha256Hash": "249637cf7043dc3a315a8c7c4654da5ca30a6883a8bb3010b84be0bf3367e84f",
        "version": 1,
    }
}

URL = os.getenv("GRAPHQL_URL")


def get_make_model_generations() -> list[str]:
    configured_targets = os.getenv(
        "SCRAPE_TARGETS",
        "porsche:911",
    )
    targets = []

    for configured_target in configured_targets.split(","):
        configured_target = configured_target.strip()
        if not configured_target:
            continue

        try:
            make, model = configured_target.split(":", maxsplit=1)
        except ValueError as error:
            raise ValueError(
                "Each SCRAPE_TARGETS entry must use make:model format"
            ) from error

        if not make or not model:
            raise ValueError(
                "Each SCRAPE_TARGETS entry must include both make and model"
            )

        targets.append(f"{make}|{model}")

    if not targets:
        raise ValueError("SCRAPE_TARGETS must contain at least one target")

    return targets


def build_variables(
    page: int = 1,
    make_model_generation: str | None = None,
) -> dict:
    if make_model_generation is None:
        make_model_generation = get_make_model_generations()[0]

    return {
        "filters": [
            {"name": "category_id", "value": "29"},
            {
                "name": "make_model_generation",
                "value": make_model_generation,
            },
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


def fetch_listing_page(
    page: int = 1,
    make_model_generation: str | None = None,
) -> dict:
    datadome_client_id = os.environ.get("DATADOME_CLIENT_ID")
    datadome_cookie = os.environ.get("DATADOME_COOKIE")

    headers = {
        "accept": "application/graphql-response+json, application/graphql+json, application/json",
        "referer": os.getenv("REFERER_URL"),
        "sitecode": os.getenv("SITECODE"),
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
            build_variables(page, make_model_generation),
            separators=(",", ":"),
            ensure_ascii=False,
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


def count_total_pages(data: dict) -> int:
    search_output = find_advert_search_output(data)
    total_count = search_output["totalCount"]
    page_size = search_output["pageInfo"]["pageSize"]
    total_pages = (total_count + page_size - 1) // page_size
    return total_pages


def scrape_listing_urls() -> list[str]:
    all_urls = []
    seen_urls = set()

    for target in get_make_model_generations():
        data = fetch_listing_page(page=1, make_model_generation=target)
        total_pages = count_total_pages(data)

        for url in extract_offer_urls(data):
            if url not in seen_urls:
                seen_urls.add(url)
                all_urls.append(url)

        for page in range(2, total_pages + 1):
            data = fetch_listing_page(page, make_model_generation=target)
            for url in extract_offer_urls(data):
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_urls.append(url)

    return all_urls
