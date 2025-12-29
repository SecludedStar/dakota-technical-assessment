"""
Client for the FastAPI Energy Facility Enrichment service.

Fetches synthetic operational data including wells, production, equipment, and emissions.
"""

import os
from datetime import datetime
from typing import Optional

from base_client import BaseClient, IngestionResult


class EnrichmentClient(BaseClient):
    """Client for fetching data from the Energy Facility Enrichment API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize enrichment client.
        
        Args:
            base_url: API base URL. Defaults to ENRICHMENT_API_URL env var or localhost.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
        """
        url = base_url or os.environ.get("ENRICHMENT_API_URL", "http://localhost:8000")
        super().__init__(
            base_url=url,
            timeout=timeout,
            max_retries=max_retries,
        )
    
    def health_check(self) -> bool:
        """Check if enrichment API is healthy."""
        try:
            response = self.get("/health")
            return response.get("status") == "healthy"
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def fetch_wells(
        self,
        page: int = 1,
        page_size: int = 100,
        basin: Optional[str] = None,
        operator: Optional[str] = None,
        status: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> IngestionResult:
        """
        Fetch well information.
        
        Args:
            page: Page number
            page_size: Records per page
            basin: Filter by basin name
            operator: Filter by operator
            status: Filter by well status
            seed: Random seed for reproducibility
        
        Returns:
            IngestionResult with well data
        """
        start_time = datetime.now()
        
        try:
            params = {
                "page": page,
                "page_size": page_size,
            }
            if basin:
                params["basin"] = basin
            if operator:
                params["operator"] = operator
            if status:
                params["status"] = status
            if seed is not None:
                params["seed"] = seed
            
            response = self.get("/wells", params=params)
            
            data = response.get("data", [])
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Fetched {len(data)} well records")
            
            return IngestionResult(
                success=True,
                records_count=len(data),
                source="enrichment_wells",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                metadata={
                    "total_count": response.get("total_count", 0),
                    "has_more": response.get("has_more", False),
                    "data": data,
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Failed to fetch wells: {e}")
            
            return IngestionResult(
                success=False,
                records_count=0,
                source="enrichment_wells",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                error_message=str(e),
            )
    
    def fetch_production(
        self,
        well_id: Optional[str] = None,
        days: int = 30,
        page: int = 1,
        page_size: int = 500,
    ) -> IngestionResult:
        """
        Fetch production records.
        
        Args:
            well_id: Filter by specific well
            days: Number of days of history
            page: Page number
            page_size: Records per page
        
        Returns:
            IngestionResult with production data
        """
        start_time = datetime.now()
        
        try:
            params = {
                "days": days,
                "page": page,
                "page_size": page_size,
            }
            if well_id:
                params["well_id"] = well_id
            
            response = self.get("/production", params=params)
            
            data = response.get("data", [])
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Fetched {len(data)} production records")
            
            return IngestionResult(
                success=True,
                records_count=len(data),
                source="enrichment_production",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                metadata={
                    "total_count": response.get("total_count", 0),
                    "data": data,
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Failed to fetch production: {e}")
            
            return IngestionResult(
                success=False,
                records_count=0,
                source="enrichment_production",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                error_message=str(e),
            )
    
    def fetch_equipment(
        self,
        well_id: Optional[str] = None,
        status: Optional[str] = None,
        equipment_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 200,
    ) -> IngestionResult:
        """
        Fetch equipment status records.
        
        Args:
            well_id: Filter by specific well
            status: Filter by equipment status
            equipment_type: Filter by equipment type
            page: Page number
            page_size: Records per page
        
        Returns:
            IngestionResult with equipment data
        """
        start_time = datetime.now()
        
        try:
            params = {
                "page": page,
                "page_size": page_size,
            }
            if well_id:
                params["well_id"] = well_id
            if status:
                params["status"] = status
            if equipment_type:
                params["equipment_type"] = equipment_type
            
            response = self.get("/equipment", params=params)
            
            data = response.get("data", [])
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Fetched {len(data)} equipment records")
            
            return IngestionResult(
                success=True,
                records_count=len(data),
                source="enrichment_equipment",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                metadata={
                    "total_count": response.get("total_count", 0),
                    "data": data,
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Failed to fetch equipment: {e}")
            
            return IngestionResult(
                success=False,
                records_count=0,
                source="enrichment_equipment",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                error_message=str(e),
            )
    
    def fetch_emissions(
        self,
        well_id: Optional[str] = None,
        days: int = 30,
        leak_detected: Optional[bool] = None,
        page: int = 1,
        page_size: int = 500,
    ) -> IngestionResult:
        """
        Fetch emissions monitoring records.
        
        Args:
            well_id: Filter by specific well
            days: Number of days of history
            leak_detected: Filter by leak detection status
            page: Page number
            page_size: Records per page
        
        Returns:
            IngestionResult with emissions data
        """
        start_time = datetime.now()
        
        try:
            params = {
                "days": days,
                "page": page,
                "page_size": page_size,
            }
            if well_id:
                params["well_id"] = well_id
            if leak_detected is not None:
                params["leak_detected"] = str(leak_detected).lower()
            
            response = self.get("/emissions", params=params)
            
            data = response.get("data", [])
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Fetched {len(data)} emissions records")
            
            return IngestionResult(
                success=True,
                records_count=len(data),
                source="enrichment_emissions",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                metadata={
                    "total_count": response.get("total_count", 0),
                    "data": data,
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Failed to fetch emissions: {e}")
            
            return IngestionResult(
                success=False,
                records_count=0,
                source="enrichment_emissions",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                error_message=str(e),
            )
    
    def fetch_daily_snapshot(
        self,
        snapshot_date: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> IngestionResult:
        """
        Fetch complete daily operational snapshot.
        
        This is the primary method for batch ingestion, providing all
        operational data in a single request.
        
        Args:
            snapshot_date: Date in YYYY-MM-DD format
            seed: Random seed for reproducibility
        
        Returns:
            IngestionResult with complete snapshot data
        """
        start_time = datetime.now()
        
        try:
            params = {}
            if snapshot_date:
                params["snapshot_date"] = snapshot_date
            if seed is not None:
                params["seed"] = seed
            
            response = self.get("/bulk/daily-snapshot", params=params)
            
            # Count total records across all categories
            total_records = (
                len(response.get("wells", [])) +
                len(response.get("production", [])) +
                len(response.get("equipment", [])) +
                len(response.get("emissions", []))
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                f"Fetched daily snapshot with {total_records} total records "
                f"({response.get('summary', {}).get('total_wells', 0)} wells)"
            )
            
            return IngestionResult(
                success=True,
                records_count=total_records,
                source="enrichment_daily_snapshot",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                metadata={
                    "snapshot_date": response.get("snapshot_date"),
                    "summary": response.get("summary", {}),
                    "wells": response.get("wells", []),
                    "production": response.get("production", []),
                    "equipment": response.get("equipment", []),
                    "emissions": response.get("emissions", []),
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Failed to fetch daily snapshot: {e}")
            
            return IngestionResult(
                success=False,
                records_count=0,
                source="enrichment_daily_snapshot",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                error_message=str(e),
            )
    
    def fetch_data(self, dataset: str = "daily_snapshot", **kwargs) -> IngestionResult:
        """
        Generic data fetch method.
        
        Args:
            dataset: Dataset to fetch (wells, production, equipment, emissions, daily_snapshot)
            **kwargs: Additional arguments passed to specific fetch methods
        
        Returns:
            IngestionResult
        """
        fetch_methods = {
            "wells": self.fetch_wells,
            "production": self.fetch_production,
            "equipment": self.fetch_equipment,
            "emissions": self.fetch_emissions,
            "daily_snapshot": self.fetch_daily_snapshot,
        }
        
        if dataset not in fetch_methods:
            return IngestionResult(
                success=False,
                records_count=0,
                source=f"enrichment_{dataset}",
                ingested_at=datetime.now(),
                duration_seconds=0,
                error_message=f"Unknown dataset: {dataset}. Valid options: {list(fetch_methods.keys())}",
            )
        
        return fetch_methods[dataset](**kwargs)


if __name__ == "__main__":
    # Example usage
    with EnrichmentClient() as client:
        if client.health_check():
            print("Enrichment API is healthy")
            
            # Fetch daily snapshot
            result = client.fetch_daily_snapshot(seed=12345)
            
            if result.success:
                print(f"Fetched {result.records_count} records in {result.duration_seconds:.2f}s")
                print(f"Summary: {result.metadata.get('summary', {})}")
            else:
                print(f"Error: {result.error_message}")
        else:
            print("Enrichment API is not available")
