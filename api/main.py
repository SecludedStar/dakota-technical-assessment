"""
FastAPI service for synthetic energy facility enrichment data.

Generates realistic operational data for oil & gas wells, including:
- Well production metrics
- Equipment status and maintenance
- Emissions monitoring
- Weather conditions affecting operations
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI(
    title="Energy Facility Enrichment API",
    description="Generates synthetic operational data for energy analytics pipelines",
    version="1.0.0",
)

# Seed for reproducibility in demos
random.seed(122725)


# =============================================================================
# Pydantic Models
# =============================================================================

class WellInfo(BaseModel):
    """Basic well information."""
    well_id: str = Field(..., description="Unique well identifier")
    well_name: str = Field(..., description="Human-readable well name")
    operator: str = Field(..., description="Operating company")
    basin: str = Field(..., description="Geological basin")
    state: str = Field(..., description="US state location")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    well_type: str = Field(..., description="Oil, Gas, or Dual")
    spud_date: str = Field(..., description="Date drilling began")
    status: str = Field(..., description="Active, Inactive, Plugged")


class ProductionRecord(BaseModel):
    """Daily production metrics for a well."""
    well_id: str
    production_date: str
    oil_bbl: float = Field(..., ge=0, description="Oil production in barrels")
    gas_mcf: float = Field(..., ge=0, description="Gas production in MCF")
    water_bbl: float = Field(..., ge=0, description="Water production in barrels")
    uptime_hours: float = Field(..., ge=0, le=24)
    choke_size: float = Field(..., description="Choke size in 64ths inch")
    tubing_pressure_psi: float = Field(..., ge=0)
    casing_pressure_psi: float = Field(..., ge=0)


class EquipmentStatus(BaseModel):
    """Equipment health and maintenance status."""
    equipment_id: str
    well_id: str
    equipment_type: str
    manufacturer: str
    install_date: str
    last_maintenance: str
    next_maintenance: str
    health_score: float = Field(..., ge=0, le=100)
    status: str = Field(..., description="Operational, Degraded, Failed, Maintenance")
    runtime_hours: int
    alerts: list[str]


class EmissionsRecord(BaseModel):
    """Emissions monitoring data."""
    well_id: str
    measurement_date: str
    methane_kg: float = Field(..., ge=0)
    co2_kg: float = Field(..., ge=0)
    voc_kg: float = Field(..., ge=0)
    flare_volume_mcf: float = Field(..., ge=0)
    leak_detected: bool
    measurement_method: str


class WeatherCondition(BaseModel):
    """Weather conditions at facility location."""
    location_id: str
    observation_time: str
    temperature_f: float
    wind_speed_mph: float
    wind_direction: str
    humidity_pct: float
    precipitation_in: float
    visibility_miles: float
    conditions: str


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    data: list
    total_count: int
    page: int
    page_size: int
    has_more: bool


# =============================================================================
# Data Generators
# =============================================================================

OPERATORS = [
    "Devon Energy", "Pioneer Natural", "EOG Resources", "Diamondback Energy",
    "ConocoPhillips", "Occidental", "Apache Corp", "Marathon Oil"
]

BASINS = [
    ("Permian", "TX", -102.0, 31.5),
    ("Permian", "NM", -103.5, 32.0),
    ("Bakken", "ND", -103.0, 48.0),
    ("Eagle Ford", "TX", -98.5, 28.5),
    ("DJ Basin", "CO", -104.5, 40.0),
    ("Marcellus", "PA", -77.0, 41.0),
    ("Haynesville", "LA", -93.5, 32.5),
    ("Anadarko", "OK", -98.0, 35.5),
]

EQUIPMENT_TYPES = [
    ("Pump Jack", ["Lufkin", "Dover", "Weatherford"]),
    ("Separator", ["NATCO", "Exterran", "Schlumberger"]),
    ("Compressor", ["Ariel", "Caterpillar", "Waukesha"]),
    ("Tank Battery", ["Matrix", "Enerflex", "CECO"]),
    ("SCADA System", ["Emerson", "ABB", "Honeywell"]),
    ("Gas Lift Valve", ["Weatherford", "Schlumberger", "Baker Hughes"]),
]

ALERTS = [
    "High vibration detected",
    "Temperature above threshold",
    "Pressure fluctuation",
    "Scheduled maintenance due",
    "Sensor calibration needed",
    "Low efficiency warning",
    "Abnormal noise pattern",
]


def generate_well_id() -> str:
    """Generate a realistic well API number format."""
    state_code = random.randint(1, 56)
    county_code = random.randint(1, 999)
    well_num = random.randint(10000, 99999)
    return f"{state_code:02d}-{county_code:03d}-{well_num:05d}"


def generate_wells(count: int, seed: Optional[int] = None) -> list[WellInfo]:
    """Generate synthetic well records."""
    if seed:
        random.seed(seed)
    
    wells = []
    for i in range(count):
        basin, state, base_lon, base_lat = random.choice(BASINS)
        spud_date = datetime.now() - timedelta(days=random.randint(365, 3650))
        
        wells.append(WellInfo(
            well_id=generate_well_id(),
            well_name=f"{basin}-{random.choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Echo'])}-{i+1:04d}",
            operator=random.choice(OPERATORS),
            basin=basin,
            state=state,
            latitude=base_lat + random.uniform(-1.5, 1.5),
            longitude=base_lon + random.uniform(-1.5, 1.5),
            well_type=random.choice(["Oil", "Gas", "Dual"]),
            spud_date=spud_date.strftime("%Y-%m-%d"),
            status=random.choices(["Active", "Inactive", "Plugged"], weights=[0.7, 0.2, 0.1])[0],
        ))
    
    return wells


def generate_production(well_id: str, days: int = 30) -> list[ProductionRecord]:
    """Generate daily production records for a well."""
    records = []
    base_oil = random.uniform(50, 500)
    base_gas = random.uniform(100, 2000)
    
    for day_offset in range(days):
        prod_date = datetime.now() - timedelta(days=day_offset)
        # Add some realistic variation and decline
        decline_factor = 1 - (day_offset * 0.001)
        daily_variation = random.uniform(0.85, 1.15)
        
        records.append(ProductionRecord(
            well_id=well_id,
            production_date=prod_date.strftime("%Y-%m-%d"),
            oil_bbl=round(base_oil * decline_factor * daily_variation, 2),
            gas_mcf=round(base_gas * decline_factor * daily_variation, 2),
            water_bbl=round(random.uniform(10, 200), 2),
            uptime_hours=round(random.uniform(20, 24), 1),
            choke_size=random.choice([16, 20, 24, 28, 32, 36, 40]),
            tubing_pressure_psi=round(random.uniform(200, 1500), 1),
            casing_pressure_psi=round(random.uniform(50, 500), 1),
        ))
    
    return records


def generate_equipment(well_id: str) -> list[EquipmentStatus]:
    """Generate equipment status records for a well."""
    equipment = []
    num_equipment = random.randint(3, 6)
    
    for _ in range(num_equipment):
        eq_type, manufacturers = random.choice(EQUIPMENT_TYPES)
        install_date = datetime.now() - timedelta(days=random.randint(180, 1800))
        last_maint = datetime.now() - timedelta(days=random.randint(7, 180))
        next_maint = datetime.now() + timedelta(days=random.randint(7, 180))
        
        health = random.uniform(60, 100)
        status = "Operational"
        if health < 70:
            status = random.choice(["Degraded", "Maintenance"])
        elif health < 50:
            status = "Failed"
        
        alerts_list = []
        if health < 85:
            alerts_list = random.sample(ALERTS, k=random.randint(1, 3))
        
        equipment.append(EquipmentStatus(
            equipment_id=str(uuid.uuid4())[:8].upper(),
            well_id=well_id,
            equipment_type=eq_type,
            manufacturer=random.choice(manufacturers),
            install_date=install_date.strftime("%Y-%m-%d"),
            last_maintenance=last_maint.strftime("%Y-%m-%d"),
            next_maintenance=next_maint.strftime("%Y-%m-%d"),
            health_score=round(health, 1),
            status=status,
            runtime_hours=random.randint(1000, 50000),
            alerts=alerts_list,
        ))
    
    return equipment


def generate_emissions(well_id: str, days: int = 30) -> list[EmissionsRecord]:
    """Generate emissions monitoring records."""
    records = []
    base_methane = random.uniform(5, 50)
    
    for day_offset in range(days):
        meas_date = datetime.now() - timedelta(days=day_offset)
        leak = random.random() < 0.05  # Simulating 5% chance of leak detection
        
        records.append(EmissionsRecord(
            well_id=well_id,
            measurement_date=meas_date.strftime("%Y-%m-%d"),
            methane_kg=round(base_methane * random.uniform(0.8, 1.5) * (3 if leak else 1), 2),
            co2_kg=round(random.uniform(100, 500), 2),
            voc_kg=round(random.uniform(1, 20), 2),
            flare_volume_mcf=round(random.uniform(0, 50), 2),
            leak_detected=leak,
            measurement_method=random.choice(["LDAR", "OGI Camera", "Continuous Monitor", "Flyover"]),
        ))
    
    return records


def generate_weather(location_id: str, hours: int = 24) -> list[WeatherCondition]:
    """Generate weather condition records."""
    records = []
    base_temp = random.uniform(30, 90)
    
    for hour_offset in range(hours):
        obs_time = datetime.now() - timedelta(hours=hour_offset)
        # Temperature variation through the day
        temp_variation = 10 * (1 - abs(12 - (obs_time.hour % 24)) / 12)
        
        records.append(WeatherCondition(
            location_id=location_id,
            observation_time=obs_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            temperature_f=round(base_temp + temp_variation + random.uniform(-5, 5), 1),
            wind_speed_mph=round(random.uniform(0, 30), 1),
            wind_direction=random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            humidity_pct=round(random.uniform(20, 80), 1),
            precipitation_in=round(random.uniform(0, 0.5) if random.random() < 0.2 else 0, 2),
            visibility_miles=round(random.uniform(5, 10), 1),
            conditions=random.choice(["Clear", "Partly Cloudy", "Cloudy", "Light Rain", "Windy"]),
        ))
    
    return records


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Energy Facility Enrichment API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "checks": {
            "api": "ok",
            "data_generation": "ok",
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/wells", response_model=PaginatedResponse, tags=["Wells"])
async def get_wells(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    basin: Optional[str] = Query(None, description="Filter by basin name"),
    operator: Optional[str] = Query(None, description="Filter by operator"),
    status: Optional[str] = Query(None, description="Filter by well status"),
    seed: Optional[int] = Query(None, description="Random seed for reproducibility"),
):
    """
    Get paginated list of synthetic wells.
    
    Use seed parameter for reproducible results across pipeline runs.
    """
    all_wells = generate_wells(500, seed=seed)
    
    # Apply filters
    if basin:
        all_wells = [w for w in all_wells if basin.lower() in w.basin.lower()]
    if operator:
        all_wells = [w for w in all_wells if operator.lower() in w.operator.lower()]
    if status:
        all_wells = [w for w in all_wells if w.status.lower() == status.lower()]
    
    total = len(all_wells)
    start = (page - 1) * page_size
    end = start + page_size
    
    return PaginatedResponse(
        data=[w.model_dump() for w in all_wells[start:end]],
        total_count=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@app.get("/wells/{well_id}", response_model=WellInfo, tags=["Wells"])
async def get_well(well_id: str):
    """Get details for a specific well."""
    wells = generate_wells(100, seed=hash(well_id) % 10000)
    # For demo purposes, modify the first well to match requested ID
    well = wells[0]
    well.well_id = well_id
    return well


@app.get("/production", response_model=PaginatedResponse, tags=["Production"])
async def get_production(
    well_id: Optional[str] = Query(None, description="Filter by well ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
):
    """Get production records for wells."""
    if well_id:
        records = generate_production(well_id, days)
    else:
        # Generate for multiple wells
        wells = generate_wells(10, seed=42)
        records = []
        for w in wells:
            records.extend(generate_production(w.well_id, min(days, 7)))
    
    total = len(records)
    start = (page - 1) * page_size
    end = start + page_size
    
    return PaginatedResponse(
        data=[r.model_dump() for r in records[start:end]],
        total_count=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@app.get("/equipment", response_model=PaginatedResponse, tags=["Equipment"])
async def get_equipment(
    well_id: Optional[str] = Query(None, description="Filter by well ID"),
    status: Optional[str] = Query(None, description="Filter by equipment status"),
    equipment_type: Optional[str] = Query(None, description="Filter by equipment type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Get equipment status records."""
    if well_id:
        equipment = generate_equipment(well_id)
    else:
        wells = generate_wells(50, seed=42)
        equipment = []
        for w in wells:
            equipment.extend(generate_equipment(w.well_id))
    
    if status:
        equipment = [e for e in equipment if e.status.lower() == status.lower()]
    if equipment_type:
        equipment = [e for e in equipment if equipment_type.lower() in e.equipment_type.lower()]
    
    total = len(equipment)
    start = (page - 1) * page_size
    end = start + page_size
    
    return PaginatedResponse(
        data=[e.model_dump() for e in equipment[start:end]],
        total_count=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@app.get("/emissions", response_model=PaginatedResponse, tags=["Emissions"])
async def get_emissions(
    well_id: Optional[str] = Query(None, description="Filter by well ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    leak_detected: Optional[bool] = Query(None, description="Filter by leak detection"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
):
    """Get emissions monitoring records."""
    if well_id:
        records = generate_emissions(well_id, days)
    else:
        wells = generate_wells(20, seed=42)
        records = []
        for w in wells:
            records.extend(generate_emissions(w.well_id, min(days, 7)))
    
    if leak_detected is not None:
        records = [r for r in records if r.leak_detected == leak_detected]
    
    total = len(records)
    start = (page - 1) * page_size
    end = start + page_size
    
    return PaginatedResponse(
        data=[r.model_dump() for r in records[start:end]],
        total_count=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@app.get("/weather", response_model=PaginatedResponse, tags=["Weather"])
async def get_weather(
    location_id: str = Query(..., description="Location/facility ID"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Get weather conditions for a location."""
    records = generate_weather(location_id, hours)
    
    total = len(records)
    start = (page - 1) * page_size
    end = start + page_size
    
    return PaginatedResponse(
        data=[r.model_dump() for r in records[start:end]],
        total_count=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@app.get("/bulk/daily-snapshot", tags=["Bulk"])
async def get_daily_snapshot(
    snapshot_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    seed: Optional[int] = Query(None, description="Random seed for reproducibility"),
    days: int = Query(30, ge=1, le=90, description="Days of historical data to generate"),
):
    """
    Get a complete daily snapshot of all operational data.

    Useful for daily batch ingestion pipelines. Generates historical
    production and emissions data for trend analysis.
    """
    if seed:
        random.seed(seed)

    wells = generate_wells(100, seed=seed)
    snapshot_dt = datetime.fromisoformat(snapshot_date) if snapshot_date else datetime.now()

    production_data = []
    equipment_data = []
    emissions_data = []

    for well in wells[:50]:  # Limit for performance
        prod = generate_production(well.well_id, days=days)
        if prod:
            production_data.extend([p.model_dump() for p in prod])

        equip = generate_equipment(well.well_id)
        equipment_data.extend([e.model_dump() for e in equip])

        emis = generate_emissions(well.well_id, days=days)
        if emis:
            emissions_data.extend([e.model_dump() for e in emis])
    
    return {
        "snapshot_date": snapshot_dt.strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(),
        "wells": [w.model_dump() for w in wells[:50]],
        "production": production_data,
        "equipment": equipment_data,
        "emissions": emissions_data,
        "summary": {
            "total_wells": len(wells[:50]),
            "active_wells": len([w for w in wells[:50] if w.status == "Active"]),
            "total_production_records": len(production_data),
            "equipment_alerts": sum(len(e.get("alerts", [])) for e in equipment_data),
            "leaks_detected": len([e for e in emissions_data if e.get("leak_detected")]),
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
