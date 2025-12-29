{{
    config(
        materialized='view',
        schema='staging'
    )
}}

/*
    Staging model for emissions monitoring data.
    
    Cleans emissions data and calculates total emissions metrics.
*/

with source as (
    select * from {{ source('raw', 'emissions') }}
),

cleaned as (
    select
        -- Keys
        well_id,
        measurement_date,
        
        -- Emissions (ensure non-negative)
        greatest(coalesce(methane_kg, 0), 0) as methane_kg,
        greatest(coalesce(co2_kg, 0), 0) as co2_kg,
        greatest(coalesce(voc_kg, 0), 0) as voc_kg,
        greatest(coalesce(flare_volume_mcf, 0), 0) as flare_volume_mcf,
        
        -- Total GHG emissions (CO2 equivalent)
        -- Methane has ~25x warming potential of CO2
        greatest(coalesce(methane_kg, 0), 0) * 25 + 
        greatest(coalesce(co2_kg, 0), 0) as co2_equivalent_kg,
        
        -- Total emissions (simple sum)
        greatest(coalesce(methane_kg, 0), 0) + 
        greatest(coalesce(co2_kg, 0), 0) + 
        greatest(coalesce(voc_kg, 0), 0) as total_emissions_kg,
        
        -- Leak detection
        coalesce(leak_detected, false) as leak_detected,
        
        -- Measurement method
        trim(measurement_method) as measurement_method,
        
        -- Is this a high-emission day (top 10% threshold)
        case 
            when methane_kg > 50 or co2_kg > 400 then true
            else false
        end as is_high_emission_day,
        
        -- Flaring flag
        flare_volume_mcf > 0 as has_flaring,
        
        -- Metadata
        ingested_at,
        current_timestamp as transformed_at
        
    from source
    where well_id is not null
      and measurement_date is not null
)

select * from cleaned
