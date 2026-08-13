{{ config(
    engine='MergeTree()',
    order_by='offer_key'
) }}

WITH ranked_offer_observations AS (
    SELECT
        source_offer_id,
        url,
        title,
        brand,
        model,
        year,
        fuel_type,
        transmission,
        observed_at,
        row_number() OVER (
            PARTITION BY source_offer_id
            ORDER BY observed_at DESC
        ) AS observation_rank
    FROM {{ ref('stg_raw__offers_observations') }}
), offer_history AS (
    SELECT
        source_offer_id,
        min(observed_at) AS first_observed_at,
        max(observed_at) AS last_observed_at,
        count() AS observation_count
    FROM {{ ref('stg_raw__offers_observations') }}
    GROUP BY source_offer_id
)

SELECT
    ranked_offer_observations.source_offer_id AS offer_key,
    ranked_offer_observations.url,
    ranked_offer_observations.title,
    ranked_offer_observations.brand,
    ranked_offer_observations.model,
    ranked_offer_observations.year,
    ranked_offer_observations.fuel_type,
    ranked_offer_observations.transmission,
    offer_history.first_observed_at,
    offer_history.last_observed_at,
    offer_history.observation_count
FROM ranked_offer_observations
JOIN offer_history
    ON ranked_offer_observations.source_offer_id = offer_history.source_offer_id
WHERE ranked_offer_observations.observation_rank = 1
