{{ config(
    engine='MergeTree()',
    order_by='brand'
) }}

SELECT
    brand,
    count() AS offer_count
FROM {{ ref('dim__offers') }}
GROUP BY brand
