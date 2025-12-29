# Data Ingestion Clients

Python clients for fetching data from external sources and loading into PostgreSQL.

## Components

### Base Client (`base_client.py`)
Abstract base class providing:
- HTTP client with connection pooling
- Exponential backoff retry logic
- Standardized error handling
- Logging infrastructure

### EIA Client (`eia_client.py`)
Client for U.S. Energy Information Administration API v2:
- Natural gas prices and storage
- Petroleum prices (Brent, WTI)
- Crude oil production data

### Enrichment Client (`enrichment_client.py`)
Client for the FastAPI enrichment service:
- Well information
- Daily production metrics
- Equipment status and maintenance
- Emissions monitoring data
- Bulk daily snapshots

### Database Loader (`db_loader.py`)
PostgreSQL loader with:
- Batch inserts with `execute_values`
- Upsert support with conflict resolution
- Transaction management
- Ingestion run logging

## Usage

```python
from eia_client import EIAClient
from enrichment_client import EnrichmentClient
from db_loader import DatabaseLoader

# Fetch EIA data
with EIAClient() as eia:
    result = eia.fetch_natural_gas_prices(start="2024-01", end="2024-06")
    if result.success:
        print(f"Fetched {result.records_count} records")

# Fetch enrichment data
with EnrichmentClient() as enrichment:
    result = enrichment.fetch_daily_snapshot(seed=12345)
    if result.success:
        data = result.metadata

# Load to database
with DatabaseLoader() as loader:
    loader.load_wells(data["wells"])
    loader.load_production(data["production"])
```

## Configuration

Environment variables:
- `EIA_API_KEY`: EIA API key (register at https://www.eia.gov/opendata/)
- `ENRICHMENT_API_URL`: FastAPI service URL (default: http://localhost:8000)
- `POSTGRES_HOST`: Database host (default: localhost)
- `POSTGRES_PORT`: Database port (default: 5432)
- `POSTGRES_DB`: Database name (default: energy_analytics)
- `POSTGRES_USER`: Database user (default: postgres)
- `POSTGRES_PASSWORD`: Database password

## Error Handling

All clients implement:
- Automatic retries with exponential backoff
- HTTP status code handling (429, 5xx trigger retries)
- Connection timeout management
- Comprehensive logging

The `IngestionResult` dataclass provides:
- Success/failure status
- Record counts
- Duration timing
- Error messages for debugging
