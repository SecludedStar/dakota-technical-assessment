"""
Dagster resources for the energy analytics pipeline.

Resources provide connections to external systems and shared utilities.
"""

import os
from typing import Any

from dagster import ConfigurableResource, InitResourceContext
import httpx
import psycopg2


class DatabaseResource(ConfigurableResource):
    """PostgreSQL database resource."""
    
    host: str = "localhost"
    port: int = 5432
    database: str = "energy_analytics"
    user: str = "postgres"
    password: str = ""
    
    def get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )
    
    def execute_query(self, query: str, params: tuple = None) -> list[dict]:
        """Execute a query and return results as list of dicts."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                return []


class EIAApiResource(ConfigurableResource):
    """EIA API resource for fetching energy data."""
    
    api_key: str = ""
    base_url: str = "https://api.eia.gov/v2"
    timeout: float = 60.0
    
    def _get_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
        )
    
    def fetch_data(self, endpoint: str, params: dict = None) -> dict:
        """Fetch data from EIA API."""
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        
        with self._get_client() as client:
            response = client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
    
    def health_check(self) -> bool:
        """Check if API is accessible."""
        try:
            with self._get_client() as client:
                response = client.get("/", params={"api_key": self.api_key})
                return response.status_code == 200
        except Exception:
            return False


class EnrichmentApiResource(ConfigurableResource):
    """FastAPI enrichment service resource."""
    
    base_url: str = "http://localhost:8000"
    timeout: float = 30.0
    
    def _get_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
        )
    
    def fetch_data(self, endpoint: str, params: dict = None) -> dict:
        """Fetch data from enrichment API."""
        with self._get_client() as client:
            response = client.get(endpoint, params=params or {})
            response.raise_for_status()
            return response.json()
    
    def health_check(self) -> bool:
        """Check if API is healthy."""
        try:
            with self._get_client() as client:
                response = client.get("/health")
                data = response.json()
                return data.get("status") == "healthy"
        except Exception:
            return False
    
    def fetch_daily_snapshot(self, seed: int = None) -> dict:
        """Fetch complete daily operational snapshot."""
        params = {}
        if seed is not None:
            params["seed"] = seed
        return self.fetch_data("/bulk/daily-snapshot", params)


# Resource definitions for Dagster
def get_resources():
    """Get resource definitions from environment variables."""
    return {
        "database": DatabaseResource(
            host=os.environ.get("POSTGRES_HOST", "postgres"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            database=os.environ.get("POSTGRES_DB", "energy_analytics"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
        ),
        "eia_api": EIAApiResource(
            api_key=os.environ.get("EIA_API_KEY", ""),
        ),
        "enrichment_api": EnrichmentApiResource(
            base_url=os.environ.get("ENRICHMENT_API_URL", "http://api:8000"),
        ),
    }
