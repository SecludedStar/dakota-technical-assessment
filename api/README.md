# Energy Facility Enrichment API

FastAPI service that generates synthetic operational data for energy analytics pipelines.

## Features

This API generates realistic synthetic data relevant to oil & gas operations:

- **Wells**: Basic well information including location, operator, basin, and status
- **Production**: Daily production metrics (oil, gas, water volumes, pressures)
- **Equipment**: Equipment health monitoring with predictive maintenance signals
- **Emissions**: Environmental monitoring including methane, CO2, and leak detection
- **Weather**: Weather conditions affecting field operations
- **Bulk Snapshots**: Complete daily operational snapshots for batch ingestion

## Technology Stack

- **Framework**: FastAPI with async support
- **Dependency Management**: uv (fast Python package manager)
- **Validation**: Pydantic v2 for schema validation
- **Containerization**: Docker with multi-stage build

## Local Development

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e ".[dev]"

# Run the server
uvicorn main:app --reload --port 8000
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health status |
| `/wells` | GET | Paginated well information |
| `/wells/{well_id}` | GET | Single well details |
| `/production` | GET | Production records |
| `/equipment` | GET | Equipment status |
| `/emissions` | GET | Emissions monitoring data |
| `/weather` | GET | Weather conditions |
| `/bulk/daily-snapshot` | GET | Complete daily operational snapshot |

## Query Parameters

Most endpoints support:
- `page`: Page number (default: 1)
- `page_size`: Items per page
- `seed`: Random seed for reproducible results (useful for testing)

## Example Requests

```bash
# Get wells in Permian basin
curl "http://localhost:8000/wells?basin=Permian&page_size=10"

# Get production for specific well
curl "http://localhost:8000/production?well_id=42-123-45678&days=7"

# Get daily snapshot with seed for reproducibility
curl "http://localhost:8000/bulk/daily-snapshot?seed=12345"
```

## Docker

```bash
# Build image
docker build -t energy-enrichment-api .

# Run container
docker run -p 8000:8000 energy-enrichment-api
```

## API Documentation

When running, interactive API docs are available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
