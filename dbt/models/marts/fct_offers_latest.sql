{{ config(
    engine='MergeTree()',
    order_by='(source_offer_id, observed_at)'
) }}

SELECT
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
FROM (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY source_offer_id
            ORDER BY observed_at DESC
        ) AS observation_rank
    FROM {{ ref('stg_offers_observations') }}
)
WHERE observation_rank = 1
