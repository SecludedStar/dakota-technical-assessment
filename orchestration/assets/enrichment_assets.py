"""
Dagster assets for enrichment API data ingestion.

These assets fetch synthetic operational data from the FastAPI service
and load it into PostgreSQL.
"""

import os
import sys
from datetime import datetime

from dagster import (
    asset,
    AssetExecutionContext,
    MetadataValue,
    MaterializeResult,
    Failure,
)

# Add ingestion module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ingestion"))

from enrichment_client import EnrichmentClient
from db_loader import DatabaseLoader


@asset(
    group_name="raw_enrichment",
    description="Well information from enrichment API",
    compute_kind="python",
)
def enrichment_wells(context: AssetExecutionContext) -> dict:
    """
    Ingest well information from the FastAPI enrichment service.
    
    Fetches well master data including location, operator, and status.
    """
    start_time = datetime.now()
    context.log.info("Fetching wells from enrichment API")
    
    with EnrichmentClient() as client:
        if not client.health_check():
            raise Failure(
                description="Enrichment API health check failed",
                metadata={"api_url": client.base_url},
            )
        
        result = client.fetch_wells(page_size=100)
    
    if not result.success:
        raise Failure(
            description=f"Failed to fetch wells: {result.error_message}",
            metadata={"error": result.error_message},
        )
    
    data = result.metadata.get("data", [])
    context.log.info(f"Fetched {len(data)} well records")
    
    # Load into database
    rows_loaded = 0
    if data:
        with DatabaseLoader() as loader:
            rows_loaded = loader.load_wells(data)
            loader.log_ingestion_run(
                source="enrichment_wells",
                status="success",
                records_count=rows_loaded,
                duration_seconds=result.duration_seconds,
            )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "records_fetched": len(data),
            "rows_loaded": rows_loaded,
            "duration_seconds": duration,
        },
        metadata={
            "records_fetched": MetadataValue.int(len(data)),
            "rows_loaded": MetadataValue.int(rows_loaded),
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="raw_enrichment",
    description="Daily production data from enrichment API",
    compute_kind="python",
    deps=[enrichment_wells],  # Production depends on wells existing
)
def enrichment_production(context: AssetExecutionContext) -> dict:
    """
    Ingest production data from the FastAPI enrichment service.
    
    Fetches daily production metrics including oil, gas, and water volumes.
    """
    start_time = datetime.now()
    context.log.info("Fetching production data from enrichment API")
    
    with EnrichmentClient() as client:
        result = client.fetch_production(page_size=500)
    
    if not result.success:
        raise Failure(
            description=f"Failed to fetch production: {result.error_message}",
            metadata={"error": result.error_message},
        )
    
    data = result.metadata.get("data", [])
    context.log.info(f"Fetched {len(data)} production records")
    
    # Load into database
    rows_loaded = 0
    if data:
        with DatabaseLoader() as loader:
            rows_loaded = loader.load_production(data)
            loader.log_ingestion_run(
                source="enrichment_production",
                status="success",
                records_count=rows_loaded,
                duration_seconds=result.duration_seconds,
            )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "records_fetched": len(data),
            "rows_loaded": rows_loaded,
            "duration_seconds": duration,
        },
        metadata={
            "records_fetched": MetadataValue.int(len(data)),
            "rows_loaded": MetadataValue.int(rows_loaded),
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="raw_enrichment",
    description="Equipment health data from enrichment API",
    compute_kind="python",
    deps=[enrichment_wells],  # Equipment depends on wells existing
)
def enrichment_equipment(context: AssetExecutionContext) -> dict:
    """
    Ingest equipment health data from the FastAPI enrichment service.
    
    Fetches equipment status, maintenance schedules, and health scores.
    """
    start_time = datetime.now()
    context.log.info("Fetching equipment data from enrichment API")
    
    with EnrichmentClient() as client:
        result = client.fetch_equipment(page_size=200)
    
    if not result.success:
        raise Failure(
            description=f"Failed to fetch equipment: {result.error_message}",
            metadata={"error": result.error_message},
        )
    
    data = result.metadata.get("data", [])
    context.log.info(f"Fetched {len(data)} equipment records")
    
    # Load into database
    rows_loaded = 0
    if data:
        with DatabaseLoader() as loader:
            rows_loaded = loader.load_equipment(data)
            loader.log_ingestion_run(
                source="enrichment_equipment",
                status="success",
                records_count=rows_loaded,
                duration_seconds=result.duration_seconds,
            )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "records_fetched": len(data),
            "rows_loaded": rows_loaded,
            "duration_seconds": duration,
        },
        metadata={
            "records_fetched": MetadataValue.int(len(data)),
            "rows_loaded": MetadataValue.int(rows_loaded),
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="raw_enrichment",
    description="Emissions monitoring data from enrichment API",
    compute_kind="python",
    deps=[enrichment_wells],  # Emissions depends on wells existing
)
def enrichment_emissions(context: AssetExecutionContext) -> dict:
    """
    Ingest emissions data from the FastAPI enrichment service.
    
    Fetches environmental monitoring data including methane, CO2, and VOC emissions.
    """
    start_time = datetime.now()
    context.log.info("Fetching emissions data from enrichment API")
    
    with EnrichmentClient() as client:
        result = client.fetch_emissions(page_size=500)
    
    if not result.success:
        raise Failure(
            description=f"Failed to fetch emissions: {result.error_message}",
            metadata={"error": result.error_message},
        )
    
    data = result.metadata.get("data", [])
    context.log.info(f"Fetched {len(data)} emissions records")
    
    # Load into database
    rows_loaded = 0
    if data:
        with DatabaseLoader() as loader:
            rows_loaded = loader.load_emissions(data)
            loader.log_ingestion_run(
                source="enrichment_emissions",
                status="success",
                records_count=rows_loaded,
                duration_seconds=result.duration_seconds,
            )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "records_fetched": len(data),
            "rows_loaded": rows_loaded,
            "duration_seconds": duration,
        },
        metadata={
            "records_fetched": MetadataValue.int(len(data)),
            "rows_loaded": MetadataValue.int(rows_loaded),
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="raw_enrichment",
    description="Complete daily snapshot from enrichment API (bulk load)",
    compute_kind="python",
)
def enrichment_daily_snapshot(context: AssetExecutionContext) -> dict:
    """
    Ingest a complete daily operational snapshot from the enrichment API.
    
    This is a bulk load that fetches wells, production, equipment, and emissions
    in a single request, ensuring data consistency across all tables.
    """
    start_time = datetime.now()
    
    # Use date-based seed for reproducibility within the same day
    seed = int(datetime.now().strftime("%Y%m%d"))
    context.log.info(f"Fetching daily snapshot with seed {seed}")
    
    with EnrichmentClient() as client:
        if not client.health_check():
            raise Failure(
                description="Enrichment API health check failed",
                metadata={"api_url": client.base_url},
            )
        
        result = client.fetch_daily_snapshot(seed=seed)
    
    if not result.success:
        raise Failure(
            description=f"Failed to fetch daily snapshot: {result.error_message}",
            metadata={"error": result.error_message},
        )
    
    # fetch_daily_snapshot returns data directly in metadata, not nested under "data"
    wells_data = result.metadata.get("wells", [])
    production_data = result.metadata.get("production", [])
    equipment_data = result.metadata.get("equipment", [])
    emissions_data = result.metadata.get("emissions", [])
    
    context.log.info(
        f"Snapshot contains: {len(wells_data)} wells, {len(production_data)} production, "
        f"{len(equipment_data)} equipment, {len(emissions_data)} emissions"
    )
    
    # Load all data
    rows_summary = {}
    with DatabaseLoader() as loader:
        if wells_data:
            rows_summary["wells"] = loader.load_wells(wells_data)
        if production_data:
            rows_summary["production"] = loader.load_production(production_data)
        if equipment_data:
            rows_summary["equipment"] = loader.load_equipment(equipment_data)
        if emissions_data:
            rows_summary["emissions"] = loader.load_emissions(emissions_data)
        
        total_rows = sum(rows_summary.values())
        loader.log_ingestion_run(
            source="enrichment_daily_snapshot",
            status="success",
            records_count=total_rows,
            duration_seconds=(datetime.now() - start_time).total_seconds(),
        )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "seed": seed,
            "rows_loaded": rows_summary,
            "total_rows": total_rows,
            "duration_seconds": duration,
        },
        metadata={
            "seed": MetadataValue.int(seed),
            "wells_loaded": MetadataValue.int(rows_summary.get("wells", 0)),
            "production_loaded": MetadataValue.int(rows_summary.get("production", 0)),
            "equipment_loaded": MetadataValue.int(rows_summary.get("equipment", 0)),
            "emissions_loaded": MetadataValue.int(rows_summary.get("emissions", 0)),
            "total_rows": MetadataValue.int(total_rows),
            "duration_seconds": MetadataValue.float(duration),
        },
    )
