{{
    config(
        materialized='ephemeral'
    )
}}

/*
    Intermediate model joining wells with production data.
    
    Provides enriched production records with well context.
*/

with wells as (
    select * from {{ ref('stg_wells') }}
),

production as (
    select * from {{ ref('stg_production') }}
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
        w.well_age_days,
        
        -- Production facts
        p.production_date,
        p.oil_bbl,
        p.gas_mcf,
        p.water_bbl,
        p.total_liquid_bbl,
        p.uptime_hours,
        p.uptime_pct,
        p.water_cut_pct,
        p.gor_mcf_bbl,
        p.tubing_pressure_psi,
        p.casing_pressure_psi,
        
        -- Production rates
        p.oil_rate_bbl_per_hour,
        p.gas_rate_mcf_per_hour,
        
        -- Time dimensions
        extract(year from p.production_date)::int as production_year,
        extract(month from p.production_date)::int as production_month,
        extract(week from p.production_date)::int as production_week,
        extract(dow from p.production_date)::int as day_of_week
        
    from production p
    inner join wells w on p.well_id = w.well_id
)

select * from joined
