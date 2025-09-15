-- Marine Data Integration Platform - PostgreSQL Database Initialization Script
-- This script creates the database, user, and applies the schema

-- Note: This script should be run as a PostgreSQL superuser (postgres)

\echo 'Starting PostgreSQL database initialization for Marine Data Platform...'

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE marine_platform' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'marine_platform')\gexec

-- Connect to the marine_platform database
\c marine_platform

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

\echo 'Extensions enabled successfully'

-- Create application user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'marine_app_user') THEN
        CREATE ROLE marine_app_user WITH LOGIN PASSWORD 'marine_platform_2024!';
        RAISE NOTICE 'Created user: marine_app_user';
    ELSE
        RAISE NOTICE 'User marine_app_user already exists';
    END IF;
END
$$;

-- Grant database connection permission
GRANT CONNECT ON DATABASE marine_platform TO marine_app_user;
GRANT USAGE ON SCHEMA public TO marine_app_user;

\echo 'User permissions configured'

-- Apply the main schema
\echo 'Applying database schema...'
\i schema.sql

\echo 'Schema applied successfully'

-- Additional performance optimizations
\echo 'Applying performance optimizations...'

-- Set better default statistics target for better query planning
ALTER DATABASE marine_platform SET default_statistics_target = 100;

-- Enable parallel query execution
ALTER DATABASE marine_platform SET max_parallel_workers_per_gather = 4;
ALTER DATABASE marine_platform SET max_parallel_workers = 8;

-- Configure work memory for complex queries
ALTER DATABASE marine_platform SET work_mem = '256MB';

-- Configure maintenance work memory for index operations
ALTER DATABASE marine_platform SET maintenance_work_mem = '1GB';

-- Enable query optimization for PostGIS operations
ALTER DATABASE marine_platform SET random_page_cost = 1.1;

\echo 'Performance optimizations applied'

-- Create additional utility functions
\echo 'Creating utility functions...'

-- Function to calculate distance between two geographic points
CREATE OR REPLACE FUNCTION calculate_distance_km(
    point1 GEOGRAPHY,
    point2 GEOGRAPHY
) RETURNS NUMERIC AS $$
BEGIN
    RETURN ST_Distance(point1, point2) / 1000.0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to generate sampling event IDs
CREATE OR REPLACE FUNCTION generate_event_id(
    project_code VARCHAR(50),
    vessel_code VARCHAR(20),
    event_date DATE
) RETURNS VARCHAR(100) AS $$
BEGIN
    RETURN CONCAT(
        project_code, 
        '_', 
        vessel_code, 
        '_', 
        TO_CHAR(event_date, 'YYYY'),
        TO_CHAR(event_date, 'MM'),
        TO_CHAR(event_date, 'DD'),
        '_',
        LPAD(EXTRACT(epoch FROM CURRENT_TIMESTAMP)::TEXT, 10, '0')
    );
END;
$$ LANGUAGE plpgsql;

-- Function to validate geographic coordinates
CREATE OR REPLACE FUNCTION is_valid_coordinates(
    longitude NUMERIC,
    latitude NUMERIC
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN (
        longitude IS NOT NULL AND 
        latitude IS NOT NULL AND
        longitude BETWEEN -180 AND 180 AND
        latitude BETWEEN -90 AND 90
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate water density from temperature and salinity
CREATE OR REPLACE FUNCTION calculate_seawater_density(
    temperature_celsius NUMERIC,
    salinity_psu NUMERIC,
    pressure_dbar NUMERIC DEFAULT 0
) RETURNS NUMERIC AS $$
DECLARE
    t NUMERIC := temperature_celsius;
    s NUMERIC := salinity_psu;
    p NUMERIC := pressure_dbar;
    density NUMERIC;
BEGIN
    -- UNESCO 1983 equation for seawater density
    -- Simplified version - for precise calculations, use full UNESCO equation
    IF t IS NULL OR s IS NULL THEN
        RETURN NULL;
    END IF;
    
    density := 999.842594 + 6.793952e-2 * t - 9.095290e-3 * t^2 + 1.001685e-4 * t^3
               - 1.120083e-6 * t^4 + 6.536332e-9 * t^5
               + (8.24493e-1 - 4.0899e-3 * t + 7.6438e-5 * t^2 - 8.2467e-7 * t^3 + 5.3875e-9 * t^4) * s
               + (-5.72466e-3 + 1.0227e-4 * t - 1.6546e-6 * t^2) * s^1.5
               + 4.8314e-4 * s^2;
    
    -- Apply pressure correction (simplified)
    density := density + (p * 4.5e-6 * density);
    
    RETURN density;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to validate oceanographic data ranges
CREATE OR REPLACE FUNCTION validate_oceanographic_ranges(
    temperature_celsius NUMERIC,
    salinity_psu NUMERIC,
    ph_level NUMERIC,
    dissolved_oxygen_mg_per_l NUMERIC
) RETURNS TEXT[] AS $$
DECLARE
    warnings TEXT[] := '{}';
BEGIN
    -- Check temperature range
    IF temperature_celsius IS NOT NULL AND (temperature_celsius < -2 OR temperature_celsius > 40) THEN
        warnings := array_append(warnings, 'Temperature outside typical marine range (-2 to 40°C)');
    END IF;
    
    -- Check salinity range
    IF salinity_psu IS NOT NULL AND (salinity_psu < 0 OR salinity_psu > 45) THEN
        warnings := array_append(warnings, 'Salinity outside typical marine range (0 to 45 PSU)');
    END IF;
    
    -- Check pH range
    IF ph_level IS NOT NULL AND (ph_level < 6.5 OR ph_level > 9.0) THEN
        warnings := array_append(warnings, 'pH outside typical marine range (6.5 to 9.0)');
    END IF;
    
    -- Check dissolved oxygen range
    IF dissolved_oxygen_mg_per_l IS NOT NULL AND (dissolved_oxygen_mg_per_l < 0 OR dissolved_oxygen_mg_per_l > 20) THEN
        warnings := array_append(warnings, 'Dissolved oxygen outside typical range (0 to 20 mg/L)');
    END IF;
    
    RETURN warnings;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

\echo 'Utility functions created'

-- Create materialized views for common analytical queries
\echo 'Creating materialized views...'

-- Materialized view for station summary statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS station_summary_stats AS
SELECT 
    se.id as sampling_event_id,
    se.event_id,
    se.event_name,
    ST_X(se.location::geometry) as longitude,
    ST_Y(se.location::geometry) as latitude,
    se.start_datetime,
    se.water_depth_meters,
    COUNT(DISTINCT sp.id) as sampling_points_count,
    COUNT(DISTINCT od.id) as oceanographic_measurements_count,
    COUNT(DISTINCT bo.id) as biological_observations_count,
    COUNT(DISTINCT bo.species_id) as unique_species_count,
    AVG(od.temperature_celsius) as avg_temperature,
    MIN(od.temperature_celsius) as min_temperature,
    MAX(od.temperature_celsius) as max_temperature,
    AVG(od.salinity_psu) as avg_salinity,
    MIN(od.salinity_psu) as min_salinity,
    MAX(od.salinity_psu) as max_salinity,
    AVG(od.ph_level) as avg_ph,
    AVG(od.dissolved_oxygen_mg_per_l) as avg_dissolved_oxygen,
    MIN(od.depth_meters) as min_sampling_depth,
    MAX(od.depth_meters) as max_sampling_depth
FROM sampling_events se
LEFT JOIN sampling_points sp ON se.id = sp.sampling_event_id
LEFT JOIN oceanographic_data od ON se.id = od.sampling_event_id
LEFT JOIN biological_observations bo ON sp.id = bo.sampling_point_id
GROUP BY se.id, se.event_id, se.event_name, se.location, se.start_datetime, se.water_depth_meters;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_station_summary_stats_event_id ON station_summary_stats(event_id);
CREATE INDEX IF NOT EXISTS idx_station_summary_stats_datetime ON station_summary_stats(start_datetime);
CREATE INDEX IF NOT EXISTS idx_station_summary_stats_location ON station_summary_stats(longitude, latitude);

-- Materialized view for species distribution summary
CREATE MATERIALIZED VIEW IF NOT EXISTS species_distribution_summary AS
SELECT 
    sm.species_id,
    sm.scientific_name,
    sm.common_name,
    sm.kingdom,
    sm.phylum,
    sm.class,
    sm.order_name,
    sm.family,
    sm.genus,
    COUNT(DISTINCT bo.sampling_point_id) as occurrence_count,
    COUNT(DISTINCT se.id) as sampling_events_count,
    MIN(se.start_datetime) as first_observed,
    MAX(se.start_datetime) as last_observed,
    AVG(bo.abundance_count) as avg_abundance,
    ST_Extent(sp.location::geometry) as geographic_extent
FROM species_metadata sm
JOIN biological_observations bo ON sm.species_id = bo.species_id
JOIN sampling_points sp ON bo.sampling_point_id = sp.id
JOIN sampling_events se ON sp.sampling_event_id = se.id
GROUP BY sm.species_id, sm.scientific_name, sm.common_name, sm.kingdom, 
         sm.phylum, sm.class, sm.order_name, sm.family, sm.genus;

-- Create index on species distribution materialized view
CREATE INDEX IF NOT EXISTS idx_species_dist_summary_species_id ON species_distribution_summary(species_id);
CREATE INDEX IF NOT EXISTS idx_species_dist_summary_taxonomy ON species_distribution_summary(kingdom, phylum, class, order_name, family);

\echo 'Materialized views created'

-- Create stored procedures for common operations
\echo 'Creating stored procedures...'

-- Procedure to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW station_summary_stats;
    REFRESH MATERIALIZED VIEW species_distribution_summary;
    
    RAISE NOTICE 'All materialized views refreshed successfully';
END;
$$ LANGUAGE plpgsql;

-- Procedure to insert sampling event with validation
CREATE OR REPLACE FUNCTION insert_sampling_event(
    p_event_id VARCHAR(100),
    p_project_id UUID,
    p_vessel_id UUID,
    p_event_name VARCHAR(255),
    p_event_type VARCHAR(50),
    p_start_datetime TIMESTAMP WITH TIME ZONE,
    p_longitude NUMERIC,
    p_latitude NUMERIC,
    p_water_depth_meters NUMERIC DEFAULT NULL,
    p_sampling_method sampling_method DEFAULT 'CTD'
) RETURNS UUID AS $$
DECLARE
    event_uuid UUID;
    location_point GEOGRAPHY;
BEGIN
    -- Validate coordinates
    IF NOT is_valid_coordinates(p_longitude, p_latitude) THEN
        RAISE EXCEPTION 'Invalid coordinates: longitude=%, latitude=%', p_longitude, p_latitude;
    END IF;
    
    -- Create geography point
    location_point := ST_GeogFromText('POINT(' || p_longitude || ' ' || p_latitude || ')');
    
    -- Insert sampling event
    INSERT INTO sampling_events (
        event_id, project_id, vessel_id, event_name, event_type,
        start_datetime, location, water_depth_meters, sampling_method
    ) VALUES (
        p_event_id, p_project_id, p_vessel_id, p_event_name, p_event_type,
        p_start_datetime, location_point, p_water_depth_meters, p_sampling_method
    ) RETURNING id INTO event_uuid;
    
    RAISE NOTICE 'Sampling event created with ID: %', event_uuid;
    RETURN event_uuid;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions on functions to application user
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO marine_app_user;

\echo 'Stored procedures created'

-- Final permissions and cleanup
\echo 'Finalizing permissions...'

-- Grant permissions on all current and future tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO marine_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO marine_app_user;

-- Grant permissions on materialized views
GRANT SELECT ON station_summary_stats TO marine_app_user;
GRANT SELECT ON species_distribution_summary TO marine_app_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO marine_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO marine_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO marine_app_user;

\echo 'Permissions finalized'

-- Database statistics and information
\echo 'Database initialization completed!'
\echo 'Database: marine_platform'
\echo 'Schema: public'
\echo 'Application user: marine_app_user'

-- Show created objects summary
SELECT 
    'Tables' as object_type,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'

UNION ALL

SELECT 
    'Views' as object_type,
    COUNT(*) as count
FROM information_schema.views 
WHERE table_schema = 'public'

UNION ALL

SELECT 
    'Materialized Views' as object_type,
    COUNT(*) as count
FROM pg_matviews 
WHERE schemaname = 'public'

UNION ALL

SELECT 
    'Functions' as object_type,
    COUNT(*) as count
FROM information_schema.routines 
WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'

UNION ALL

SELECT 
    'Indexes' as object_type,
    COUNT(*) as count
FROM pg_indexes 
WHERE schemaname = 'public';

\echo 'PostgreSQL initialization complete! Database is ready for use.'

-- Show connection information
\echo 'Connection details:'
\echo '  Database: marine_platform'
\echo '  User: marine_app_user'
\echo '  Default port: 5432'
\echo '  Extensions enabled: postgis, uuid-ossp, btree_gist, pg_trgm'