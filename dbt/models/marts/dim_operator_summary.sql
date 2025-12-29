{{
    config(
        materialized='table',
        schema='analytics'
    )
}}

/*
    Operator summary mart.
    
    Aggregates key metrics by operator for executive reporting.
*/

with well_production as (
    select * from {{ ref('int_well_production') }}
),

well_equipment as (
    select * from {{ ref('int_well_equipment') }}
),

wells as (
    select * from {{ ref('stg_wells') }}
),

emissions as (
    select * from {{ ref('stg_emissions') }}
),

-- Well counts by operator
well_summary as (
    select
        operator,
        count(*) as total_wells,
        sum(case when status = 'Active' then 1 else 0 end) as active_wells,
        sum(case when status = 'Inactive' then 1 else 0 end) as inactive_wells,
        sum(case when status = 'Plugged' then 1 else 0 end) as plugged_wells,
        count(distinct basin) as basins_operated,
        count(distinct state) as states_operated,
        avg(well_age_days) as avg_well_age_days
    from wells
    group by operator
),

-- Production totals by operator
production_summary as (
    select
        operator,
        sum(oil_bbl) as total_oil_bbl,
        sum(gas_mcf) as total_gas_mcf,
        sum(water_bbl) as total_water_bbl,
        avg(uptime_pct) as avg_uptime_pct,
        avg(water_cut_pct) as avg_water_cut_pct,
        count(distinct well_id) as producing_wells
    from well_production
    where production_date >= current_date - interval '30 days'
    group by operator
),

-- Equipment health by operator
equipment_summary as (
    select
        operator,
        count(*) as total_equipment,
        avg(health_score) as avg_equipment_health,
        sum(case when risk_level = 'Critical' then 1 else 0 end) as critical_equipment,
        sum(case when risk_level = 'High' then 1 else 0 end) as high_risk_equipment,
        sum(case when is_maintenance_overdue then 1 else 0 end) as overdue_maintenance,
        sum(alert_count) as total_alerts
    from well_equipment
    group by operator
),

-- Emissions by operator
emissions_summary as (
    select
        w.operator,
        sum(e.methane_kg) as total_methane_kg,
        sum(e.co2_equivalent_kg) as total_co2e_kg,
        sum(case when e.leak_detected then 1 else 0 end) as leak_events,
        sum(e.flare_volume_mcf) as total_flare_mcf
    from emissions e
    inner join wells w on e.well_id = w.well_id
    where e.measurement_date >= current_date - interval '30 days'
    group by w.operator
)

select
    -- Operator identification
    ws.operator,
    
    -- Well metrics
    ws.total_wells,
    ws.active_wells,
    ws.inactive_wells,
    ws.plugged_wells,
    ws.basins_operated,
    ws.states_operated,
    round(ws.avg_well_age_days) as avg_well_age_days,
    
    -- Production metrics (last 30 days)
    coalesce(ps.total_oil_bbl, 0) as total_oil_bbl_30d,
    coalesce(ps.total_gas_mcf, 0) as total_gas_mcf_30d,
    coalesce(ps.total_water_bbl, 0) as total_water_bbl_30d,
    round(coalesce(ps.avg_uptime_pct, 0)::numeric, 1) as avg_uptime_pct,
    round(coalesce(ps.avg_water_cut_pct, 0)::numeric, 1) as avg_water_cut_pct,
    
    -- BOE (30 day)
    coalesce(ps.total_oil_bbl, 0) + (coalesce(ps.total_gas_mcf, 0) / 6.0) as total_boe_30d,
    
    -- Equipment metrics
    coalesce(es.total_equipment, 0) as total_equipment,
    round(coalesce(es.avg_equipment_health, 0)::numeric, 1) as avg_equipment_health,
    coalesce(es.critical_equipment, 0) as critical_equipment,
    coalesce(es.high_risk_equipment, 0) as high_risk_equipment,
    coalesce(es.overdue_maintenance, 0) as overdue_maintenance_count,
    coalesce(es.total_alerts, 0) as total_equipment_alerts,
    
    -- Emissions metrics (30 day)
    round(coalesce(ems.total_methane_kg, 0)::numeric, 2) as total_methane_kg_30d,
    round(coalesce(ems.total_co2e_kg, 0)::numeric, 2) as total_co2e_kg_30d,
    coalesce(ems.leak_events, 0) as leak_events_30d,
    round(coalesce(ems.total_flare_mcf, 0)::numeric, 2) as total_flare_mcf_30d,
    
    -- Calculated scores
    case
        when ws.active_wells = 0 then 0
        else round((coalesce(ps.total_oil_bbl, 0) / ws.active_wells)::numeric, 2)
    end as oil_per_active_well_30d,
    
    -- Timestamp
    current_timestamp as model_run_at

from well_summary ws
left join production_summary ps on ws.operator = ps.operator
left join equipment_summary es on ws.operator = es.operator
left join emissions_summary ems on ws.operator = ems.operator

order by ws.total_wells desc
