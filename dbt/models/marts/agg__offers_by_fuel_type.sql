{{ config(
    engine='MergeTree()',
    order_by='fuel_type'
) }}

select
    ifNull(fuel_type, 'unknown') as fuel_type,
    count() as offer_count
from {{ ref('dim__offers') }}
group by fuel_type
