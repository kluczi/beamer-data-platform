select
    brand,
    total_offers,
    inventory_share
from rpt__brand_inventory
order by total_offers desc
