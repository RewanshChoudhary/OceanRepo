-- Marine Data Integration Platform - PostgreSQL Schema
-- Enable PostGIS Extension for spatial data support
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sampling Points Table
-- Stores geographic locations where marine samples were collected
CREATE TABLE IF NOT EXISTS sampling_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location GEOMETRY(Point, 4326) NOT NULL,  -- WGS84 coordinate system
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    depth_meters FLOAT,
    parameters JSONB,  -- Store flexible parameters like temperature, pH, salinity
    metadata JSONB,    -- Store sampling method, equipment used, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index for efficient location-based queries
CREATE INDEX IF NOT EXISTS idx_sampling_location ON sampling_points USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_sampling_timestamp ON sampling_points(timestamp);
CREATE INDEX IF NOT EXISTS idx_sampling_parameters ON sampling_points USING GIN(parameters);

-- Oceanographic Data Table  
-- Stores measured oceanographic parameters
CREATE TABLE IF NOT EXISTS oceanographic_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sampling_point_id UUID REFERENCES sampling_points(id) ON DELETE CASCADE,
    location GEOMETRY(Point, 4326) NOT NULL,
    parameter_type VARCHAR(100) NOT NULL,  -- e.g., 'temperature', 'salinity', 'pH', 'dissolved_oxygen'
    value FLOAT NOT NULL,
    unit VARCHAR(20),  -- e.g., 'celsius', 'ppm', 'mg/L'
    measurement_depth FLOAT,  -- depth at which measurement was taken
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    quality_flag VARCHAR(10) DEFAULT 'GOOD',  -- GOOD, SUSPECT, BAD
    instrument_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_oceanographic_location ON oceanographic_data USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_oceanographic_parameter ON oceanographic_data(parameter_type);
CREATE INDEX IF NOT EXISTS idx_oceanographic_timestamp ON oceanographic_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_oceanographic_sampling_point ON oceanographic_data(sampling_point_id);

-- Morphometric Data Table
-- Stores physical measurements and characteristics of marine specimens
CREATE TABLE IF NOT EXISTS morphometric_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    species_id VARCHAR(50),  -- Links to MongoDB taxonomy collection
    specimen_id VARCHAR(100) UNIQUE,
    image_path VARCHAR(255),
    sample_location GEOMETRY(Point, 4326),
    depth_collected FLOAT,
    metrics JSONB,  -- Store measurements like length, weight, width, etc.
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    collector_name VARCHAR(100),
    preservation_method VARCHAR(100),
    condition_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_morphometric_location ON morphometric_data USING GIST(sample_location);
CREATE INDEX IF NOT EXISTS idx_morphometric_species ON morphometric_data(species_id);
CREATE INDEX IF NOT EXISTS idx_morphometric_specimen ON morphometric_data(specimen_id);
CREATE INDEX IF NOT EXISTS idx_morphometric_timestamp ON morphometric_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_morphometric_metrics ON morphometric_data USING GIN(metrics);

-- Environmental Zones Table
-- Define marine environmental zones for analysis
CREATE TABLE IF NOT EXISTS environmental_zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(50),  -- e.g., 'coastal', 'pelagic', 'benthic', 'coral_reef'
    boundary GEOMETRY(Polygon, 4326),  -- Geographic boundary of the zone
    depth_range_min FLOAT,
    depth_range_max FLOAT,
    characteristics JSONB,  -- Store zone-specific characteristics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_environmental_zones_boundary ON environmental_zones USING GIST(boundary);
CREATE INDEX IF NOT EXISTS idx_environmental_zones_type ON environmental_zones(zone_type);

-- Data Quality Logs Table
-- Track data quality issues and validation results
CREATE TABLE IF NOT EXISTS data_quality_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    quality_check VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- PASSED, FAILED, WARNING
    message TEXT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quality_logs_table ON data_quality_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_quality_logs_status ON data_quality_logs(status);

-- Create a view for easy querying of sampling data with environmental context
CREATE OR REPLACE VIEW sampling_summary AS
SELECT 
    sp.id,
    sp.location,
    ST_X(sp.location) as longitude,
    ST_Y(sp.location) as latitude,
    sp.timestamp,
    sp.depth_meters,
    sp.parameters,
    sp.metadata,
    COUNT(od.id) as oceanographic_measurements,
    COUNT(md.id) as morphometric_specimens
FROM sampling_points sp
LEFT JOIN oceanographic_data od ON sp.id = od.sampling_point_id
LEFT JOIN morphometric_data md ON ST_DWithin(sp.location, md.sample_location, 0.01)  -- Within ~1km
GROUP BY sp.id, sp.location, sp.timestamp, sp.depth_meters, sp.parameters, sp.metadata;

-- Insert some sample environmental zones
INSERT INTO environmental_zones (zone_name, zone_type, boundary, depth_range_min, depth_range_max, characteristics) 
VALUES 
    ('Arabian Sea Coastal', 'coastal', 
     ST_GeomFromText('POLYGON((68 8, 78 8, 78 25, 68 25, 68 8))', 4326),
     0, 200,
     '{"water_type": "coastal", "primary_currents": "monsoon_driven", "productivity": "high"}'::jsonb),
    ('Bay of Bengal Deep Water', 'pelagic',
     ST_GeomFromText('POLYGON((80 5, 95 5, 95 22, 80 22, 80 5))', 4326), 
     200, 4000,
     '{"water_type": "oceanic", "primary_currents": "cyclonic", "productivity": "moderate"}'::jsonb)
ON CONFLICT DO NOTHING;

-- Function to calculate distance between sampling points
CREATE OR REPLACE FUNCTION sampling_distance(point1_id UUID, point2_id UUID)
RETURNS FLOAT AS $$
DECLARE
    distance FLOAT;
BEGIN
    SELECT ST_Distance(
        ST_Transform(sp1.location, 3857),
        ST_Transform(sp2.location, 3857)
    ) / 1000.0 INTO distance  -- Convert to kilometers
    FROM sampling_points sp1, sampling_points sp2
    WHERE sp1.id = point1_id AND sp2.id = point2_id;
    
    RETURN distance;
END;
$$ LANGUAGE plpgsql;

-- Function to find nearby sampling points within a radius
CREATE OR REPLACE FUNCTION find_nearby_samples(
    center_lon FLOAT, 
    center_lat FLOAT, 
    radius_km FLOAT DEFAULT 10.0
)
RETURNS TABLE(
    sample_id UUID,
    distance_km FLOAT,
    longitude FLOAT,
    latitude FLOAT,
    sample_timestamp TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sp.id,
        ST_Distance(
            ST_Transform(ST_SetSRID(ST_Point(center_lon, center_lat), 4326), 3857),
            ST_Transform(sp.location, 3857)
        ) / 1000.0 as distance_km,
        ST_X(sp.location) as longitude,
        ST_Y(sp.location) as latitude,
        sp.timestamp
    FROM sampling_points sp
    WHERE ST_DWithin(
        ST_Transform(ST_SetSRID(ST_Point(center_lon, center_lat), 4326), 3857),
        ST_Transform(sp.location, 3857),
        radius_km * 1000
    )
    ORDER BY distance_km;
END;
$$ LANGUAGE plpgsql;