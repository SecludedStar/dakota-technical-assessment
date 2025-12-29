# Dakota Analytics Technical Assessment

A production-ready data pipeline for energy analytics demonstrating modern data engineering practices.

## Overview

This project implements an end-to-end data pipeline that:
- Ingests data from the **EIA API** (energy prices, production) and an internal **Enrichment API** (wells, equipment, emissions)
- Stores data in **PostgreSQL** using a medallion architecture (raw → staging → analytics)
- Transforms data with **dbt** following staging → intermediate → marts pattern
- Orchestrates everything with **Dagster** for scheduling, monitoring, and lineage
- Generates automated **reports** (Excel dashboards, PDF summaries)

## Architecture

```
EIA API ──────┐                    ┌─────────── PostgreSQL ─────────────┐
              │    Ingestion       │  raw.* → staging.* → analytics.*   │
              ├───────────────────►│         (dbt transforms)           │
Enrichment    │                    └─────────────┬─────────────────────┘
   API ───────┘                                  │
                                                 ▼
                                       Dagster Orchestration
                                                 │
                                                 ▼
                                    ┌───────────────────────┐
                                    │  Reports & Analytics  │
                                    │  Excel │ PDF │ Jupyter│
                                    └───────────────────────┘
```

See [docs/architecture.md](docs/architecture.md) for detailed system design.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- EIA API key ([register here](https://www.eia.gov/opendata/register.php))

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd dakota-assessment

# Start all services (creates .env automatically with demo_key)
chmod +x run.sh
./run.sh start

# Run the data pipeline
./run.sh pipeline

# View Dagster UI
open http://localhost:3000
```

> **Note**: The pipeline works out-of-the-box with `demo_key` for EIA API (rate-limited).
> For production use, get your own key at [eia.gov](https://www.eia.gov/opendata/register.php).

### Available Commands

```bash
./run.sh start      # Build and start all services
./run.sh stop       # Stop all services
./run.sh status     # Show service status and access points
./run.sh pipeline   # Run the complete data pipeline
./run.sh dbt        # Run dbt transformations only
./run.sh reports    # Generate reports only
./run.sh logs       # Show service logs
./run.sh clean      # Remove all containers and data
```

## Project Structure

```
dakota-assessment/
├── api/                    # FastAPI enrichment service
│   ├── main.py            # API endpoints and synthetic data generation
│   ├── Dockerfile         # Multi-stage container build
│   └── pyproject.toml     # uv dependency management
│
├── ingestion/              # Data ingestion clients
│   ├── eia_client.py      # EIA API client with retry logic
│   ├── enrichment_client.py # Internal API client
│   └── db_loader.py       # PostgreSQL batch loader
│
├── database/               # Database schema
│   └── init.sql           # Raw schema DDL
│
├── dbt/                    # dbt transformations
│   ├── models/
│   │   ├── staging/       # Clean and standardize raw data
│   │   ├── intermediate/  # Join and prepare for marts
│   │   └── marts/         # Business-ready analytics
│   └── dbt_project.yml
│
├── orchestration/          # Dagster orchestration
│   ├── assets/            # Software-defined assets
│   ├── resources/         # Database and API resources
│   └── jobs/              # Job definitions and schedules
│
├── reports/                # Report generation
│   ├── report_generator.py # Excel, PDF, notebook generation
│   └── output/            # Generated reports
│
├── docs/                   # Documentation
│   ├── architecture.md    # System design
│   └── decisions.md       # Technical decisions
│
├── docker-compose.yml      # Service orchestration
├── run.sh                  # Convenience script
└── .env.example           # Environment template
```

## Data Model

### Raw Layer
| Table | Description |
|-------|-------------|
| `eia_natural_gas_prices` | Natural gas spot and futures prices |
| `eia_petroleum_prices` | Brent/WTI crude oil prices |
| `wells` | Well metadata and status |
| `production` | Daily production metrics |
| `equipment` | Equipment health and alerts |
| `emissions` | Environmental monitoring |

### Analytics Layer (dbt Marts)
| Model | Description |
|-------|-------------|
| `fct_well_performance_daily` | Production metrics with revenue estimates |
| `fct_equipment_health` | Maintenance priority scoring |
| `fct_emissions_daily` | Environmental risk categorization |
| `dim_operator_summary` | Operator-level aggregations |

## Key Features

### Technical Excellence
- **Retry Logic**: Exponential backoff for transient failures
- **Idempotent Loading**: Upsert patterns prevent duplicates
- **Type Safety**: Pydantic validation throughout
- **Testing**: dbt tests, API tests, integration tests

### Architecture
- **Medallion Pattern**: Clear data progression
- **Separation of Concerns**: Ingestion, transformation, reporting
- **Resource-Based Design**: Clean configuration management

### Documentation
- Inline code comments
- dbt model documentation
- API OpenAPI/Swagger docs
- Architecture decision records

### Innovation
- Synthetic data generation with domain realism
- Maintenance priority scoring algorithm
- Environmental risk categorization
- Revenue estimation with price correlation

## API Endpoints

The Enrichment API provides synthetic operational data:

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /wells` | Paginated well information |
| `GET /production` | Daily production metrics |
| `GET /equipment` | Equipment health data |
| `GET /emissions` | Environmental monitoring |
| `GET /bulk/daily-snapshot` | Complete daily data snapshot |

API documentation: http://localhost:8000/docs

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database user | `dakota` |
| `POSTGRES_PASSWORD` | Database password | `dakota_dev` |
| `POSTGRES_DB` | Database name | `dakota_analytics` |
| `EIA_API_KEY` | EIA API key | Required |
| `API_PORT` | Enrichment API port | `8000` |
| `DAGSTER_PORT` | Dagster UI port | `3000` |

## Development

### Running dbt Locally

```bash
cd dbt
pip install dbt-postgres
dbt deps
dbt run --profiles-dir . --target dev
dbt test --profiles-dir . --target dev
dbt docs generate && dbt docs serve
```

### Running Tests

```bash
# dbt tests
cd dbt && dbt test

# API tests
cd api && pytest

# Integration tests
pytest tests/
```

## Monitoring

- **Dagster UI**: Asset lineage, run history, schedules
- **Ingestion Logs**: `raw.ingestion_log` table
- **dbt Test Results**: Post-transformation validation

## Technology Stack

| Component | Technology |
|-----------|------------|
| Orchestration | Dagster |
| Database | PostgreSQL 15 |
| Transformations | dbt-core |
| API Framework | FastAPI |
| Containerization | Docker Compose |
| Package Management | uv (API), pip (others) |

## Design Decisions

See [docs/decisions.md](docs/decisions.md) for rationale on:
- Why Dagster over Airflow
- PostgreSQL vs. cloud data warehouses
- Medallion architecture benefits
- Synthetic data generation approach

## Future Enhancements

- [ ] Incremental dbt models
- [ ] Streaming ingestion with Kafka
- [ ] CI/CD with GitHub Actions
- [ ] Prometheus/Grafana/OpenSearch monitoring
- [ ] Data contracts for API versioning

## Author

Built as a technical assessment for Dakota Analytics.

## License

MIT
