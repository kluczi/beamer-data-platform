with ranked_currency_rates as (
    select
        effective_date,
        rate_to_pln,
        provider,
        source_table,
        fetched_at,
        upper(base_currency) as base_currency,
        upper(quote_currency) as quote_currency,
        row_number() over (
            partition by effective_date, base_currency, quote_currency
            order by fetched_at desc
        ) as rate_rank
    from {{ source('raw', 'currency_rates') }}
)

select
    effective_date,
    base_currency,
    quote_currency,
    rate_to_pln,
    provider,
    source_table,
    fetched_at
from ranked_currency_rates
where rate_rank = 1
