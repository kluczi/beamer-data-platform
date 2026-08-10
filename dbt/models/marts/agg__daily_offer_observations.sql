{{ config(
    engine='MergeTree()',
    order_by='observation_date'
) }}

SELECT
    toDate(observed_at) AS observation_date,
    count() AS observation_count,
    uniqExact(offer_key) AS distinct_offer_count,
    avg(price_amount) AS average_price_amount
FROM {{ ref('fct__offer_observations') }}
GROUP BY observation_date
