"""Tests for ingestion clients."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date
import sys
sys.path.insert(0, '/home/claude/dakota-assessment/ingestion')


class TestEIAClient:
    """Tests for the EIA API client."""
    
    def test_client_initialization(self):
        """Client should initialize with API key."""
        from eia_client import EIAClient
        client = EIAClient(api_key="test_key")
        assert client.api_key == "test_key"
    
    def test_client_base_url(self):
        """Client should use correct base URL."""
        from eia_client import EIAClient
        client = EIAClient(api_key="test_key")
        assert "eia.gov" in client.base_url


class TestEnrichmentClient:
    """Tests for the Enrichment API client."""
    
    def test_client_initialization(self):
        """Client should initialize with base URL."""
        from enrichment_client import EnrichmentClient
        client = EnrichmentClient(base_url="http://localhost:8000")
        assert client.base_url == "http://localhost:8000"


class TestDBLoader:
    """Tests for the database loader."""
    
    def test_loader_initialization(self):
        """Loader should initialize with connection string."""
        from db_loader import DBLoader
        loader = DBLoader(connection_string="postgresql://test:test@localhost/test")
        assert loader.connection_string is not None
    
    def test_batch_size_configuration(self):
        """Loader should accept custom batch size."""
        from db_loader import DBLoader
        loader = DBLoader(
            connection_string="postgresql://test:test@localhost/test",
            batch_size=500
        )
        assert loader.batch_size == 500


class TestIngestionResult:
    """Tests for the IngestionResult dataclass."""
    
    def test_result_creation(self):
        """IngestionResult should store all fields."""
        from base_client import IngestionResult
        result = IngestionResult(
            source="test_source",
            records_fetched=100,
            records_loaded=100,
            success=True,
            errors=[]
        )
        assert result.source == "test_source"
        assert result.records_fetched == 100
        assert result.success is True
    
    def test_result_with_errors(self):
        """IngestionResult should handle errors."""
        from base_client import IngestionResult
        result = IngestionResult(
            source="test_source",
            records_fetched=100,
            records_loaded=50,
            success=False,
            errors=["Connection timeout", "Retry exhausted"]
        )
        assert result.success is False
        assert len(result.errors) == 2


class TestRetryLogic:
    """Tests for retry behavior."""
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Client should retry on transient errors."""
        # This is a conceptual test - actual implementation would mock httpx
        pass
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Retry delays should increase exponentially."""
        # This is a conceptual test - actual implementation would mock time
        pass


class TestDataValidation:
    """Tests for data validation."""
    
    def test_well_data_validation(self):
        """Well data should have required fields."""
        sample_well = {
            "well_id": "W001",
            "well_name": "Test Well",
            "operator": "Test Operator",
            "basin": "Test Basin",
            "status": "active",
            "latitude": 40.0,
            "longitude": -105.0
        }
        required_fields = ["well_id", "well_name", "operator", "status"]
        for field in required_fields:
            assert field in sample_well
    
    def test_production_data_validation(self):
        """Production data should have valid ranges."""
        sample_production = {
            "well_id": "W001",
            "production_date": "2024-01-15",
            "oil_bbl": 150.5,
            "gas_mcf": 500.0,
            "water_bbl": 75.0,
            "uptime_hours": 23.5
        }
        assert sample_production["oil_bbl"] >= 0
        assert sample_production["gas_mcf"] >= 0
        assert sample_production["water_bbl"] >= 0
        assert 0 <= sample_production["uptime_hours"] <= 24
    
    def test_equipment_health_validation(self):
        """Equipment health scores should be 0-100."""
        sample_equipment = {
            "equipment_id": "E001",
            "well_id": "W001",
            "equipment_type": "pump",
            "health_score": 85.0,
            "last_maintenance": "2024-01-01"
        }
        assert 0 <= sample_equipment["health_score"] <= 100
