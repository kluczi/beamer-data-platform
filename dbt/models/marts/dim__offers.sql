{{ config(
    engine='MergeTree()',
    order_by='offer_key'
) }}

with ranked_offer_observations as (
    select
        source_offer_id,
        url,
        title,
        brand,
        model,
        year,
        fuel_type,
        transmission,
        observed_at,
        row_number() over (
            partition by source_offer_id
            order by observed_at desc
        ) as observation_rank
    from {{ ref('int__exchange_rates') }}
),

offer_history as (
    select
        source_offer_id,
        min(observed_at) as first_observed_at,
        max(observed_at) as last_observed_at,
        count() as observation_count
    from {{ ref('int__exchange_rates') }}
    group by source_offer_id
)

select
    ranked_offer_observations.source_offer_id as offer_key,
    ranked_offer_observations.url,
    ranked_offer_observations.title,
    ranked_offer_observations.brand,
    ranked_offer_observations.model,
    ranked_offer_observations.year,
    ranked_offer_observations.fuel_type,
    ranked_offer_observations.transmission,
    offer_history.first_observed_at,
    offer_history.last_observed_at,
    offer_history.observation_count
from ranked_offer_observations
inner join offer_history
    on ranked_offer_observations.source_offer_id = offer_history.source_offer_id
where ranked_offer_observations.observation_rank = 1
