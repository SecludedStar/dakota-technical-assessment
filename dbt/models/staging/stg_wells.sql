{{
    config(
        materialized='view',
        schema='staging'
    )
}}

/*
    Staging model for well master data.
    
    Cleans and standardizes well information from the raw layer.
*/

with source as (
    select * from {{ source('raw', 'wells') }}
),

cleaned as (
    select
        -- Primary key
        well_id,
        
        -- Well identification
        trim(well_name) as well_name,
        trim(operator) as operator,
        
        -- Location
        trim(basin) as basin,
        upper(trim(state)) as state,
        round(latitude::numeric, 6) as latitude,
        round(longitude::numeric, 6) as longitude,
        
        -- Well attributes
        initcap(trim(well_type)) as well_type,
        spud_date,
        initcap(trim(status)) as status,
        
        -- Calculate well age in days
        current_date - spud_date as well_age_days,
        
        -- Metadata
        ingested_at,
        current_timestamp as transformed_at
        
    from source
    where well_id is not null
)

select * from cleaned
