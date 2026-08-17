select
    source_offer_id,
    url,
    title,
    brand,
    model,
    year,
    mileage_km,
    fuel_type,
    transmission,
    price_amount,
    price_currency,
    observed_at,
    scrape_run_id
from {{ source('raw', 'offers_observations') }}
