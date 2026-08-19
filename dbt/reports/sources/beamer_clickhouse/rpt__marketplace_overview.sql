select
    observation_date,
    current_offer_count,
    new_offer_count,
    cumulative_offer_count,
    observation_count,
    distinct_offer_count,
    average_price_amount
from rpt__marketplace_overview
order by observation_date
