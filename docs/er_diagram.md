# Database ER Diagram

## Entity Relationship Diagram

```mermaid
erDiagram
    %% Raw Layer Tables

    wells ||--o{ production : "produces"
    wells ||--o{ equipment : "has"
    wells ||--o{ emissions : "emits"

    wells {
        varchar well_id PK
        varchar api_number UK
        varchar well_name
        varchar operator
        varchar basin
        varchar state
        varchar county
        decimal latitude
        decimal longitude
        varchar well_type
        varchar status
        date spud_date
        date first_production_date
        timestamp loaded_at
    }

    production {
        serial id PK
        varchar well_id FK
        date production_date
        decimal oil_bbl
        decimal gas_mcf
        decimal water_bbl
        int hours_online
        timestamp loaded_at
    }

    equipment {
        varchar equipment_id PK
        varchar well_id FK
        varchar equipment_type
        varchar manufacturer
        date install_date
        date last_maintenance
        date next_maintenance
        int health_score
        varchar status
        decimal runtime_hours
        jsonb alerts
        timestamp loaded_at
    }

    emissions {
        serial id PK
        varchar well_id FK
        date measurement_date
        decimal methane_kg
        decimal co2_kg
        decimal voc_kg
        decimal flare_volume_mcf
        boolean leak_detected
        timestamp loaded_at
    }

    eia_natural_gas_prices {
        serial id PK
        varchar period
        varchar series UK
        decimal value
        varchar units
        varchar description
        timestamp loaded_at
    }

    eia_petroleum_prices {
        serial id PK
        varchar period
        varchar series UK
        decimal value
        varchar units
        varchar product
        varchar area
        timestamp loaded_at
    }

    ingestion_log {
        serial id PK
        varchar source
        varchar table_name
        int rows_loaded
        varchar status
        text error_message
        timestamp started_at
        timestamp completed_at
    }
```

## Schema Overview

### Raw Layer (`raw.*`)
| Table | Description | Primary Key | Unique Constraints |
|-------|-------------|-------------|-------------------|
| `wells` | Well master data | `well_id` | `api_number` |
| `production` | Daily production metrics | `id` | `(well_id, production_date)` |
| `equipment` | Equipment health data | `equipment_id` | - |
| `emissions` | Environmental monitoring | `id` | `(well_id, measurement_date)` |
| `eia_natural_gas_prices` | Natural gas prices | `id` | `(period, series)` |
| `eia_petroleum_prices` | Crude oil prices | `id` | `(period, series)` |
| `ingestion_log` | Pipeline run metadata | `id` | - |

### Staging Layer (`staging.*`) - dbt Managed
Views that clean and standardize raw data:
- `stg_wells`, `stg_production`, `stg_equipment`, `stg_emissions`
- `stg_eia_natural_gas_prices`, `stg_eia_petroleum_prices`

### Analytics Layer (`analytics.*`) - dbt Managed
Materialized tables for business metrics:
- `fct_well_performance_daily` - Production with revenue estimates
- `fct_equipment_health` - Maintenance priority scoring
- `fct_emissions_daily` - Environmental risk categories
- `dim_operator_summary` - Operator-level KPIs

## Relationships

| Parent | Child | Relationship | On |
|--------|-------|--------------|-----|
| `wells` | `production` | 1:Many | `well_id` |
| `wells` | `equipment` | 1:Many | `well_id` |
| `wells` | `emissions` | 1:Many | `well_id` |
