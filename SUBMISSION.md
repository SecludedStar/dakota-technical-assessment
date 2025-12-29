# Submission Checklist

## Before Submitting

### 1. Implementation Status
- [x] All six components implemented (API, ingestion, orchestration, database, dbt, reports)
- [x] Documentation created in `/docs/` folder
- [x] `run.sh` startup script with required commands
- [x] Tests written (pytest + dbt tests)

### 2. Test in Clean Environment
```bash
# Remove everything and test from scratch
./run.sh clean
rm -rf __pycache__/ .pytest_cache/ dbt/target/ dbt/logs/

# Test the full flow
./run.sh start      # Build and start all services
./run.sh pipeline   # Run complete data pipeline
./run.sh status     # Verify services are running
```

### 3. Verify Deliverables

Check your repository includes:
- [x] `run.sh` with: start, stop, pipeline, dbt, reports, clean
- [x] `docker-compose.yml` with all services (postgres, api, dagster-webserver, dagster-daemon)
- [x] `.env.example` with all required variables
- [x] `docs/architecture.md` - system architecture and design
- [x] `docs/decisions.md` - technical decisions and rationale
- [x] `docs/er_diagram.md` - database schema diagram (Mermaid format)
- [x] `README.md` - setup instructions and project overview
- [x] All source code properly organized
- [x] Tests included (`tests/`, dbt tests)

### 4. Final Checks
- [x] Repository is **public**
- [x] No sensitive data committed (API keys in `.env`, not committed)
- [x] `.env` is in `.gitignore`
- [ ] `./run.sh start && ./run.sh pipeline` works from fresh clone

## How to Submit

Email to: **technical-assessment@dakotaanalytics.com**

**Subject:** Technical Assessment Submission - [Your Name]

**Body:**
```
Name: [Your Full Name]
GitHub Repository: https://github.com/SecludedStar/dakota-technical-assessment
Orchestration Tool: Dagster

Brief Summary:
Built a production-ready energy analytics pipeline using a medallion architecture.
Data flows from EIA API and a custom FastAPI enrichment service through PostgreSQL,
transformed via dbt (staging → intermediate → marts), orchestrated by Dagster,
with automated Excel/PDF/Jupyter report generation.

Time Spent: [X hours]
```

## What They'll Do

1. Clone your repository
2. Review your documentation (`docs/architecture.md`, `docs/decisions.md`)
3. Run `./run.sh start && ./run.sh pipeline`
4. Examine generated reports in `reports/output/`
5. Review code, tests, and architecture
6. Evaluate based on criteria in assignment README

## Quick Verification

```bash
# Verify key files exist
ls -la run.sh docker-compose.yml .env.example
ls -la docs/architecture.md docs/decisions.md docs/er_diagram.md
ls -la api/main.py ingestion/eia_client.py orchestration/__init__.py
ls -la dbt/dbt_project.yml database/init.sql reports/report_generator.py
```

## Access Points (after `./run.sh start`)

| Service | URL |
|---------|-----|
| Dagster UI | http://localhost:3000 |
| Enrichment API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
