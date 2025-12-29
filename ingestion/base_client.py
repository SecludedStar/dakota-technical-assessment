"""
Base client for data ingestion with retry logic and error handling.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@dataclass
class IngestionResult:
    """Result of an ingestion operation."""
    success: bool
    records_count: int
    source: str
    ingested_at: datetime
    duration_seconds: float
    error_message: Optional[str] = None
    metadata: Optional[dict] = None


class BaseClient(ABC):
    """Abstract base client with retry logic and error handling."""
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": "Dakota-Energy-Ingestion/1.0"},
        )
    
    def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Request attempt {attempt + 1}: {method} {endpoint}")
                
                response = self._client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    **kwargs
                )
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code in (429, 500, 502, 503, 504):
                    # Retryable errors
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"HTTP {e.response.status_code} error, retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    # Non-retryable HTTP error
                    self.logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                    raise
                    
            except httpx.RequestError as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)
                self.logger.warning(
                    f"Request error: {e}, retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
        
        # All retries exhausted
        self.logger.error(f"All {self.max_retries} retry attempts failed")
        raise last_exception
    
    def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GET request and return JSON response."""
        response = self._request_with_retry("GET", endpoint, params=params)
        return response.json()
    
    @abstractmethod
    def fetch_data(self, **kwargs) -> IngestionResult:
        """Fetch data from the source. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the data source is available."""
        pass
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
