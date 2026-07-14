from src.fetch_offer import scrape_offers_from_listing
from src.fetch_listing import scrape_listing_urls


def main():
    urls = scrape_listing_urls()
    for url in urls:
        print(f"{url}\n")
    offers = []
    for url in urls:
        offers.append(scrape_offers_from_listing(url))
    for offer in offers:
        print(f"{offer}\n")


if __name__ == "__main__":
    main()
