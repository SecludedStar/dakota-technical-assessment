"""
EIA (U.S. Energy Information Administration) API client.

Fetches natural gas and petroleum data from the EIA API v2.
API Documentation: https://www.eia.gov/opendata/documentation.php
"""

import os
from datetime import datetime
from typing import Optional

from base_client import BaseClient, IngestionResult


class EIAClient(BaseClient):
    """Client for fetching data from EIA API v2."""
    
    # API endpoints for different data categories
    ENDPOINTS = {
        "natural_gas_prices": "/natural-gas/pri/sum/data/",
        "natural_gas_storage": "/natural-gas/stor/wkly/data/",
        "petroleum_prices": "/petroleum/pri/spt/data/",
        "petroleum_production": "/petroleum/crd/crpdn/data/",
        "electricity_generation": "/electricity/rto/fuel-type-data/data/",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        """
        Initialize EIA client.
        
        Args:
            api_key: EIA API key. If not provided, reads from EIA_API_KEY env var.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
        """
        super().__init__(
            base_url="https://api.eia.gov/v2",
            timeout=timeout,
            max_retries=max_retries,
        )
        
        self.api_key = api_key or os.environ.get("EIA_API_KEY")
        if not self.api_key:
            self.logger.warning(
                "No EIA API key provided. Set EIA_API_KEY environment variable "
                "or pass api_key parameter. Register at https://www.eia.gov/opendata/"
            )
    
    def _build_params(
        self,
        data_columns: list[str],
        frequency: str = "monthly",
        start: Optional[str] = None,
        end: Optional[str] = None,
        facets: Optional[dict] = None,
        sort_column: str = "period",
        sort_direction: str = "desc",
        length: int = 5000,
        offset: int = 0,
    ) -> dict:
        """Build query parameters for EIA API request."""
        params = {
            "api_key": self.api_key,
            "frequency": frequency,
            "sort[0][column]": sort_column,
            "sort[0][direction]": sort_direction,
            "length": length,
            "offset": offset,
        }
        
        # Add data columns
        for i, col in enumerate(data_columns):
            params[f"data[{i}]"] = col
        
        # Add date filters
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        
        # Add facet filters
        if facets:
            for key, values in facets.items():
                if isinstance(values, list):
                    for i, v in enumerate(values):
                        params[f"facets[{key}][{i}]"] = v
                else:
                    params[f"facets[{key}][0]"] = values
        
        return params
    
    def health_check(self) -> bool:
        """Check if EIA API is accessible."""
        try:
            # Query API metadata
            response = self.get("/", params={"api_key": self.api_key})
            return response.get("response", {}).get("routes") is not None
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def fetch_natural_gas_prices(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        process: Optional[str] = None,
        length: int = 5000,
    ) -> IngestionResult:
        """
        Fetch natural gas price summary data.
        
        Args:
            start: Start date (YYYY-MM format)
            end: End date (YYYY-MM format)
            process: Filter by process type (e.g., "PRS" for residential)
            length: Maximum records to fetch
        
        Returns:
            IngestionResult with fetched data
        """
        start_time = datetime.now()
        
        try:
            facets = {}
            if process:
                facets["process"] = process
            
            params = self._build_params(
                data_columns=["value"],
                frequency="monthly",
                start=start,
                end=end,
                facets=facets if facets else None,
                length=length,
            )
            
            response = self.get(self.ENDPOINTS["natural_gas_prices"], params=params)
            
            data = response.get("response", {}).get("data", [])
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Fetched {len(data)} natural gas price records")
            
            return IngestionResult(
                success=True,
                records_count=len(data),
                source="eia_natural_gas_prices",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                metadata={
                    "endpoint": self.ENDPOINTS["natural_gas_prices"],
                    "start": start,
                    "end": end,
                    "data": data,
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Failed to fetch natural gas prices: {e}")
            
            return IngestionResult(
                success=False,
                records_count=0,
                source="eia_natural_gas_prices",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                error_message=str(e),
            )
    
    def fetch_petroleum_prices(
        self,
        product: str = "EPCBRENT",  # Brent crude spot price
        start: Optional[str] = None,
        end: Optional[str] = None,
        length: int = 5000,
    ) -> IngestionResult:
        """
        Fetch petroleum spot prices.
        
        Args:
            product: Product code (EPCBRENT, EPCWTI, etc.)
            start: Start date
            end: End date
            length: Maximum records
        
        Returns:
            IngestionResult with fetched data
        """
        start_time = datetime.now()
        
        try:
            params = self._build_params(
                data_columns=["value"],
                frequency="daily",
                start=start,
                end=end,
                facets={"product": product} if product else None,
                length=length,
            )
            
            response = self.get(self.ENDPOINTS["petroleum_prices"], params=params)
            
            data = response.get("response", {}).get("data", [])
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Fetched {len(data)} petroleum price records")
            
            return IngestionResult(
                success=True,
                records_count=len(data),
                source="eia_petroleum_prices",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                metadata={
                    "endpoint": self.ENDPOINTS["petroleum_prices"],
                    "product": product,
                    "data": data,
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Failed to fetch petroleum prices: {e}")
            
            return IngestionResult(
                success=False,
                records_count=0,
                source="eia_petroleum_prices",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                error_message=str(e),
            )
    
    def fetch_petroleum_production(
        self,
        area: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        length: int = 5000,
    ) -> IngestionResult:
        """
        Fetch crude oil production data.
        
        Args:
            area: Area code (e.g., state codes)
            start: Start date
            end: End date
            length: Maximum records
        
        Returns:
            IngestionResult with fetched data
        """
        start_time = datetime.now()
        
        try:
            facets = {}
            if area:
                facets["area"] = area
            
            params = self._build_params(
                data_columns=["value"],
                frequency="monthly",
                start=start,
                end=end,
                facets=facets if facets else None,
                length=length,
            )
            
            response = self.get(self.ENDPOINTS["petroleum_production"], params=params)
            
            data = response.get("response", {}).get("data", [])
            duration = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"Fetched {len(data)} petroleum production records")
            
            return IngestionResult(
                success=True,
                records_count=len(data),
                source="eia_petroleum_production",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                metadata={
                    "endpoint": self.ENDPOINTS["petroleum_production"],
                    "area": area,
                    "data": data,
                }
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Failed to fetch petroleum production: {e}")
            
            return IngestionResult(
                success=False,
                records_count=0,
                source="eia_petroleum_production",
                ingested_at=datetime.now(),
                duration_seconds=duration,
                error_message=str(e),
            )
    
    def fetch_data(self, dataset: str = "natural_gas_prices", **kwargs) -> IngestionResult:
        """
        Generic data fetch method.
        
        Args:
            dataset: Dataset to fetch (natural_gas_prices, petroleum_prices, petroleum_production)
            **kwargs: Additional arguments passed to specific fetch methods
        
        Returns:
            IngestionResult
        """
        fetch_methods = {
            "natural_gas_prices": self.fetch_natural_gas_prices,
            "petroleum_prices": self.fetch_petroleum_prices,
            "petroleum_production": self.fetch_petroleum_production,
        }
        
        if dataset not in fetch_methods:
            return IngestionResult(
                success=False,
                records_count=0,
                source=f"eia_{dataset}",
                ingested_at=datetime.now(),
                duration_seconds=0,
                error_message=f"Unknown dataset: {dataset}. Valid options: {list(fetch_methods.keys())}",
            )
        
        return fetch_methods[dataset](**kwargs)


if __name__ == "__main__":
    # Example usage
    with EIAClient() as client:
        if client.health_check():
            print("EIA API is accessible")
            
            # Fetch natural gas prices
            result = client.fetch_natural_gas_prices(
                start="2024-01",
                end="2024-12",
                length=100
            )
            
            if result.success:
                print(f"Fetched {result.records_count} records in {result.duration_seconds:.2f}s")
            else:
                print(f"Error: {result.error_message}")
        else:
            print("EIA API is not accessible")
