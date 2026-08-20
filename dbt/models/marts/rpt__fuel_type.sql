{{ config(
    engine='MergeTree()',
    order_by='fuel_type'
) }}

with fuel_type as (
    select
        fuel_type,
        offer_count as total_offers,
        sum(offer_count) over () as fuel_type_count
    from {{ ref('agg__offers_by_fuel_type') }}
)

select
    fuel_type,
    total_offers,
    total_offers / nullIf(fuel_type_count, 0) as fuel_share
from fuel_type
