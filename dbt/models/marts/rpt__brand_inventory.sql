{{ config(
    engine='MergeTree()',
    order_by='brand'
) }}

with brand_inventory as (
    select
        brand,
        offer_count as total_offers,
        sum(offer_count) over () as marketplace_offer_count
    from {{ ref('agg__offers_by_brand') }}
)

select
    brand,
    total_offers,
    total_offers / nullIf(marketplace_offer_count, 0) as inventory_share
from brand_inventory
order by total_offers desc
