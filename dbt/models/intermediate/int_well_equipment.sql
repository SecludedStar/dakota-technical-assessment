{{
    config(
        materialized='ephemeral'
    )
}}

/*
    Intermediate model joining wells with equipment data.
    
    Provides enriched equipment records with well context.
*/

with wells as (
    select * from {{ ref('stg_wells') }}
),

equipment as (
    select * from {{ ref('stg_equipment') }}
),

joined as (
    select
        -- Equipment identification
        e.equipment_id,
        e.equipment_type,
        e.manufacturer,
        
        -- Well dimensions
        w.well_id,
        w.well_name,
        w.operator,
        w.basin,
        w.state,
        w.well_type,
        w.status as well_status,
        
        -- Equipment dates
        e.install_date,
        e.last_maintenance,
        e.next_maintenance,
        e.days_since_maintenance,
        e.days_until_maintenance,
        
        -- Health metrics
        e.health_score,
        e.health_category,
        e.status as equipment_status,
        e.is_operational,
        
        -- Runtime
        e.runtime_hours,
        
        -- Alerts
        e.alerts,
        e.alert_count,
        e.has_alerts,
        
        -- Maintenance status
        e.is_maintenance_overdue,
        
        -- Risk scoring (higher = more risk)
        case
            when e.is_maintenance_overdue and e.health_score < 50 then 'Critical'
            when e.is_maintenance_overdue or e.health_score < 50 then 'High'
            when e.has_alerts or e.health_score < 70 then 'Medium'
            else 'Low'
        end as risk_level
        
    from equipment e
    inner join wells w on e.well_id = w.well_id
)

select * from joined
