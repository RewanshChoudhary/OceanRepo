-- Marine Data Integration Platform - PostgreSQL Schema
-- Comprehensive database schema for marine research data storage

-- Enable PostGIS extension for spatial data
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create custom types
CREATE TYPE confidence_level AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH');
CREATE TYPE data_quality AS ENUM ('RAW', 'PROCESSED', 'VALIDATED', 'PUBLISHED');
CREATE TYPE sampling_method AS ENUM ('CTD', 'BOTTLE', 'TRAWL', 'SEDIMENT', 'PLANKTON_NET', 'AUTONOMOUS_SENSOR');

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Research Projects Table
CREATE TABLE IF NOT EXISTS research_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_name VARCHAR(255) NOT NULL,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    principal_investigator VARCHAR(255) NOT NULL,
    institution VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    budget DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'COMPLETED', 'SUSPENDED', 'CANCELLED')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Research Vessels Table
CREATE TABLE IF NOT EXISTS research_vessels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vessel_name VARCHAR(255) NOT NULL,
    vessel_code VARCHAR(20) UNIQUE NOT NULL,
    country_flag VARCHAR(5) NOT NULL,
    length_meters DECIMAL(8,2),
    beam_meters DECIMAL(8,2),
    draft_meters DECIMAL(8,2),
    gross_tonnage INTEGER,
    max_speed_knots DECIMAL(5,2),
    crew_capacity INTEGER,
    scientific_capacity INTEGER,
    equipment_capabilities TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sampling Events Table (Enhanced)
CREATE TABLE IF NOT EXISTS sampling_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(100) UNIQUE NOT NULL,
    project_id UUID REFERENCES research_projects(id) ON DELETE SET NULL,
    vessel_id UUID REFERENCES research_vessels(id) ON DELETE SET NULL,
    event_name VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('STATION', 'TRANSECT', 'CONTINUOUS', 'DEPLOYMENT', 'RECOVERY')),
    start_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    end_datetime TIMESTAMP WITH TIME ZONE,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    start_location GEOGRAPHY(POINT, 4326),
    end_location GEOGRAPHY(POINT, 4326),
    water_depth_meters DECIMAL(10,3),
    weather_conditions TEXT,
    sea_state_beaufort INTEGER CHECK (sea_state_beaufort BETWEEN 0 AND 12),
    wind_speed_knots DECIMAL(5,2),
    wind_direction_degrees INTEGER CHECK (wind_direction_degrees BETWEEN 0 AND 360),
    sampling_method sampling_method NOT NULL,
    equipment_used TEXT[],
    chief_scientist VARCHAR(255),
    data_quality data_quality DEFAULT 'RAW',
    comments TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sampling Points Table (Enhanced)
CREATE TABLE IF NOT EXISTS sampling_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    point_id VARCHAR(100) UNIQUE NOT NULL,
    sampling_event_id UUID REFERENCES sampling_events(id) ON DELETE CASCADE,
    station_name VARCHAR(255),
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    depth_meters DECIMAL(10,3) NOT NULL DEFAULT 0,
    bottom_depth_meters DECIMAL(10,3),
    distance_to_shore_km DECIMAL(10,3),
    habitat_type VARCHAR(100),
    substrate_type VARCHAR(100),
    protection_status VARCHAR(100),
    sampling_protocol VARCHAR(255),
    sample_volume_liters DECIMAL(10,3),
    preservation_method VARCHAR(100),
    storage_temperature_celsius DECIMAL(5,2),
    chain_of_custody TEXT,
    data_quality data_quality DEFAULT 'RAW',
    qc_flags TEXT[],
    comments TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Oceanographic Data Table (Enhanced)
CREATE TABLE IF NOT EXISTS oceanographic_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    measurement_id VARCHAR(100) UNIQUE NOT NULL,
    sampling_point_id UUID REFERENCES sampling_points(id) ON DELETE CASCADE,
    sampling_event_id UUID REFERENCES sampling_events(id) ON DELETE CASCADE,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    depth_meters DECIMAL(10,3) NOT NULL,
    
    -- Physical Parameters
    temperature_celsius DECIMAL(8,4),
    temperature_qc_flag INTEGER DEFAULT 0,
    salinity_psu DECIMAL(8,4),
    salinity_qc_flag INTEGER DEFAULT 0,
    pressure_dbar DECIMAL(10,3),
    pressure_qc_flag INTEGER DEFAULT 0,
    density_kg_m3 DECIMAL(10,6),
    density_qc_flag INTEGER DEFAULT 0,
    sound_velocity_ms DECIMAL(8,3),
    sound_velocity_qc_flag INTEGER DEFAULT 0,
    
    -- Chemical Parameters
    ph_level DECIMAL(6,4),
    ph_qc_flag INTEGER DEFAULT 0,
    dissolved_oxygen_mg_per_l DECIMAL(8,4),
    dissolved_oxygen_qc_flag INTEGER DEFAULT 0,
    dissolved_oxygen_percent DECIMAL(6,2),
    nitrate_umol_l DECIMAL(8,4),
    nitrite_umol_l DECIMAL(8,4),
    ammonia_umol_l DECIMAL(8,4),
    phosphate_umol_l DECIMAL(8,4),
    silicate_umol_l DECIMAL(8,4),
    total_alkalinity_umol_kg DECIMAL(8,2),
    dissolved_inorganic_carbon_umol_kg DECIMAL(8,2),
    
    -- Optical Parameters
    turbidity_ntu DECIMAL(8,4),
    turbidity_qc_flag INTEGER DEFAULT 0,
    chlorophyll_a_mg_m3 DECIMAL(8,4),
    chlorophyll_qc_flag INTEGER DEFAULT 0,
    suspended_particulate_matter_mg_l DECIMAL(8,4),
    colored_dissolved_organic_matter_ppb DECIMAL(8,4),
    
    -- Current Data
    current_speed_cm_s DECIMAL(8,3),
    current_direction_degrees INTEGER CHECK (current_direction_degrees BETWEEN 0 AND 360),
    current_qc_flag INTEGER DEFAULT 0,
    
    -- Instrument Information
    instrument_type VARCHAR(100),
    instrument_serial VARCHAR(100),
    calibration_date DATE,
    data_quality data_quality DEFAULT 'RAW',
    processing_level INTEGER DEFAULT 0,
    qc_flags TEXT[],
    measurement_uncertainty DECIMAL(8,6),
    detection_limit DECIMAL(8,6),
    
    -- Additional Data
    comments TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Species Metadata Table (PostgreSQL side for relational data)
CREATE TABLE IF NOT EXISTS species_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    species_id VARCHAR(50) UNIQUE NOT NULL,
    scientific_name VARCHAR(255) NOT NULL,
    common_name VARCHAR(255),
    authority VARCHAR(255),
    taxonomic_status VARCHAR(50) DEFAULT 'ACCEPTED',
    
    -- Taxonomy
    kingdom VARCHAR(100),
    phylum VARCHAR(100),
    class VARCHAR(100),
    order_name VARCHAR(100), -- 'order' is reserved keyword
    family VARCHAR(100),
    genus VARCHAR(100),
    species VARCHAR(100),
    subspecies VARCHAR(100),
    
    -- Conservation Status
    iucn_status VARCHAR(50),
    cites_status VARCHAR(50),
    national_status VARCHAR(100),
    
    -- Ecological Information
    habitat_type VARCHAR(100),
    depth_range_min_m DECIMAL(10,3),
    depth_range_max_m DECIMAL(10,3),
    temperature_range_min_c DECIMAL(6,3),
    temperature_range_max_c DECIMAL(6,3),
    salinity_range_min_psu DECIMAL(6,3),
    salinity_range_max_psu DECIMAL(6,3),
    geographic_distribution TEXT,
    feeding_type VARCHAR(100),
    trophic_level DECIMAL(4,2),
    
    -- Reference Information
    reference_source VARCHAR(255),
    reference_url TEXT,
    data_source VARCHAR(100) NOT NULL,
    confidence_level confidence_level DEFAULT 'MEDIUM',
    
    -- Temporal Information
    date_added DATE DEFAULT CURRENT_DATE,
    last_verified DATE,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Biological Observations Table
CREATE TABLE IF NOT EXISTS biological_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    observation_id VARCHAR(100) UNIQUE NOT NULL,
    sampling_point_id UUID REFERENCES sampling_points(id) ON DELETE CASCADE,
    species_id VARCHAR(50) REFERENCES species_metadata(species_id) ON DELETE SET NULL,
    observed_name VARCHAR(255) NOT NULL,
    identification_method VARCHAR(100),
    identification_confidence confidence_level DEFAULT 'MEDIUM',
    
    -- Abundance Data
    abundance_count INTEGER,
    abundance_density_per_m2 DECIMAL(12,6),
    abundance_density_per_m3 DECIMAL(12,6),
    biomass_g_per_m2 DECIMAL(12,6),
    biomass_g_per_m3 DECIMAL(12,6),
    
    -- Size Data
    length_min_mm DECIMAL(8,3),
    length_max_mm DECIMAL(8,3),
    length_mean_mm DECIMAL(8,3),
    width_min_mm DECIMAL(8,3),
    width_max_mm DECIMAL(8,3),
    width_mean_mm DECIMAL(8,3),
    weight_min_g DECIMAL(10,6),
    weight_max_g DECIMAL(10,6),
    weight_mean_g DECIMAL(10,6),
    
    -- Life Stage
    life_stage VARCHAR(50),
    maturity_stage VARCHAR(50),
    sex VARCHAR(20),
    
    -- Environmental Context
    associated_species TEXT[],
    behavior_notes TEXT,
    condition_assessment VARCHAR(100),
    
    -- Quality Control
    data_quality data_quality DEFAULT 'RAW',
    qc_flags TEXT[],
    observer_name VARCHAR(255),
    verification_status VARCHAR(50) DEFAULT 'UNVERIFIED',
    verified_by VARCHAR(255),
    verification_date DATE,
    
    comments TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Data Processing Log Table
CREATE TABLE IF NOT EXISTS data_processing_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    process_id VARCHAR(100) UNIQUE NOT NULL,
    process_type VARCHAR(100) NOT NULL,
    input_table VARCHAR(100),
    input_record_id UUID,
    processing_algorithm VARCHAR(255),
    algorithm_version VARCHAR(50),
    parameters JSONB,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'PENDING',
    error_message TEXT,
    output_records INTEGER DEFAULT 0,
    processing_notes TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Research Projects Indexes
CREATE INDEX IF NOT EXISTS idx_research_projects_code ON research_projects(project_code);
CREATE INDEX IF NOT EXISTS idx_research_projects_status ON research_projects(status);
CREATE INDEX IF NOT EXISTS idx_research_projects_dates ON research_projects(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_research_projects_institution ON research_projects(institution);

-- Research Vessels Indexes
CREATE INDEX IF NOT EXISTS idx_research_vessels_code ON research_vessels(vessel_code);
CREATE INDEX IF NOT EXISTS idx_research_vessels_country ON research_vessels(country_flag);

-- Sampling Events Indexes
CREATE INDEX IF NOT EXISTS idx_sampling_events_event_id ON sampling_events(event_id);
CREATE INDEX IF NOT EXISTS idx_sampling_events_project_id ON sampling_events(project_id);
CREATE INDEX IF NOT EXISTS idx_sampling_events_vessel_id ON sampling_events(vessel_id);
CREATE INDEX IF NOT EXISTS idx_sampling_events_datetime ON sampling_events(start_datetime, end_datetime);
CREATE INDEX IF NOT EXISTS idx_sampling_events_location ON sampling_events USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_sampling_events_type ON sampling_events(event_type);
CREATE INDEX IF NOT EXISTS idx_sampling_events_method ON sampling_events(sampling_method);
CREATE INDEX IF NOT EXISTS idx_sampling_events_quality ON sampling_events(data_quality);

-- Sampling Points Indexes
CREATE INDEX IF NOT EXISTS idx_sampling_points_point_id ON sampling_points(point_id);
CREATE INDEX IF NOT EXISTS idx_sampling_points_event_id ON sampling_points(sampling_event_id);
CREATE INDEX IF NOT EXISTS idx_sampling_points_location ON sampling_points USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_sampling_points_timestamp ON sampling_points(timestamp);
CREATE INDEX IF NOT EXISTS idx_sampling_points_depth ON sampling_points(depth_meters);
CREATE INDEX IF NOT EXISTS idx_sampling_points_habitat ON sampling_points(habitat_type);
CREATE INDEX IF NOT EXISTS idx_sampling_points_quality ON sampling_points(data_quality);

-- Oceanographic Data Indexes
CREATE INDEX IF NOT EXISTS idx_oceanographic_measurement_id ON oceanographic_data(measurement_id);
CREATE INDEX IF NOT EXISTS idx_oceanographic_point_id ON oceanographic_data(sampling_point_id);
CREATE INDEX IF NOT EXISTS idx_oceanographic_event_id ON oceanographic_data(sampling_event_id);
CREATE INDEX IF NOT EXISTS idx_oceanographic_location ON oceanographic_data USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_oceanographic_timestamp ON oceanographic_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_oceanographic_depth ON oceanographic_data(depth_meters);
CREATE INDEX IF NOT EXISTS idx_oceanographic_temperature ON oceanographic_data(temperature_celsius);
CREATE INDEX IF NOT EXISTS idx_oceanographic_salinity ON oceanographic_data(salinity_psu);
CREATE INDEX IF NOT EXISTS idx_oceanographic_quality ON oceanographic_data(data_quality);
CREATE INDEX IF NOT EXISTS idx_oceanographic_instrument ON oceanographic_data(instrument_type);

-- Species Metadata Indexes
CREATE INDEX IF NOT EXISTS idx_species_metadata_species_id ON species_metadata(species_id);
CREATE INDEX IF NOT EXISTS idx_species_metadata_scientific_name ON species_metadata(scientific_name);
CREATE INDEX IF NOT EXISTS idx_species_metadata_common_name ON species_metadata(common_name);
CREATE INDEX IF NOT EXISTS idx_species_metadata_taxonomy ON species_metadata(kingdom, phylum, class, order_name, family, genus);
CREATE INDEX IF NOT EXISTS idx_species_metadata_iucn ON species_metadata(iucn_status);
CREATE INDEX IF NOT EXISTS idx_species_metadata_habitat ON species_metadata(habitat_type);
CREATE INDEX IF NOT EXISTS idx_species_metadata_source ON species_metadata(data_source);
CREATE INDEX IF NOT EXISTS idx_species_metadata_confidence ON species_metadata(confidence_level);

-- Biological Observations Indexes
CREATE INDEX IF NOT EXISTS idx_biological_observations_obs_id ON biological_observations(observation_id);
CREATE INDEX IF NOT EXISTS idx_biological_observations_point_id ON biological_observations(sampling_point_id);
CREATE INDEX IF NOT EXISTS idx_biological_observations_species_id ON biological_observations(species_id);
CREATE INDEX IF NOT EXISTS idx_biological_observations_name ON biological_observations(observed_name);
CREATE INDEX IF NOT EXISTS idx_biological_observations_method ON biological_observations(identification_method);
CREATE INDEX IF NOT EXISTS idx_biological_observations_confidence ON biological_observations(identification_confidence);
CREATE INDEX IF NOT EXISTS idx_biological_observations_life_stage ON biological_observations(life_stage);
CREATE INDEX IF NOT EXISTS idx_biological_observations_quality ON biological_observations(data_quality);

-- Data Processing Log Indexes
CREATE INDEX IF NOT EXISTS idx_data_processing_log_process_id ON data_processing_log(process_id);
CREATE INDEX IF NOT EXISTS idx_data_processing_log_type ON data_processing_log(process_type);
CREATE INDEX IF NOT EXISTS idx_data_processing_log_status ON data_processing_log(status);
CREATE INDEX IF NOT EXISTS idx_data_processing_log_time ON data_processing_log(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_data_processing_log_input ON data_processing_log(input_table, input_record_id);

-- =====================================================
-- ADDITIONAL CONSTRAINTS AND TRIGGERS
-- =====================================================

-- Add check constraints
ALTER TABLE sampling_events ADD CONSTRAINT chk_sampling_events_datetime 
    CHECK (end_datetime IS NULL OR end_datetime >= start_datetime);

ALTER TABLE sampling_points ADD CONSTRAINT chk_sampling_points_depth 
    CHECK (depth_meters >= 0);

ALTER TABLE sampling_points ADD CONSTRAINT chk_sampling_points_bottom_depth 
    CHECK (bottom_depth_meters IS NULL OR bottom_depth_meters >= depth_meters);

ALTER TABLE oceanographic_data ADD CONSTRAINT chk_oceanographic_depth 
    CHECK (depth_meters >= 0);

ALTER TABLE oceanographic_data ADD CONSTRAINT chk_oceanographic_temperature 
    CHECK (temperature_celsius IS NULL OR temperature_celsius BETWEEN -5 AND 50);

ALTER TABLE oceanographic_data ADD CONSTRAINT chk_oceanographic_salinity 
    CHECK (salinity_psu IS NULL OR salinity_psu BETWEEN 0 AND 50);

ALTER TABLE oceanographic_data ADD CONSTRAINT chk_oceanographic_ph 
    CHECK (ph_level IS NULL OR ph_level BETWEEN 6 AND 10);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers to all tables
CREATE TRIGGER update_research_projects_updated_at BEFORE UPDATE ON research_projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_vessels_updated_at BEFORE UPDATE ON research_vessels 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sampling_events_updated_at BEFORE UPDATE ON sampling_events 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sampling_points_updated_at BEFORE UPDATE ON sampling_points 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_oceanographic_data_updated_at BEFORE UPDATE ON oceanographic_data 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_species_metadata_updated_at BEFORE UPDATE ON species_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_biological_observations_updated_at BEFORE UPDATE ON biological_observations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for complete sampling information
CREATE OR REPLACE VIEW sampling_summary AS
SELECT 
    se.id as event_id,
    se.event_id as event_code,
    se.event_name,
    se.event_type,
    se.start_datetime,
    se.end_datetime,
    ST_AsText(se.location) as location_wkt,
    ST_X(se.location::geometry) as longitude,
    ST_Y(se.location::geometry) as latitude,
    se.water_depth_meters,
    se.sampling_method,
    rp.project_name,
    rp.principal_investigator,
    rv.vessel_name,
    COUNT(sp.id) as sampling_points_count,
    COUNT(od.id) as oceanographic_measurements_count,
    COUNT(bo.id) as biological_observations_count
FROM sampling_events se
LEFT JOIN research_projects rp ON se.project_id = rp.id
LEFT JOIN research_vessels rv ON se.vessel_id = rv.id
LEFT JOIN sampling_points sp ON se.id = sp.sampling_event_id
LEFT JOIN oceanographic_data od ON se.id = od.sampling_event_id
LEFT JOIN biological_observations bo ON sp.id = bo.sampling_point_id
GROUP BY se.id, se.event_id, se.event_name, se.event_type, se.start_datetime, 
         se.end_datetime, se.location, se.water_depth_meters, se.sampling_method,
         rp.project_name, rp.principal_investigator, rv.vessel_name;

-- View for oceanographic data with spatial information
CREATE OR REPLACE VIEW oceanographic_summary AS
SELECT 
    od.id,
    od.measurement_id,
    od.timestamp,
    ST_AsText(od.location) as location_wkt,
    ST_X(od.location::geometry) as longitude,
    ST_Y(od.location::geometry) as latitude,
    od.depth_meters,
    od.temperature_celsius,
    od.salinity_psu,
    od.ph_level,
    od.dissolved_oxygen_mg_per_l,
    od.turbidity_ntu,
    od.chlorophyll_a_mg_m3,
    od.data_quality,
    se.event_name,
    se.sampling_method,
    rp.project_name
FROM oceanographic_data od
LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
LEFT JOIN research_projects rp ON se.project_id = rp.id;

-- =====================================================
-- GRANTS AND PERMISSIONS
-- =====================================================

-- Create application role
CREATE ROLE marine_app_user;
GRANT CONNECT ON DATABASE postgres TO marine_app_user;
GRANT USAGE ON SCHEMA public TO marine_app_user;

-- Grant permissions on all tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO marine_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO marine_app_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO marine_app_user;

-- Grant permissions on views
GRANT SELECT ON sampling_summary TO marine_app_user;
GRANT SELECT ON oceanographic_summary TO marine_app_user;

-- Comments for documentation
COMMENT ON TABLE research_projects IS 'Research projects and expeditions conducting marine data collection';
COMMENT ON TABLE research_vessels IS 'Research vessels used for data collection';
COMMENT ON TABLE sampling_events IS 'Discrete sampling events or stations during research cruises';
COMMENT ON TABLE sampling_points IS 'Individual sampling points within sampling events';
COMMENT ON TABLE oceanographic_data IS 'Physical and chemical oceanographic measurements';
COMMENT ON TABLE species_metadata IS 'Species taxonomy and ecological metadata';
COMMENT ON TABLE biological_observations IS 'Biological observations and species abundance data';
COMMENT ON TABLE data_processing_log IS 'Log of all data processing operations';