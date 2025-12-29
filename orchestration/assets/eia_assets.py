"""
Dagster assets for EIA data ingestion.

These assets fetch data from the EIA API and load it into PostgreSQL.
"""

import os
import sys
from datetime import datetime, timedelta

from dagster import (
    asset,
    AssetExecutionContext,
    MetadataValue,
    MaterializeResult,
    
    Failure,
)

# Add ingestion module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ingestion"))

from eia_client import EIAClient
from db_loader import DatabaseLoader


@asset(
    group_name="raw_eia",
    description="Natural gas prices from EIA API",
    compute_kind="python",
)
def eia_natural_gas_prices(context: AssetExecutionContext) -> dict:
    """
    Ingest natural gas price data from EIA API.
    
    Fetches monthly natural gas price summary data and loads it into
    the raw.eia_natural_gas_prices table.
    """
    start_time = datetime.now()
    
    # Calculate date range (last 2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    context.log.info(f"Fetching natural gas prices from {start_date:%Y-%m} to {end_date:%Y-%m}")
    
    # Fetch data from EIA
    with EIAClient() as client:
        if not client.health_check():
            context.log.warning("EIA API health check failed, proceeding anyway")
        
        result = client.fetch_natural_gas_prices(
            start=start_date.strftime("%Y-%m"),
            end=end_date.strftime("%Y-%m"),
            length=5000,
        )
    
    if not result.success:
        raise Failure(
            description=f"Failed to fetch natural gas prices: {result.error_message}",
            metadata={"error": result.error_message},
        )
    
    data = result.metadata.get("data", [])
    context.log.info(f"Fetched {len(data)} natural gas price records")
    
    # Load into database
    rows_loaded = 0
    if data:
        with DatabaseLoader() as loader:
            rows_loaded = loader.load_eia_natural_gas_prices(data)
            loader.log_ingestion_run(
                source="eia_natural_gas_prices",
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
            "date_range": {
                "start": start_date.strftime("%Y-%m"),
                "end": end_date.strftime("%Y-%m"),
            },
        },
        metadata={
            "records_fetched": MetadataValue.int(len(data)),
            "rows_loaded": MetadataValue.int(rows_loaded),
            "duration_seconds": MetadataValue.float(duration),
            "date_range_start": MetadataValue.text(start_date.strftime("%Y-%m")),
            "date_range_end": MetadataValue.text(end_date.strftime("%Y-%m")),
        },
    )


@asset(
    group_name="raw_eia",
    description="Petroleum spot prices from EIA API (Brent and WTI crude)",
    compute_kind="python",
)
def eia_petroleum_prices(context: AssetExecutionContext) -> dict:
    """
    Ingest petroleum spot price data from EIA API.
    
    Fetches daily Brent and WTI crude oil spot prices and loads them
    into the raw.eia_petroleum_prices table.
    """
    start_time = datetime.now()
    
    # Calculate date range (last year for daily data)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    context.log.info(f"Fetching petroleum prices from {start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}")
    
    all_data = []
    
    with EIAClient() as client:
        # Fetch Brent crude prices
        brent_result = client.fetch_petroleum_prices(
            product="EPCBRENT",
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            length=5000,
        )
        
        if brent_result.success:
            brent_data = brent_result.metadata.get("data", [])
            all_data.extend(brent_data)
            context.log.info(f"Fetched {len(brent_data)} Brent crude price records")
        else:
            context.log.warning(f"Failed to fetch Brent prices: {brent_result.error_message}")
        
        # Fetch WTI crude prices
        wti_result = client.fetch_petroleum_prices(
            product="EPCWTI",
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            length=5000,
        )
        
        if wti_result.success:
            wti_data = wti_result.metadata.get("data", [])
            all_data.extend(wti_data)
            context.log.info(f"Fetched {len(wti_data)} WTI crude price records")
        else:
            context.log.warning(f"Failed to fetch WTI prices: {wti_result.error_message}")
    
    if not all_data:
        raise Failure(
            description="Failed to fetch any petroleum price data",
            metadata={"brent_error": brent_result.error_message, "wti_error": wti_result.error_message},
        )
    
    # Load into database
    rows_loaded = 0
    with DatabaseLoader() as loader:
        rows_loaded = loader.load_eia_petroleum_prices(all_data)
        loader.log_ingestion_run(
            source="eia_petroleum_prices",
            status="success",
            records_count=rows_loaded,
            duration_seconds=(datetime.now() - start_time).total_seconds(),
        )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "records_fetched": len(all_data),
            "rows_loaded": rows_loaded,
            "duration_seconds": duration,
        },
        metadata={
            "records_fetched": MetadataValue.int(len(all_data)),
            "rows_loaded": MetadataValue.int(rows_loaded),
            "duration_seconds": MetadataValue.float(duration),
            "products": MetadataValue.text("EPCBRENT, EPCWTI"),
        },
    )


# Asset checks
@asset(
    group_name="checks",
    deps=[eia_natural_gas_prices],
    description="Data quality checks for EIA natural gas prices",
    compute_kind="python",
)
def eia_natural_gas_quality_check(context: AssetExecutionContext) -> dict:
    """Run data quality checks on EIA natural gas prices."""
    
    with DatabaseLoader() as loader:
        loader.connect()
        
        with loader._conn.cursor() as cursor:
            # Check record count
            cursor.execute("SELECT COUNT(*) FROM raw.eia_natural_gas_prices")
            total_count = cursor.fetchone()[0]
            
            # Check for recent data (within last 3 months)
            cursor.execute("""
                SELECT COUNT(*) FROM raw.eia_natural_gas_prices 
                WHERE period >= to_char(NOW() - INTERVAL '3 months', 'YYYY-MM')
            """)
            recent_count = cursor.fetchone()[0]
            
            # Check for null values
            cursor.execute("""
                SELECT COUNT(*) FROM raw.eia_natural_gas_prices 
                WHERE value IS NULL
            """)
            null_count = cursor.fetchone()[0]
    
    checks_passed = total_count > 0 and recent_count > 0 and null_count == 0
    
    return MaterializeResult(
        value={
            "total_records": total_count,
            "recent_records": recent_count,
            "null_values": null_count,
            "checks_passed": checks_passed,
        },
        metadata={
            "total_records": MetadataValue.int(total_count),
            "recent_records": MetadataValue.int(recent_count),
            "null_values": MetadataValue.int(null_count),
            "checks_passed": MetadataValue.bool(checks_passed),
        },
    )
