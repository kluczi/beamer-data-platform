{{ config(
    engine='MergeTree()',
    order_by='(brand, vehicle_model, model_year, offer_key)'
) }}

with current_offers as (
    select
        offer_key,
        url,
        title,
        fuel_type,
        transmission,
        mileage_km,
        price_amount,
        price_currency,
        last_observed_at,
        coalesce(brand, 'unknown') as brand,
        coalesce(model, 'unknown') as vehicle_model,
        coalesce(year, 0) as model_year
    from {{ ref('dim__offers') }}
    where
        mileage_km is not null
        and price_amount is not null
)

select
    offer_key,
    url,
    title,
    brand,
    vehicle_model,
    model_year,
    fuel_type,
    transmission,
    mileage_km,
    price_amount,
    price_currency,
    last_observed_at
from current_offers
