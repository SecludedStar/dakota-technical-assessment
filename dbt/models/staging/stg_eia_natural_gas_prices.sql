{{
    config(
        materialized='view',
        schema='staging'
    )
}}

/*
    Staging model for EIA natural gas price data.
    
    Cleans and standardizes natural gas price information.
*/

with source as (
    select * from {{ source('raw', 'eia_natural_gas_prices') }}
),

cleaned as (
    select
        -- Time dimension
        period,
        -- Parse period to date (format: YYYY-MM)
        to_date(period || '-01', 'YYYY-MM-DD') as period_date,
        extract(year from to_date(period || '-01', 'YYYY-MM-DD'))::int as period_year,
        extract(month from to_date(period || '-01', 'YYYY-MM-DD'))::int as period_month,
        
        -- Area information
        trim(duoarea) as area_code,
        trim(area_name) as area_name,
        
        -- Product information
        trim(product) as product_code,
        trim(product_name) as product_name,
        
        -- Process/sector information
        trim(process) as process_code,
        trim(process_name) as process_name,
        
        -- Series identifier
        trim(series) as series_id,
        trim(series_description) as series_description,
        
        -- Price value
        coalesce(value, 0) as price_value,
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
