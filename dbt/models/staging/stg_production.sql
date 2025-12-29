{{
    config(
        materialized='view',
        schema='staging'
    )
}}

/*
    Staging model for daily production records.
    
    Cleans production data and calculates derived metrics.
*/

with source as (
    select * from {{ source('raw', 'production') }}
),

cleaned as (
    select
        -- Keys
        well_id,
        production_date,
        
        -- Production volumes (ensure non-negative)
        greatest(coalesce(oil_bbl, 0), 0) as oil_bbl,
        greatest(coalesce(gas_mcf, 0), 0) as gas_mcf,
        greatest(coalesce(water_bbl, 0), 0) as water_bbl,
        
        -- Total liquid production
        greatest(coalesce(oil_bbl, 0), 0) + greatest(coalesce(water_bbl, 0), 0) as total_liquid_bbl,
        
        -- Operational metrics
        least(greatest(coalesce(uptime_hours, 0), 0), 24) as uptime_hours,
        coalesce(choke_size, 0) as choke_size,
        greatest(coalesce(tubing_pressure_psi, 0), 0) as tubing_pressure_psi,
        greatest(coalesce(casing_pressure_psi, 0), 0) as casing_pressure_psi,
        
        -- Derived metrics
        case 
            when uptime_hours > 0 then oil_bbl / uptime_hours 
            else 0 
        end as oil_rate_bbl_per_hour,
        
        case 
            when uptime_hours > 0 then gas_mcf / uptime_hours 
            else 0 
        end as gas_rate_mcf_per_hour,
        
        -- Water cut percentage
        case 
            when (oil_bbl + water_bbl) > 0 
            then round((water_bbl / (oil_bbl + water_bbl) * 100)::numeric, 2)
            else 0 
        end as water_cut_pct,
        
        -- Gas-Oil Ratio (GOR) in MCF/BBL
        case 
            when oil_bbl > 0 then round((gas_mcf / oil_bbl)::numeric, 2)
            else null 
        end as gor_mcf_bbl,
        
        -- Uptime percentage
        round((uptime_hours / 24 * 100)::numeric, 1) as uptime_pct,
        
        -- Metadata
        ingested_at,
        current_timestamp as transformed_at
        
    from source
    where well_id is not null
      and production_date is not null
)

select * from cleaned
