{{ config(
    engine='MergeTree()',
    order_by='observation_date'
) }}

with current_inventory as (
    select
        count() as current_offer_count
    from {{ ref('dim__offers') }}
), daily_new_offers as (
    select
        toDate(first_observed_at) as observation_date,
        count() as new_offer_count
    from {{ ref('dim__offers') }}
    group by observation_date
), daily_activity as (
    select
        observation_date,
        observation_count,
        distinct_offer_count,
        average_price_amount
    from {{ ref('agg__daily_offer_observations') }}
)

select
    daily_activity.observation_date as observation_date,
    current_inventory.current_offer_count,
    ifNull(daily_new_offers.new_offer_count, 0) as new_offer_count,
    sum(ifNull(daily_new_offers.new_offer_count, 0)) over (
        order by daily_activity.observation_date
        rows between unbounded preceding and current row
    ) as cumulative_offer_count,
    daily_activity.observation_count,
    daily_activity.distinct_offer_count,
    daily_activity.average_price_amount
from daily_activity
cross join current_inventory
left join daily_new_offers
    on daily_activity.observation_date = daily_new_offers.observation_date
