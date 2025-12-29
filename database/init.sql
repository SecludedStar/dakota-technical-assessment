-- ============================================================================
-- Energy Analytics Database Schema
-- ============================================================================
-- 
-- This schema implements a medallion architecture with three layers:
--   - raw: Raw data as ingested from sources
--   - staging: Cleaned and validated data (managed by dbt)
--   - analytics: Business-ready aggregations and metrics (managed by dbt)
--
-- ============================================================================

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ============================================================================
-- RAW LAYER - Source data as-is
-- ============================================================================

-- EIA Natural Gas Prices
CREATE TABLE IF NOT EXISTS raw.eia_natural_gas_prices (
    id SERIAL PRIMARY KEY,
    period VARCHAR(20),
    duoarea VARCHAR(10),
    area_name VARCHAR(100),
    product VARCHAR(20),
    product_name VARCHAR(100),
    process VARCHAR(10),
    process_name VARCHAR(100),
    series VARCHAR(50),
    series_description VARCHAR(255),
    value DECIMAL(18, 4),
    units VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_ng_prices_period_series UNIQUE (period, series)
);

CREATE INDEX IF NOT EXISTS idx_ng_prices_period ON raw.eia_natural_gas_prices(period);
CREATE INDEX IF NOT EXISTS idx_ng_prices_ingested ON raw.eia_natural_gas_prices(ingested_at);

-- EIA Petroleum Prices
CREATE TABLE IF NOT EXISTS raw.eia_petroleum_prices (
    id SERIAL PRIMARY KEY,
    period VARCHAR(20),
    duoarea VARCHAR(10),
    area_name VARCHAR(100),
    product VARCHAR(20),
    product_name VARCHAR(100),
    series VARCHAR(50),
    series_description VARCHAR(255),
    value DECIMAL(18, 4),
    units VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_pet_prices_period_series UNIQUE (period, series)
);

CREATE INDEX IF NOT EXISTS idx_pet_prices_period ON raw.eia_petroleum_prices(period);
CREATE INDEX IF NOT EXISTS idx_pet_prices_product ON raw.eia_petroleum_prices(product);

-- Wells (from enrichment API)
CREATE TABLE IF NOT EXISTS raw.wells (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(20) UNIQUE NOT NULL,
    well_name VARCHAR(100),
    operator VARCHAR(100),
    basin VARCHAR(50),
    state VARCHAR(10),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    well_type VARCHAR(20),
    spud_date DATE,
    status VARCHAR(20),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wells_basin ON raw.wells(basin);
CREATE INDEX IF NOT EXISTS idx_wells_operator ON raw.wells(operator);
CREATE INDEX IF NOT EXISTS idx_wells_status ON raw.wells(status);
CREATE INDEX IF NOT EXISTS idx_wells_state ON raw.wells(state);

-- Production Records
CREATE TABLE IF NOT EXISTS raw.production (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(20) NOT NULL,
    production_date DATE NOT NULL,
    oil_bbl DECIMAL(12, 2),
    gas_mcf DECIMAL(12, 2),
    water_bbl DECIMAL(12, 2),
    uptime_hours DECIMAL(4, 1),
    choke_size DECIMAL(6, 2),
    tubing_pressure_psi DECIMAL(10, 2),
    casing_pressure_psi DECIMAL(10, 2),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_production_well_date UNIQUE (well_id, production_date)
);

CREATE INDEX IF NOT EXISTS idx_production_well ON raw.production(well_id);
CREATE INDEX IF NOT EXISTS idx_production_date ON raw.production(production_date);

-- Equipment Status
CREATE TABLE IF NOT EXISTS raw.equipment (
    id SERIAL PRIMARY KEY,
    equipment_id VARCHAR(20) UNIQUE NOT NULL,
    well_id VARCHAR(20) NOT NULL,
    equipment_type VARCHAR(50),
    manufacturer VARCHAR(100),
    install_date DATE,
    last_maintenance DATE,
    next_maintenance DATE,
    health_score DECIMAL(5, 2),
    status VARCHAR(20),
    runtime_hours INTEGER,
    alerts JSONB DEFAULT '[]'::jsonb,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_equipment_well ON raw.equipment(well_id);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON raw.equipment(status);
CREATE INDEX IF NOT EXISTS idx_equipment_type ON raw.equipment(equipment_type);
CREATE INDEX IF NOT EXISTS idx_equipment_health ON raw.equipment(health_score);

-- Emissions Records
CREATE TABLE IF NOT EXISTS raw.emissions (
    id SERIAL PRIMARY KEY,
    well_id VARCHAR(20) NOT NULL,
    measurement_date DATE NOT NULL,
    methane_kg DECIMAL(12, 4),
    co2_kg DECIMAL(12, 4),
    voc_kg DECIMAL(12, 4),
    flare_volume_mcf DECIMAL(12, 4),
    leak_detected BOOLEAN DEFAULT FALSE,
    measurement_method VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_emissions_well_date UNIQUE (well_id, measurement_date)
);

CREATE INDEX IF NOT EXISTS idx_emissions_well ON raw.emissions(well_id);
CREATE INDEX IF NOT EXISTS idx_emissions_date ON raw.emissions(measurement_date);
CREATE INDEX IF NOT EXISTS idx_emissions_leak ON raw.emissions(leak_detected);

-- Ingestion Log (metadata tracking)
CREATE TABLE IF NOT EXISTS raw.ingestion_log (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    records_count INTEGER,
    duration_seconds DECIMAL(10, 3),
    error_message TEXT,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ingestion_log_source ON raw.ingestion_log(source);
CREATE INDEX IF NOT EXISTS idx_ingestion_log_run_at ON raw.ingestion_log(run_at);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON SCHEMA raw IS 'Raw data layer - source data as ingested';
COMMENT ON SCHEMA staging IS 'Staging layer - cleaned and validated data (managed by dbt)';
COMMENT ON SCHEMA analytics IS 'Analytics layer - business-ready metrics (managed by dbt)';

COMMENT ON TABLE raw.eia_natural_gas_prices IS 'EIA natural gas price data from API v2';
COMMENT ON TABLE raw.eia_petroleum_prices IS 'EIA petroleum spot price data from API v2';
COMMENT ON TABLE raw.wells IS 'Well master data from enrichment API';
COMMENT ON TABLE raw.production IS 'Daily well production records from enrichment API';
COMMENT ON TABLE raw.equipment IS 'Equipment status and health from enrichment API';
COMMENT ON TABLE raw.emissions IS 'Emissions monitoring data from enrichment API';
COMMENT ON TABLE raw.ingestion_log IS 'Metadata tracking for ingestion runs';

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant usage on schemas
GRANT USAGE ON SCHEMA raw TO PUBLIC;
GRANT USAGE ON SCHEMA staging TO PUBLIC;
GRANT USAGE ON SCHEMA analytics TO PUBLIC;

-- Grant permissions on tables
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA raw TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA staging TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO PUBLIC;

-- Grant permissions on sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO PUBLIC;
