{{
    config(
        materialized='view',
        schema='staging'
    )
}}

/*
    Staging model for EIA petroleum spot price data.
    
    Cleans and standardizes petroleum price information.
*/

with source as (
    select * from {{ source('raw', 'eia_petroleum_prices') }}
),

cleaned as (
    select
        -- Time dimension
        period,
        -- Parse period to date (format: YYYY-MM-DD)
        to_date(period, 'YYYY-MM-DD') as price_date,
        extract(year from to_date(period, 'YYYY-MM-DD'))::int as price_year,
        extract(month from to_date(period, 'YYYY-MM-DD'))::int as price_month,
        extract(dow from to_date(period, 'YYYY-MM-DD'))::int as day_of_week,
        
        -- Area information
        trim(duoarea) as area_code,
        trim(area_name) as area_name,
        
        -- Product information
        trim(product) as product_code,
        trim(product_name) as product_name,
        
        -- Identify major benchmark products
        case
            when upper(trim(product)) = 'EPCBRENT' then 'Brent Crude'
            when upper(trim(product)) = 'EPCWTI' then 'WTI Crude'
            else trim(product_name)
        end as benchmark_name,
        
        -- Series identifier
        trim(series) as series_id,
        trim(series_description) as series_description,
        
        -- Price value
        coalesce(value, 0) as price_usd,
        trim(units) as price_units,
        
        -- Is this a valid price (non-null, positive)
        value is not null and value > 0 as is_valid_price,
        
        -- Metadata
        ingested_at,
        current_timestamp as transformed_at
        
    from source
    where period is not null
)

select * from cleaned
