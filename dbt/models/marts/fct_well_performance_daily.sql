{{
    config(
        materialized='table',
        schema='analytics'
    )
}}

/*
    Daily well performance mart.
    
    Aggregates production metrics by well and date for operational dashboards.
*/

with well_production as (
    select * from {{ ref('int_well_production') }}
),

daily_metrics as (
    select
        -- Dimensions
        well_id,
        well_name,
        operator,
        basin,
        state,
        well_type,
        well_status,
        production_date,
        production_year,
        production_month,
        
        -- Production volumes
        oil_bbl,
        gas_mcf,
        water_bbl,
        total_liquid_bbl,
        
        -- Calculated metrics
        water_cut_pct,
        gor_mcf_bbl,
        uptime_pct,
        
        -- Pressures
        tubing_pressure_psi,
        casing_pressure_psi,
        
        -- BOE (Barrel of Oil Equivalent)
        -- Using 6:1 conversion (6 MCF gas = 1 BBL oil equivalent)
        oil_bbl + (gas_mcf / 6.0) as boe_total,
        
        -- Revenue estimates (placeholder prices)
        oil_bbl * 75.0 as est_oil_revenue_usd,
        gas_mcf * 3.0 as est_gas_revenue_usd,
        (oil_bbl * 75.0) + (gas_mcf * 3.0) as est_total_revenue_usd,
        
        -- Performance flags
        case when uptime_pct >= 95 then true else false end as is_high_uptime,
        case when water_cut_pct > 50 then true else false end as is_high_water_cut,
        case when oil_bbl > 100 then true else false end as is_high_producer
        
    from well_production
    where well_status = 'Active'
)

select
    *,
    current_timestamp as model_run_at
from daily_metrics
