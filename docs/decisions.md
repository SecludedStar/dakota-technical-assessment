# Technical Decisions

This document outlines key technology choices and trade-offs made during the implementation.

## Orchestration: Dagster

### Decision
Use Dagster as the orchestration framework.

### Alternatives Considered
- **Apache Airflow**: Industry standard, mature ecosystem
- **Prefect**: Modern Python-native, cloud-first
- **Luigi**: Simple, battle-tested at Spotify

### Rationale
1. **Asset-Centric Model**: Dagster's software-defined assets align naturally with dbt models and data products
2. **First-Class dbt Integration**: `dagster-dbt` provides automatic asset generation from dbt manifests
3. **Modern Developer Experience**: Type hints, local development, excellent testing support
4. **Resource Management**: Clean separation of configuration from business logic
5. **Observability**: Built-in data lineage and materialization tracking
6. **Company Alignment**: If I remember correctly, Dakota Analytics uses Dagster in their stack, making this choice demonstrate familiarity with their preferred tooling

### Trade-offs
- Smaller community than Airflow
- Fewer third-party integrations
- Learning curve for asset-based thinking

## Database: PostgreSQL

### Decision
Use PostgreSQL 15 with a medallion architecture (raw → staging → analytics).

### Alternatives Considered
- **DuckDB**: Embedded analytical database
- **SQLite**: Simpler deployment
- **Cloud DW (Snowflake/BigQuery)**: Production-scale analytics

### Rationale
1. **Familiar & Robust**: PostgreSQL is battle-tested and widely understood
2. **dbt Compatibility**: First-class dbt-postgres adapter
3. **JSONB Support**: Flexible schema for equipment alerts
4. **Local Development**: Easy Docker setup, no cloud dependencies
5. **Scalability Path**: Can migrate to cloud PostgreSQL (RDS, Cloud SQL) or Snowflake

### Trade-offs
- Not optimized for analytical queries at scale
- Requires manual partitioning for large tables
- No native time-series optimizations

## API Framework: FastAPI

### Decision
Build the enrichment API with FastAPI and uv for dependency management.

### Alternatives Considered
- **Flask**: Simple, widely adopted
- **Django REST Framework**: Full-featured, batteries included
- **Starlette**: Lower-level ASGI framework

### Rationale
1. **Performance**: ASGI-based, async-ready for high throughput
2. **Type Safety**: Pydantic integration for request/response validation
3. **Auto Documentation**: OpenAPI/Swagger UI out of the box
4. **Modern Python**: Native type hints, dataclasses support
5. **uv**: Fast dependency resolution, reproducible builds

### Trade-offs
- Requires understanding of async patterns
- Smaller plugin ecosystem than Flask/Django
- uv is newer/less mature than pip

## Transformation: dbt

### Decision
Use dbt-core with PostgreSQL adapter for transformations.

### Alternatives Considered
- **Raw SQL scripts**: Simple, no learning curve
- **SQLMesh**: Open-source alternative with column-level lineage
- **Spark SQL**: Distributed processing

### Rationale
1. **Industry Standard**: dbt is the de facto standard for analytics engineering
2. **Testing Framework**: Built-in data quality tests
3. **Documentation**: Auto-generated docs from schema.yml
4. **Modularity**: ref() and source() macros enable clean dependencies
5. **Dagster Integration**: Seamless asset generation

### Trade-offs
- SQL-only (no Python transformations in core)
- Learning curve for Jinja templating
- Compilation time for large projects

## Data Modeling: Medallion Architecture

### Decision
Implement Bronze/Silver/Gold pattern as raw/staging/analytics schemas.

### Alternatives Considered
- **Flat Schema**: All tables in one schema
- **Kimball Dimensional**: Star schema with facts/dimensions
- **Data Vault**: Hub/Link/Satellite pattern

### Rationale
1. **Simplicity**: Clear progression from raw to refined
2. **Debuggability**: Can inspect data at each layer
3. **Incremental Adoption**: Easy to add new sources
4. **dbt Alignment**: Matches dbt's staging → marts pattern

### Trade-offs
- Additional storage for intermediate layers (can be avoided with ephemeral materialization)
- Potential for schema drift between layers
- Not as flexible as Data Vault for complex integrations

## Containerization: Docker Compose

### Decision
Use Docker Compose for local development and deployment.

### Alternatives Considered
- **Kubernetes**: Production-grade orchestration
- **Bare Metal**: Direct installation on host
- **Podman Compose**: Daemonless alternative

### Rationale
1. **Simplicity**: Single `docker-compose up` starts everything
2. **Reproducibility**: Identical environments across machines
3. **Service Dependencies**: Health checks and startup ordering
4. **Volume Management**: Persistent data across restarts

### Trade-offs
- Not production-ready without additional hardening
- Single-host limitation
- Debugging can be complex

## Synthetic Data Generation

### Decision
Generate synthetic energy sector data with reproducible seeds.

### Alternatives Considered
- **Real EIA Data Only**: Simpler, no generation logic
- **Faker Library**: Generic fake data
- **Database Fixtures**: Static JSON/SQL files

### Rationale
1. **Domain Realism**: Data reflects actual oil & gas operations
2. **Reproducibility**: Seeded random generation for testing
3. **Flexibility**: Configurable volumes and distributions
4. **Demonstration**: Shows ability to model complex domains

### Trade-offs
- Additional development time
- May not capture all real-world edge cases
- Requires domain knowledge validation

## Error Handling: Retry with Exponential Backoff

### Decision
Implement automatic retries with exponential backoff for API calls.

### Rationale
1. **Resilience**: Handles transient failures gracefully
2. **API Politeness**: Respects rate limits with backoff
3. **Observability**: Logged retry attempts for debugging
4. **Configurability**: Adjustable retry counts and delays

### Implementation
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
)
async def fetch_with_retry(self, url: str) -> dict:
    ...
```

## Testing Strategy

### Decision
Multi-layer testing approach.

### Layers
1. **dbt Tests**: Data quality (unique, not_null, accepted_values)
2. **API Tests**: FastAPI TestClient for endpoint validation
3. **Integration Tests**: End-to-end pipeline verification
4. **Unit Tests**: Client and loader logic

### Rationale
- Each layer catches different types of issues
- dbt tests run in production for ongoing quality
- API tests ensure contract compliance
- Integration tests validate full data flow

## Future Considerations

### If Scaling Beyond Prototype

1. **Replace PostgreSQL** with Snowflake or BigQuery for analytical workloads
2. **Add Streaming** with Kafka/Kinesis for real-time enrichment data
3. **Implement CI/CD** with GitHub Actions for dbt and Docker
4. **Add Monitoring** with Prometheus/Grafana, OpenSearch, or DataDog
5. **Implement Data Contracts** for producer/consumer agreements
6. **Add Column-Level Lineage** with SQLMesh or dbt Cloud
