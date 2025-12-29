"""Tests for the FastAPI enrichment service."""
import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '/home/claude/dakota-assessment/api')
from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_returns_200(self, client):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_status(self, client):
        """Health endpoint should return status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestWellsEndpoint:
    """Tests for the wells endpoint."""
    
    def test_wells_returns_200(self, client):
        """Wells endpoint should return 200."""
        response = client.get("/wells")
        assert response.status_code == 200
    
    def test_wells_returns_list(self, client):
        """Wells endpoint should return a list."""
        response = client.get("/wells")
        data = response.json()
        assert isinstance(data, list)
    
    def test_wells_pagination(self, client):
        """Wells endpoint should respect limit parameter."""
        response = client.get("/wells?limit=5")
        data = response.json()
        assert len(data) <= 5
    
    def test_wells_filter_by_status(self, client):
        """Wells endpoint should filter by status."""
        response = client.get("/wells?status=active")
        data = response.json()
        for well in data:
            assert well["status"] == "active"
    
    def test_wells_seed_reproducibility(self, client):
        """Same seed should produce same results."""
        response1 = client.get("/wells?seed=42&limit=10")
        response2 = client.get("/wells?seed=42&limit=10")
        assert response1.json() == response2.json()


class TestProductionEndpoint:
    """Tests for the production endpoint."""
    
    def test_production_returns_200(self, client):
        """Production endpoint should return 200."""
        response = client.get("/production")
        assert response.status_code == 200
    
    def test_production_has_required_fields(self, client):
        """Production records should have required fields."""
        response = client.get("/production?limit=1")
        data = response.json()
        if data:
            record = data[0]
            required_fields = ["well_id", "production_date", "oil_bbl", "gas_mcf", "water_bbl"]
            for field in required_fields:
                assert field in record


class TestEquipmentEndpoint:
    """Tests for the equipment endpoint."""
    
    def test_equipment_returns_200(self, client):
        """Equipment endpoint should return 200."""
        response = client.get("/equipment")
        assert response.status_code == 200
    
    def test_equipment_health_score_range(self, client):
        """Health scores should be between 0 and 100."""
        response = client.get("/equipment?limit=20")
        data = response.json()
        for equipment in data:
            assert 0 <= equipment["health_score"] <= 100


class TestEmissionsEndpoint:
    """Tests for the emissions endpoint."""
    
    def test_emissions_returns_200(self, client):
        """Emissions endpoint should return 200."""
        response = client.get("/emissions")
        assert response.status_code == 200
    
    def test_emissions_has_measurements(self, client):
        """Emissions records should have measurement fields."""
        response = client.get("/emissions?limit=1")
        data = response.json()
        if data:
            record = data[0]
            assert "methane_kg" in record
            assert "co2_kg" in record


class TestBulkSnapshotEndpoint:
    """Tests for the bulk daily snapshot endpoint."""
    
    def test_bulk_snapshot_returns_200(self, client):
        """Bulk snapshot endpoint should return 200."""
        response = client.get("/bulk/daily-snapshot")
        assert response.status_code == 200
    
    def test_bulk_snapshot_has_all_sections(self, client):
        """Bulk snapshot should have all data sections."""
        response = client.get("/bulk/daily-snapshot")
        data = response.json()
        assert "snapshot_date" in data
        assert "wells" in data
        assert "production" in data
        assert "equipment" in data
        assert "emissions" in data
    
    def test_bulk_snapshot_date_parameter(self, client):
        """Bulk snapshot should accept date parameter."""
        response = client.get("/bulk/daily-snapshot?date=2024-01-15")
        data = response.json()
        assert data["snapshot_date"] == "2024-01-15"
