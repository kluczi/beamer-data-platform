{{ config(
    engine='MergeTree()',
    order_by='offer_key'
) }}

WITH ranked_offers AS (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY source_offer_id
            ORDER BY observed_at DESC
        ) AS observation_rank
    FROM {{ ref('stg_offers_observations') }}
), offer_history AS (
    SELECT
        source_offer_id,
        min(observed_at) AS first_observed_at,
        max(observed_at) AS last_observed_at,
        count() AS observation_count
    FROM {{ ref('stg_offers_observations') }}
    GROUP BY source_offer_id
)

SELECT
    ranked_offers.source_offer_id AS offer_key,
    ranked_offers.url,
    ranked_offers.title,
    ranked_offers.brand,
    ranked_offers.model,
    ranked_offers.year,
    ranked_offers.fuel_type,
    ranked_offers.transmission,
    offer_history.first_observed_at,
    offer_history.last_observed_at,
    offer_history.observation_count
FROM ranked_offers
JOIN offer_history
    ON ranked_offers.source_offer_id = offer_history.source_offer_id
WHERE ranked_offers.observation_rank = 1
