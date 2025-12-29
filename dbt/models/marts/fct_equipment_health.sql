{{
    config(
        materialized='table',
        schema='analytics'
    )
}}

/*
    Equipment health summary mart.
    
    Aggregates equipment status and alerts for maintenance planning.
*/

with well_equipment as (
    select * from {{ ref('int_well_equipment') }}
),

equipment_summary as (
    select
        -- Dimensions
        equipment_id,
        equipment_type,
        manufacturer,
        well_id,
        well_name,
        operator,
        basin,
        state,
        
        -- Health metrics
        health_score,
        health_category,
        equipment_status,
        is_operational,
        risk_level,
        
        -- Maintenance info
        install_date,
        last_maintenance,
        next_maintenance,
        days_since_maintenance,
        days_until_maintenance,
        is_maintenance_overdue,
        
        -- Runtime
        runtime_hours,
        
        -- Alert details
        alert_count,
        has_alerts,
        alerts,
        
        -- Priority score for maintenance scheduling
        -- Higher score = higher priority
        case
            when risk_level = 'Critical' then 100
            when risk_level = 'High' then 75
            when risk_level = 'Medium' then 50
            else 25
        end
        + (100 - health_score) 
        + (alert_count * 10)
        + (case when is_maintenance_overdue then 30 else 0 end)
        as maintenance_priority_score,
        
        -- Estimated remaining useful life (simple model)
        case
            when health_score >= 90 then '12+ months'
            when health_score >= 70 then '6-12 months'
            when health_score >= 50 then '3-6 months'
            when health_score >= 30 then '1-3 months'
            else 'Immediate attention'
        end as estimated_remaining_life
        
    from well_equipment
)

select
    *,
    current_timestamp as model_run_at
from equipment_summary
order by maintenance_priority_score desc
