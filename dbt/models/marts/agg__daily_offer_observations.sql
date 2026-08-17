{{ config(
    engine='MergeTree()',
    order_by='observation_date'
) }}

select
    toDate(observed_at) as observation_date,
    count() as observation_count,
    uniqExact(offer_key) as distinct_offer_count,
    avg(price_amount) as average_price_amount
from {{ ref('fct__offer_observations') }}
group by observation_date
