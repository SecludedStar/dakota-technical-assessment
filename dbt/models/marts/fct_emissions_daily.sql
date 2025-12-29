{{
    config(
        materialized='table',
        schema='analytics'
    )
}}

/*
    Emissions analysis mart.
    
    Combines emissions data with well information for environmental reporting.
*/

with wells as (
    select * from {{ ref('stg_wells') }}
),

emissions as (
    select * from {{ ref('stg_emissions') }}
),

joined as (
    select
        -- Well dimensions
        w.well_id,
        w.well_name,
        w.operator,
        w.basin,
        w.state,
        w.well_type,
        w.status as well_status,
        
        -- Emissions dimensions
        e.measurement_date,
        extract(year from e.measurement_date)::int as measurement_year,
        extract(month from e.measurement_date)::int as measurement_month,
        
        -- Emissions metrics
        e.methane_kg,
        e.co2_kg,
        e.voc_kg,
        e.total_emissions_kg,
        e.co2_equivalent_kg,
        e.flare_volume_mcf,
        
        -- Flags
        e.leak_detected,
        e.is_high_emission_day,
        e.has_flaring,
        
        -- Measurement details
        e.measurement_method
        
    from emissions e
    inner join wells w on e.well_id = w.well_id
),

with_metrics as (
    select
        *,
        
        -- Emissions intensity (placeholder - would need production data join)
        total_emissions_kg / nullif(1, 0) as emissions_intensity,
        
        -- Environmental risk score
        case
            when leak_detected then 'High'
            when is_high_emission_day then 'Medium'
            when has_flaring then 'Low-Medium'
            else 'Low'
        end as environmental_risk
        
    from joined
)

select
    *,
    current_timestamp as model_run_at
from with_metrics
