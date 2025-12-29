"""
Database loader for ingesting data into PostgreSQL.

Handles batch inserts with conflict resolution and logging.
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Loads data into PostgreSQL database."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize database loader.
        
        Connection parameters can be passed directly or read from environment variables:
        - POSTGRES_HOST (default: localhost)
        - POSTGRES_PORT (default: 5432)
        - POSTGRES_DB (default: energy_analytics)
        - POSTGRES_USER (default: postgres)
        - POSTGRES_PASSWORD
        """
        self.host = host or os.environ.get("POSTGRES_HOST", "localhost")
        self.port = port or int(os.environ.get("POSTGRES_PORT", "5432"))
        self.database = database or os.environ.get("POSTGRES_DB", "energy_analytics")
        self.user = user or os.environ.get("POSTGRES_USER", "postgres")
        self.password = password or os.environ.get("POSTGRES_PASSWORD", "")
        
        self._conn = None
    
    def connect(self) -> None:
        """Establish database connection."""
        try:
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            self._conn.autocommit = False
            logger.info(f"Connected to database {self.database} at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _execute_batch(
        self,
        table: str,
        columns: list[str],
        data: list[tuple],
        conflict_columns: Optional[list[str]] = None,
        update_columns: Optional[list[str]] = None,
    ) -> int:
        """
        Execute batch insert with optional upsert.
        
        Args:
            table: Target table name
            columns: Column names
            data: List of tuples containing values
            conflict_columns: Columns to check for conflicts (for upsert)
            update_columns: Columns to update on conflict
        
        Returns:
            Number of rows affected
        """
        if not data:
            return 0
        
        columns_str = ", ".join(columns)
        
        query = f"INSERT INTO {table} ({columns_str}) VALUES %s"
        
        # Add ON CONFLICT clause for upsert
        if conflict_columns and update_columns:
            conflict_str = ", ".join(conflict_columns)
            updates = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])
            query += f" ON CONFLICT ({conflict_str}) DO UPDATE SET {updates}"
        elif conflict_columns:
            conflict_str = ", ".join(conflict_columns)
            query += f" ON CONFLICT ({conflict_str}) DO NOTHING"
        
        with self._conn.cursor() as cursor:
            execute_values(cursor, query, data, page_size=1000)
            rows_affected = cursor.rowcount
        
        return rows_affected
    
    def load_eia_natural_gas_prices(self, data: list[dict]) -> int:
        """
        Load EIA natural gas price data.
        
        Args:
            data: List of price records from EIA API
        
        Returns:
            Number of rows loaded
        """
        if not data:
            logger.warning("No natural gas price data to load")
            return 0
        
        rows = []
        for record in data:
            rows.append((
                record.get("period"),
                record.get("duoarea"),
                record.get("area-name"),
                record.get("product"),
                record.get("product-name"),
                record.get("process"),
                record.get("process-name"),
                record.get("series"),
                record.get("series-description"),
                record.get("value"),
                record.get("units"),
                datetime.now(),
            ))
        
        columns = [
            "period", "duoarea", "area_name", "product", "product_name",
            "process", "process_name", "series", "series_description",
            "value", "units", "ingested_at"
        ]
        
        try:
            rows_affected = self._execute_batch(
                table="raw.eia_natural_gas_prices",
                columns=columns,
                data=rows,
                conflict_columns=["period", "series"],
                update_columns=["value", "ingested_at"],
            )
            self._conn.commit()
            logger.info(f"Loaded {rows_affected} natural gas price records")
            return rows_affected
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to load natural gas prices: {e}")
            raise
    
    def load_eia_petroleum_prices(self, data: list[dict]) -> int:
        """Load EIA petroleum price data."""
        if not data:
            logger.warning("No petroleum price data to load")
            return 0
        
        rows = []
        for record in data:
            rows.append((
                record.get("period"),
                record.get("duoarea"),
                record.get("area-name"),
                record.get("product"),
                record.get("product-name"),
                record.get("series"),
                record.get("series-description"),
                record.get("value"),
                record.get("units"),
                datetime.now(),
            ))
        
        columns = [
            "period", "duoarea", "area_name", "product", "product_name",
            "series", "series_description", "value", "units", "ingested_at"
        ]
        
        try:
            rows_affected = self._execute_batch(
                table="raw.eia_petroleum_prices",
                columns=columns,
                data=rows,
                conflict_columns=["period", "series"],
                update_columns=["value", "ingested_at"],
            )
            self._conn.commit()
            logger.info(f"Loaded {rows_affected} petroleum price records")
            return rows_affected
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to load petroleum prices: {e}")
            raise
    
    def load_wells(self, data: list[dict]) -> int:
        """Load well information from enrichment API."""
        if not data:
            logger.warning("No well data to load")
            return 0
        
        rows = []
        for record in data:
            rows.append((
                record.get("well_id"),
                record.get("well_name"),
                record.get("operator"),
                record.get("basin"),
                record.get("state"),
                record.get("latitude"),
                record.get("longitude"),
                record.get("well_type"),
                record.get("spud_date"),
                record.get("status"),
                datetime.now(),
            ))
        
        columns = [
            "well_id", "well_name", "operator", "basin", "state",
            "latitude", "longitude", "well_type", "spud_date", "status",
            "ingested_at"
        ]
        
        try:
            rows_affected = self._execute_batch(
                table="raw.wells",
                columns=columns,
                data=rows,
                conflict_columns=["well_id"],
                update_columns=["well_name", "operator", "status", "ingested_at"],
            )
            self._conn.commit()
            logger.info(f"Loaded {rows_affected} well records")
            return rows_affected
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to load wells: {e}")
            raise
    
    def load_production(self, data: list[dict]) -> int:
        """Load production records from enrichment API."""
        if not data:
            logger.warning("No production data to load")
            return 0
        
        rows = []
        for record in data:
            rows.append((
                record.get("well_id"),
                record.get("production_date"),
                record.get("oil_bbl"),
                record.get("gas_mcf"),
                record.get("water_bbl"),
                record.get("uptime_hours"),
                record.get("choke_size"),
                record.get("tubing_pressure_psi"),
                record.get("casing_pressure_psi"),
                datetime.now(),
            ))
        
        columns = [
            "well_id", "production_date", "oil_bbl", "gas_mcf", "water_bbl",
            "uptime_hours", "choke_size", "tubing_pressure_psi", "casing_pressure_psi",
            "ingested_at"
        ]
        
        try:
            rows_affected = self._execute_batch(
                table="raw.production",
                columns=columns,
                data=rows,
                conflict_columns=["well_id", "production_date"],
                update_columns=["oil_bbl", "gas_mcf", "water_bbl", "uptime_hours", "ingested_at"],
            )
            self._conn.commit()
            logger.info(f"Loaded {rows_affected} production records")
            return rows_affected
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to load production: {e}")
            raise
    
    def load_equipment(self, data: list[dict]) -> int:
        """Load equipment status records from enrichment API."""
        if not data:
            logger.warning("No equipment data to load")
            return 0
        
        rows = []
        for record in data:
            rows.append((
                record.get("equipment_id"),
                record.get("well_id"),
                record.get("equipment_type"),
                record.get("manufacturer"),
                record.get("install_date"),
                record.get("last_maintenance"),
                record.get("next_maintenance"),
                record.get("health_score"),
                record.get("status"),
                record.get("runtime_hours"),
                json.dumps(record.get("alerts", [])),
                datetime.now(),
            ))
        
        columns = [
            "equipment_id", "well_id", "equipment_type", "manufacturer",
            "install_date", "last_maintenance", "next_maintenance",
            "health_score", "status", "runtime_hours", "alerts", "ingested_at"
        ]
        
        try:
            rows_affected = self._execute_batch(
                table="raw.equipment",
                columns=columns,
                data=rows,
                conflict_columns=["equipment_id"],
                update_columns=[
                    "last_maintenance", "next_maintenance", "health_score",
                    "status", "runtime_hours", "alerts", "ingested_at"
                ],
            )
            self._conn.commit()
            logger.info(f"Loaded {rows_affected} equipment records")
            return rows_affected
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to load equipment: {e}")
            raise
    
    def load_emissions(self, data: list[dict]) -> int:
        """Load emissions records from enrichment API."""
        if not data:
            logger.warning("No emissions data to load")
            return 0
        
        rows = []
        for record in data:
            rows.append((
                record.get("well_id"),
                record.get("measurement_date"),
                record.get("methane_kg"),
                record.get("co2_kg"),
                record.get("voc_kg"),
                record.get("flare_volume_mcf"),
                record.get("leak_detected"),
                record.get("measurement_method"),
                datetime.now(),
            ))
        
        columns = [
            "well_id", "measurement_date", "methane_kg", "co2_kg", "voc_kg",
            "flare_volume_mcf", "leak_detected", "measurement_method", "ingested_at"
        ]
        
        try:
            rows_affected = self._execute_batch(
                table="raw.emissions",
                columns=columns,
                data=rows,
                conflict_columns=["well_id", "measurement_date"],
                update_columns=[
                    "methane_kg", "co2_kg", "voc_kg", "flare_volume_mcf",
                    "leak_detected", "ingested_at"
                ],
            )
            self._conn.commit()
            logger.info(f"Loaded {rows_affected} emissions records")
            return rows_affected
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to load emissions: {e}")
            raise
    
    def log_ingestion_run(
        self,
        source: str,
        status: str,
        records_count: int,
        duration_seconds: float,
        error_message: Optional[str] = None,
    ) -> None:
        """Log an ingestion run to the metadata table."""
        query = """
            INSERT INTO raw.ingestion_log 
            (source, status, records_count, duration_seconds, error_message, run_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self._conn.cursor() as cursor:
                cursor.execute(query, (
                    source,
                    status,
                    records_count,
                    duration_seconds,
                    error_message,
                    datetime.now(),
                ))
            self._conn.commit()
            logger.info(f"Logged ingestion run for {source}: {status}")
        except Exception as e:
            self._conn.rollback()
            logger.error(f"Failed to log ingestion run: {e}")


if __name__ == "__main__":
    # Example usage
    with DatabaseLoader() as loader:
        print("Database loader initialized")
