"""
Dagster jobs and schedules for the energy analytics pipeline.

Jobs define groups of assets to materialize together.
Schedules define when jobs should run automatically.
"""

from dagster import (
    define_asset_job,
    AssetSelection,
    ScheduleDefinition,
    DefaultScheduleStatus,
)


# =============================================================================
# Job Definitions
# =============================================================================

# Daily batch job: EIA data + dbt transformations + reports
daily_batch_job = define_asset_job(
    name="daily_batch_pipeline",
    description="Daily batch pipeline: EIA ingestion → dbt transforms → reports",
    selection=AssetSelection.groups("raw_eia", "dbt_staging", "dbt_intermediate", "dbt_marts", "dbt_tests", "reports"),
)

# Hourly enrichment job: FastAPI data
hourly_enrichment_job = define_asset_job(
    name="hourly_enrichment_pipeline",
    description="Hourly ingestion from FastAPI enrichment service",
    selection=AssetSelection.groups("raw_enrichment"),
)

# Full pipeline job: Everything
# Excludes layer-specific dbt assets to avoid conflicts with dbt_run_all
full_pipeline_job = define_asset_job(
    name="full_pipeline",
    description="Full pipeline execution: all sources → transforms → reports",
    selection=(
        AssetSelection.all()
        - AssetSelection.assets("dbt_staging_models", "dbt_intermediate_models", "dbt_mart_models")
    ),
)

# dbt-only job: Just transformations
dbt_transform_job = define_asset_job(
    name="dbt_transforms",
    description="Run all dbt transformations",
    selection=AssetSelection.groups("dbt_deps", "dbt_staging", "dbt_intermediate", "dbt_marts", "dbt_tests"),
)

# Reports-only job
reports_job = define_asset_job(
    name="reports_generation",
    description="Generate all reports from existing data",
    selection=AssetSelection.groups("reports"),
)

# Data quality job
data_quality_job = define_asset_job(
    name="data_quality_checks",
    description="Run data quality checks",
    selection=AssetSelection.groups("checks", "dbt_tests"),
)


# =============================================================================
# Schedule Definitions
# =============================================================================

# Daily batch at 6 AM UTC
daily_batch_schedule = ScheduleDefinition(
    name="daily_batch_schedule",
    job=daily_batch_job,
    cron_schedule="0 6 * * *",  # 6 AM daily
    default_status=DefaultScheduleStatus.STOPPED,
    description="Runs the daily batch pipeline at 6 AM UTC",
)

# Hourly enrichment
hourly_enrichment_schedule = ScheduleDefinition(
    name="hourly_enrichment_schedule",
    job=hourly_enrichment_job,
    cron_schedule="0 * * * *",  # Every hour
    default_status=DefaultScheduleStatus.STOPPED,
    description="Runs enrichment ingestion every hour",
)

# Weekly full pipeline (Sunday at 2 AM)
weekly_full_schedule = ScheduleDefinition(
    name="weekly_full_schedule",
    job=full_pipeline_job,
    cron_schedule="0 2 * * 0",  # 2 AM on Sundays
    default_status=DefaultScheduleStatus.STOPPED,
    description="Runs the full pipeline weekly on Sunday at 2 AM UTC",
)


# =============================================================================
# Export all jobs and schedules
# =============================================================================

all_jobs = [
    daily_batch_job,
    hourly_enrichment_job,
    full_pipeline_job,
    dbt_transform_job,
    reports_job,
    data_quality_job,
]

all_schedules = [
    daily_batch_schedule,
    hourly_enrichment_schedule,
    weekly_full_schedule,
]
