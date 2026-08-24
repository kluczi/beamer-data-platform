---
title: Beamer Analytics
---

```sql overview
select *
from beamer_clickhouse.rpt__marketplace_overview
order by observation_date
```

```sql current_metrics
select
    current_offer_count,
    average_price_amount,
    observation_count,
    distinct_offer_count,
    new_offer_count,
    observation_date
from ${overview}
order by observation_date desc
limit 1
```

```sql brands
select *
from beamer_clickhouse.rpt__brand_inventory
order by total_offers desc
```

```sql top_brands
select *
from ${brands}
limit 10
```

```sql fuels
select *
from beamer_clickhouse.rpt__fuel_type
order by total_offers desc
```

```sql mileage_price
select *
from beamer_clickhouse.rpt__mileage_vs_price
where mileage_km >= 0 and price_amount > 0
order by last_observed_at desc
limit 1000
```

```sql mileage_price_bands
select
    brand,
    cast(floor(mileage_km / 25000.0) * 25000 + 12500 as integer) as mileage_band_midpoint,
    median(price_amount) as median_price_amount,
    count(*) as offer_count
from ${mileage_price}
group by
    brand,
    mileage_band_midpoint
order by mileage_band_midpoint, brand
```

```sql vehicle_prices
select *
from beamer_clickhouse.rpt__price_distribution_by_vehicle
order by offer_count desc, median_price_amount desc
limit 15
```

<Grid cols=4 gapSize="lg">
    <BigValue data={current_metrics} value=current_offer_count title="Current inventory" fmt=num0 />
    <BigValue data={current_metrics} value=average_price_amount title="Average asking price" fmt='#,##0" zł"' />
    <BigValue data={current_metrics} value=new_offer_count title="New in latest day" fmt=num0 />
    <BigValue data={current_metrics} value=distinct_offer_count title="Offers in latest snapshot" fmt=num0 />
</Grid>

## Marketplace momentum

<Grid cols=2 gapSize="lg">
    <LineChart
        data={overview}
        x=observation_date
        y=cumulative_offer_count
        y2=average_price_amount
        yFmt=num0
        y2Fmt='#,##0" zł"'
        yAxisTitle="Offers"
        y2AxisTitle="Average price"
        title="Catalog growth and asking price"
        chartAreaHeight=300
    />
    <BarChart
        data={overview}
        x=observation_date
        y=new_offer_count
        yFmt=num0
        title="New offers by day"
        chartAreaHeight=300
    />
</Grid>

## Inventory mix

<Grid cols=2 gapSize="lg">
    <BarChart
        data={top_brands}
        x=brand
        y=total_offers
        yFmt=num0
        swapXY=true
        labels=true
        title="Top brands by inventory"
        chartAreaHeight=360
    />
    <BarChart
        data={fuels}
        x=fuel_type
        y=total_offers
        yFmt=num0
        labels=true
        title="Inventory by fuel type"
        chartAreaHeight=360
    />
</Grid>

## Median price by mileage

<LineChart
    data={mileage_price_bands}
    x=mileage_band_midpoint
    y=median_price_amount
    series=brand
    xFmt=num0
    yFmt='#,##0" zł"'
    xMin=0
    yMin=0
    xAxisTitle="Mileage (km)"
    yAxisTitle="Median asking price"
    markers=true
    lineWidth=2
    chartAreaHeight=440
    legend=true
/>

## Most represented vehicle groups

<DataTable data={vehicle_prices} rows=15>
    <Column id=brand title="Brand" />
    <Column id=vehicle_model title="Model" />
    <Column id=model_year title="Year" fmt=num0 />
    <Column id=offer_count title="Offers" fmt=num0 contentType="bar" />
    <Column id=minimum_price_amount title="Minimum" fmt='#,##0" zł"' />
    <Column id=median_price_amount title="Median" fmt='#,##0" zł"' />
    <Column id=maximum_price_amount title="Maximum" fmt='#,##0" zł"' />
</DataTable>
