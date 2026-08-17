{{ config(
    engine='MergeTree()',
    order_by='(offer_key, observed_at)'
) }}

select
    source_offer_id as offer_key,
    observed_at,
    price_amount,
    price_currency,
    mileage_km,
    scrape_run_id
from {{ ref('stg_raw__offers_observations') }}
