{{ config(
    engine='MergeTree()',
    order_by='(source_offer_id, observed_at)'
) }}


with latest_currency_rates as (
    select
        price_currency,
        argMax(
            rate_to_pln,
            tuple(effective_date, fetched_at)
        ) as rate_to_pln
    from {{ ref('stg__currency_rates') }}
    where quote_currency = 'PLN'
    group by price_currency
),

offers_with_exchange_rate as (
    select
        oo.source_offer_id,
        oo.url,
        oo.title,
        oo.brand,
        oo.model,
        oo.year,
        oo.mileage_km,
        oo.fuel_type,
        oo.transmission,
        oo.observed_at,
        oo.scrape_run_id,
        case
            when oo.price_currency = 'PLN' or lcr.rate_to_pln is not null then 'PLN'
            else oo.price_currency
        end as price_currency,
        case
            when oo.price_currency = 'PLN' then oo.price_amount
            when lcr.rate_to_pln is not null then oo.price_amount * lcr.rate_to_pln
        end as price_amount
    from {{ ref('stg_raw__offers_observations') }} as oo
    left join latest_currency_rates as lcr
        on oo.price_currency = lcr.price_currency
)

select * from offers_with_exchange_rate
