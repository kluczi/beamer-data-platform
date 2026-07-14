from dataclasses import dataclass


@dataclass
class Offer:
    source_offer_id: str
    url: str
    title: str
    brand: str
    model: str
    year: int
    mileage_km: int
    fuel_type: str
    transmission: str
    price_amount: float
    price_currency: str
    observed_at: str
