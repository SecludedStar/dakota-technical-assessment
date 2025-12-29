{{
    config(
        materialized='view',
        schema='staging'
    )
}}

/*
    Staging model for equipment status data.
    
    Cleans equipment data and extracts alert information.
*/

with source as (
    select * from {{ source('raw', 'equipment') }}
),

cleaned as (
    select
        -- Keys
        equipment_id,
        well_id,
        
        -- Equipment details
        trim(equipment_type) as equipment_type,
        trim(manufacturer) as manufacturer,
        install_date,
        
        -- Maintenance dates
        last_maintenance,
        next_maintenance,
        
        -- Days since last maintenance
        current_date - last_maintenance as days_since_maintenance,
        
        -- Days until next maintenance
        next_maintenance - current_date as days_until_maintenance,
        
        -- Health metrics
        round(greatest(least(coalesce(health_score, 0), 100), 0)::numeric, 1) as health_score,
        
        -- Health status category
        case
            when health_score >= 90 then 'Excellent'
            when health_score >= 70 then 'Good'
            when health_score >= 50 then 'Fair'
            when health_score >= 30 then 'Poor'
            else 'Critical'
        end as health_category,
        
        -- Status
        initcap(trim(status)) as status,
        
        -- Is equipment operational
        case 
            when lower(status) in ('operational', 'active') then true
            else false
        end as is_operational,
        
        -- Runtime
        greatest(coalesce(runtime_hours, 0), 0) as runtime_hours,
        
        -- Alerts (as JSONB)
        coalesce(alerts, '[]'::jsonb) as alerts,
        
        -- Alert count
        jsonb_array_length(coalesce(alerts, '[]'::jsonb)) as alert_count,
        
        -- Has active alerts
        jsonb_array_length(coalesce(alerts, '[]'::jsonb)) > 0 as has_alerts,
        
        -- Maintenance overdue flag
        next_maintenance < current_date as is_maintenance_overdue,
        
        -- Metadata
        ingested_at,
        current_timestamp as transformed_at
        
    from source
    where equipment_id is not null
      and well_id is not null
)

select * from cleaned
