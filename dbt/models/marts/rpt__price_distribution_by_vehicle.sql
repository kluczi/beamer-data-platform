{{ config(
    engine='MergeTree()',
    order_by='offer_count'
) }}

with priced_offers as (
    select
        price_currency,
        price_amount,
        coalesce(brand, 'unknown') as brand,
        coalesce(model, 'unknown') as vehicle_model,
        coalesce(year, 0) as model_year
    from {{ ref('dim__offers') }}
    where
        price_amount is not null
        and price_currency is not null
)

select
    brand,
    vehicle_model,
    model_year,
    price_currency,
    count() as offer_count,
    min(price_amount) as minimum_price_amount,
    median(price_amount) as median_price_amount,
    max(price_amount) as maximum_price_amount
from priced_offers
group by
    brand,
    vehicle_model,
    model_year,
    price_currency
