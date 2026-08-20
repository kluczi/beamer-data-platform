{{ config(
    engine='MergeTree()',
    order_by='brand'
) }}

select
    coalesce(brand, 'unknown') as brand,
    count() as offer_count
from {{ ref('dim__offers') }}
group by brand
