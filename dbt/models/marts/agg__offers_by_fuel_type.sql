{{ config(
    engine='MergeTree()',
    order_by='fuel_type'
) }}

SELECT
    fuel_type,
    count() AS offer_count
FROM {{ ref('dim__offers') }}
GROUP BY fuel_type
