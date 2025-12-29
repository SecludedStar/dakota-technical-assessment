# Database Schema

PostgreSQL database schema implementing a medallion architecture for energy analytics.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                            PostgreSQL                               │
├───────────────────┬───────────────────┬─────────────────────────────┤
│       raw         │      staging      │         analytics           │
├───────────────────┼───────────────────┼─────────────────────────────┤
│ Source data       │ Cleaned data      │ Business metrics            │
│ as-is             │ (dbt managed)     │ (dbt managed)               │
│                   │                   │                             │
│ • EIA prices      │ • stg_wells       │ • fct_well_performance      │
│ • wells           │ • stg_production  │ • fct_equipment_health      │
│ • production      │ • stg_equipment   │ • fct_emissions_daily       │
│ • equipment       │ • stg_emissions   │ • dim_operator_summary      │
│ • emissions       │                   │                             │
└───────────────────┴───────────────────┴─────────────────────────────┘
```

## Raw Layer Tables

### EIA Data (External API)

| Table | Description | Update Frequency |
|-------|-------------|------------------|
| `eia_natural_gas_prices` | Natural gas price summaries by region/sector | Daily |
| `eia_petroleum_prices` | Crude oil spot prices (Brent, WTI) | Daily |

### Enrichment Data (Internal API)

| Table | Description | Update Frequency |
|-------|-------------|------------------|
| `wells` | Well master data (location, operator, status) | Daily |
| `production` | Daily production metrics (oil, gas, water) | Daily |
| `equipment` | Equipment health and maintenance status | Hourly |
| `emissions` | Environmental monitoring data | Daily |

### Metadata

| Table | Description |
|-------|-------------|
| `ingestion_log` | Tracks all ingestion runs with status and metrics |

## Key Design Decisions

### Upsert Pattern
All tables use `ON CONFLICT ... DO UPDATE` for idempotent loads:
- EIA prices: Unique on `(period, series)`
- Production: Unique on `(well_id, production_date)`
- Equipment: Unique on `equipment_id`
- Emissions: Unique on `(well_id, measurement_date)`

### Time-Series Optimization
- Indexed on date columns for efficient range queries
- Partitioning can be added for production tables at scale

### JSONB for Flexible Data
- `equipment.alerts` stored as JSONB array
- Allows flexible schema for varying alert types

## Initialization

The `init.sql` script:
1. Creates all three schemas (raw, staging, analytics)
2. Creates raw layer tables with constraints
3. Creates indexes for query performance
4. Sets up permissions

```bash
# Run initialization
psql -h localhost -U postgres -d energy_analytics -f init.sql
```

## ER Diagram

See [docs/er_diagram.md](../docs/er_diagram.md) for the complete entity-relationship diagram (rendered as Mermaid).

## Schema Management

- **Raw layer**: Managed by Python ingestion scripts
- **Staging/Analytics layers**: Managed by dbt (see `/dbt` directory)

## Performance Considerations

1. **Indexes**: All foreign key and frequently queried columns are indexed
2. **Batch Inserts**: Use `execute_values` for bulk loads
3. **Connection Pooling**: Recommended for production (PgBouncer)
4. **Vacuum**: Schedule regular maintenance for heavily updated tables
