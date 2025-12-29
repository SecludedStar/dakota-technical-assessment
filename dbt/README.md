# dbt Transformations

dbt project implementing a medallion architecture for energy analytics transformations.

## Project Structure

```
dbt/
├── dbt_project.yml      # Project configuration
├── profiles.yml         # Connection profiles
├── models/
│   ├── staging/         # Cleaned source data (views)
│   │   ├── sources.yml  # Source definitions
│   │   ├── schema.yml   # Model documentation & tests
│   │   ├── stg_wells.sql
│   │   ├── stg_production.sql
│   │   ├── stg_equipment.sql
│   │   ├── stg_emissions.sql
│   │   ├── stg_eia_natural_gas_prices.sql
│   │   └── stg_eia_petroleum_prices.sql
│   ├── intermediate/    # Business logic (ephemeral)
│   │   ├── int_well_production.sql
│   │   └── int_well_equipment.sql
│   └── marts/           # Business-ready tables
│       ├── schema.yml
│       ├── fct_well_performance_daily.sql
│       ├── fct_equipment_health.sql
│       ├── fct_emissions_daily.sql
│       └── dim_operator_summary.sql
├── macros/              # Reusable SQL
├── tests/               # Custom data tests
└── seeds/               # Static reference data
```

## Architecture

### Staging Layer (`staging/`)
- **Materialization**: Views
- **Purpose**: Clean and standardize raw data
- **Naming**: `stg_<source>_<entity>`

Models:
| Model | Description |
|-------|-------------|
| `stg_wells` | Cleaned well master data |
| `stg_production` | Production with derived metrics (water cut, GOR) |
| `stg_equipment` | Equipment with health categorization |
| `stg_emissions` | Emissions with CO2 equivalents |
| `stg_eia_natural_gas_prices` | EIA natural gas prices |
| `stg_eia_petroleum_prices` | EIA petroleum spot prices |

### Intermediate Layer (`intermediate/`)
- **Materialization**: Ephemeral (compiled into downstream queries)
- **Purpose**: Join and prepare data for marts
- **Naming**: `int_<entity>_<description>`

Models:
| Model | Description |
|-------|-------------|
| `int_well_production` | Wells joined with production |
| `int_well_equipment` | Wells joined with equipment |

### Marts Layer (`marts/`)
- **Materialization**: Tables
- **Purpose**: Business-ready analytics
- **Naming**: `fct_<entity>` (facts) or `dim_<entity>` (dimensions)

Models:
| Model | Description |
|-------|-------------|
| `fct_well_performance_daily` | Daily production metrics with revenue estimates |
| `fct_equipment_health` | Equipment status with maintenance priority |
| `fct_emissions_daily` | Environmental metrics by well |
| `dim_operator_summary` | Executive summary by operator |

## Key Transformations

### Production Metrics
- Water Cut: `water_bbl / (oil_bbl + water_bbl) * 100`
- Gas-Oil Ratio: `gas_mcf / oil_bbl`
- BOE: `oil_bbl + (gas_mcf / 6)`

### Equipment Health
- Health Categories: Excellent (90+), Good (70-89), Fair (50-69), Poor (30-49), Critical (<30)
- Risk Levels: Based on health score, maintenance status, and alerts

### Emissions
- CO2 Equivalent: `methane_kg * 25 + co2_kg` (using GWP of methane)

## Running dbt

```bash
# Install dependencies
pip install dbt-postgres

# Test connection
dbt debug

# Run all models
dbt run

# Run specific layer
dbt run --select staging
dbt run --select marts

# Run with tests
dbt build

# Generate documentation
dbt docs generate
dbt docs serve
```

## Tests

Built-in tests include:
- `unique` and `not_null` on primary keys
- `accepted_values` for categorical columns
- `relationships` for foreign keys

Run tests:
```bash
dbt test
```

## Variables

Configure in `dbt_project.yml`:
```yaml
vars:
  start_date: '2024-01-01'
  equipment_health_threshold: 70
  include_leak_events: true
```

## Dependencies

This project uses:
- dbt-core >= 1.7.0
- dbt-postgres >= 1.7.0
- dbt-utils (for additional tests)
