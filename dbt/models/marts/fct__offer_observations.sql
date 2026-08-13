{{ config(
    engine='MergeTree()',
    order_by='(offer_key, observed_at)'
) }}

SELECT
    source_offer_id AS offer_key,
    observed_at,
    price_amount,
    price_currency,
    mileage_km,
    scrape_run_id
FROM {{ ref('stg_raw__offers_observations') }}
