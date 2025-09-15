-- Marine Data Integration Platform - PostgreSQL Sample Data
-- Comprehensive test data to validate schema functionality

\echo 'Inserting sample data for Marine Data Platform...'

-- =====================================================
-- RESEARCH PROJECTS
-- =====================================================

INSERT INTO research_projects (
    project_name, project_code, description, principal_investigator, 
    institution, start_date, end_date, budget, status, metadata
) VALUES 
(
    'Atlantic Marine Biodiversity Survey',
    'AMBS2024',
    'Comprehensive survey of marine biodiversity in the North Atlantic Ocean focusing on climate change impacts',
    'Dr. Sarah Johnson',
    'Bedford Institute of Oceanography',
    '2024-01-15',
    '2026-12-31',
    2500000.00,
    'ACTIVE',
    '{"funding_agency": "NSERC", "vessel_days": 120, "sampling_sites": 50}'
),
(
    'Coastal Ecosystem Monitoring Program',
    'CEMP2024',
    'Long-term monitoring of coastal marine ecosystems in the Bay of Fundy',
    'Dr. Michael Chen',
    'Dalhousie University',
    '2024-03-01',
    '2027-02-28',
    1800000.00,
    'ACTIVE',
    '{"funding_agency": "DFO", "monitoring_frequency": "monthly", "focus": "eDNA analysis"}'
),
(
    'Deep Sea Exploration Initiative',
    'DSEI2023',
    'Investigation of deep-sea habitats and biodiversity in Canadian waters',
    'Dr. Emily Rodriguez',
    'Memorial University',
    '2023-06-01',
    '2024-05-31',
    3200000.00,
    'COMPLETED',
    '{"funding_agency": "CFI", "max_depth": 3000, "ROV_missions": 25}'
);

-- =====================================================
-- RESEARCH VESSELS
-- =====================================================

INSERT INTO research_vessels (
    vessel_name, vessel_code, country_flag, length_meters, beam_meters,
    draft_meters, gross_tonnage, max_speed_knots, crew_capacity,
    scientific_capacity, equipment_capabilities, metadata
) VALUES
(
    'CCGS Hudson',
    'CCGS-HUD',
    'CA',
    90.5,
    15.2,
    5.8,
    3600,
    16.0,
    48,
    20,
    ARRAY['CTD', 'Multibeam Sonar', 'ROV', 'Trawl Nets', 'Sediment Corer', 'Water Samplers'],
    '{"operator": "Canadian Coast Guard", "year_built": 1963, "last_refit": 2021}'
),
(
    'RV Oceanus',
    'RV-OCE',
    'CA',
    55.8,
    10.4,
    3.7,
    1200,
    12.5,
    12,
    15,
    ARRAY['CTD', 'Plankton Nets', 'ADCP', 'Multi-corer', 'Benthic Trawl'],
    '{"operator": "Dalhousie University", "year_built": 1995, "ice_class": "1A"}'
),
(
    'CCGS Amundsen',
    'CCGS-AMU',
    'CA',
    98.2,
    19.6,
    6.2,
    5910,
    16.5,
    40,
    65,
    ARRAY['CTD', 'Ice Radar', 'ROV', 'Icebreaker', 'Helicopter Deck', 'Wet/Dry Labs'],
    '{"operator": "Canadian Coast Guard", "ice_breaker": true, "arctic_capable": true}'
);

-- =====================================================
-- SAMPLING EVENTS
-- =====================================================

INSERT INTO sampling_events (
    event_id, project_id, vessel_id, event_name, event_type,
    start_datetime, end_datetime, location, water_depth_meters,
    weather_conditions, sea_state_beaufort, wind_speed_knots,
    wind_direction_degrees, sampling_method, equipment_used,
    chief_scientist, data_quality, comments, metadata
) VALUES
(
    'AMBS2024_HUD_001',
    (SELECT id FROM research_projects WHERE project_code = 'AMBS2024'),
    (SELECT id FROM research_vessels WHERE vessel_code = 'CCGS-HUD'),
    'Halifax Line Station 1',
    'STATION',
    '2024-08-15 08:00:00+00',
    '2024-08-15 12:30:00+00',
    ST_GeogFromText('POINT(-63.5833 44.6333)'),
    185.5,
    'Clear skies, light winds',
    2,
    8.5,
    245,
    'CTD',
    ARRAY['CTD', 'Niskin Bottles', 'Plankton Net', 'Water Samplers'],
    'Dr. Sarah Johnson',
    'VALIDATED',
    'Excellent sampling conditions, all equipment functioning normally',
    '{"station_number": 1, "transect": "Halifax_Line", "repeat_station": true}'
),
(
    'CEMP2024_OCE_005',
    (SELECT id FROM research_projects WHERE project_code = 'CEMP2024'),
    (SELECT id FROM research_vessels WHERE vessel_code = 'RV-OCE'),
    'Bay of Fundy Transect A',
    'TRANSECT',
    '2024-09-02 06:30:00+00',
    '2024-09-02 18:45:00+00',
    ST_GeogFromText('POINT(-66.0667 45.2833)'),
    95.2,
    'Partly cloudy, moderate seas',
    3,
    12.0,
    280,
    'CTD',
    ARRAY['CTD', 'ADCP', 'Multi-corer', 'eDNA Samplers'],
    'Dr. Michael Chen',
    'PROCESSED',
    'Strong tidal currents encountered, adjusted sampling timing accordingly',
    '{"tidal_phase": "flood", "current_speed_ms": 1.8, "sampling_interval_km": 2.0}'
),
(
    'DSEI2023_AMU_012',
    (SELECT id FROM research_projects WHERE project_code = 'DSEI2023'),
    (SELECT id FROM research_vessels WHERE vessel_code = 'CCGS-AMU'),
    'Labrador Deep Station',
    'STATION',
    '2024-04-20 14:00:00+00',
    '2024-04-20 22:15:00+00',
    ST_GeogFromText('POINT(-58.7500 55.4167)'),
    2850.0,
    'Overcast, rough seas',
    5,
    25.0,
    315,
    'CTD',
    ARRAY['Deep CTD', 'ROV', 'Deep Water Samplers', 'Sediment Corer'],
    'Dr. Emily Rodriguez',
    'VALIDATED',
    'Deep water sampling successful, ROV deployment completed',
    '{"max_sampling_depth": 2800, "ROV_dive_duration": 6.5, "bottom_type": "fine_sediment"}'
);

-- =====================================================
-- SAMPLING POINTS
-- =====================================================

INSERT INTO sampling_points (
    point_id, sampling_event_id, station_name, location, timestamp,
    depth_meters, bottom_depth_meters, habitat_type, substrate_type,
    sampling_protocol, sample_volume_liters, preservation_method,
    storage_temperature_celsius, data_quality, comments, metadata
) VALUES
(
    'AMBS2024_HUD_001_P01',
    (SELECT id FROM sampling_events WHERE event_id = 'AMBS2024_HUD_001'),
    'Halifax Line St1 Surface',
    ST_GeogFromText('POINT(-63.5833 44.6333)'),
    '2024-08-15 08:30:00+00',
    5.0,
    185.5,
    'pelagic',
    'soft_sediment',
    'Standard CTD Protocol v2.1',
    12.5,
    'ethanol_95',
    -80,
    'VALIDATED',
    'Surface water sample with high phytoplankton concentration',
    '{"niskin_bottle": 1, "filtration_volume": 2.5, "filter_size_um": 0.22}'
),
(
    'AMBS2024_HUD_001_P02',
    (SELECT id FROM sampling_events WHERE event_id = 'AMBS2024_HUD_001'),
    'Halifax Line St1 Thermocline',
    ST_GeogFromText('POINT(-63.5833 44.6333)'),
    '2024-08-15 09:15:00+00',
    45.0,
    185.5,
    'pelagic',
    'soft_sediment',
    'Standard CTD Protocol v2.1',
    12.5,
    'ethanol_95',
    -80,
    'VALIDATED',
    'Thermocline sample showing temperature stratification',
    '{"niskin_bottle": 3, "filtration_volume": 2.5, "chlorophyll_filter": true}'
),
(
    'CEMP2024_OCE_005_P01',
    (SELECT id FROM sampling_events WHERE event_id = 'CEMP2024_OCE_005'),
    'Fundy Transect A Point 1',
    ST_GeogFromText('POINT(-66.0667 45.2833)'),
    '2024-09-02 07:00:00+00',
    10.0,
    95.2,
    'coastal',
    'mixed_sediment',
    'eDNA Sampling Protocol v1.3',
    5.0,
    'frozen_minus80',
    -80,
    'PROCESSED',
    'High turbidity due to tidal mixing',
    '{"edna_replicate": 1, "turbidity_ntu": 15.2, "tidal_state": "flood"}'
),
(
    'DSEI2023_AMU_012_P01',
    (SELECT id FROM sampling_events WHERE event_id = 'DSEI2023_AMU_012'),
    'Labrador Deep Bottom',
    ST_GeogFromText('POINT(-58.7500 55.4167)'),
    '2024-04-20 18:30:00+00',
    2800.0,
    2850.0,
    'abyssal',
    'fine_mud',
    'Deep Water Sampling v3.0',
    50.0,
    'frozen_minus80',
    -80,
    'VALIDATED',
    'Deep water sample near seafloor, extremely low temperature',
    '{"pressure_dbar": 2850, "bottle_type": "deep_niskin", "recovery_time": 4.2}'
);

-- =====================================================
-- OCEANOGRAPHIC DATA
-- =====================================================

INSERT INTO oceanographic_data (
    measurement_id, sampling_point_id, sampling_event_id, location, timestamp,
    depth_meters, temperature_celsius, salinity_psu, ph_level,
    dissolved_oxygen_mg_per_l, turbidity_ntu, chlorophyll_a_mg_m3,
    pressure_dbar, density_kg_m3, nitrate_umol_l, phosphate_umol_l,
    instrument_type, instrument_serial, data_quality, processing_level,
    comments, metadata
) VALUES
(
    'AMBS2024_HUD_001_M001',
    (SELECT id FROM sampling_points WHERE point_id = 'AMBS2024_HUD_001_P01'),
    (SELECT id FROM sampling_events WHERE event_id = 'AMBS2024_HUD_001'),
    ST_GeogFromText('POINT(-63.5833 44.6333)'),
    '2024-08-15 08:30:00+00',
    5.0,
    18.45,
    32.85,
    8.12,
    7.85,
    2.3,
    4.2,
    5.1,
    1024.65,
    12.8,
    0.95,
    'SBE 911plus CTD',
    'SBE-0923',
    'VALIDATED',
    2,
    'Surface measurement with high biological activity',
    '{"calibration_date": "2024-07-15", "drift_correction": true, "spike_removal": true}'
),
(
    'AMBS2024_HUD_001_M002',
    (SELECT id FROM sampling_points WHERE point_id = 'AMBS2024_HUD_001_P02'),
    (SELECT id FROM sampling_events WHERE event_id = 'AMBS2024_HUD_001'),
    ST_GeogFromText('POINT(-63.5833 44.6333)'),
    '2024-08-15 09:15:00+00',
    45.0,
    12.32,
    33.42,
    8.05,
    6.23,
    0.8,
    1.1,
    46.2,
    1025.98,
    18.5,
    1.42,
    'SBE 911plus CTD',
    'SBE-0923',
    'VALIDATED',
    2,
    'Thermocline measurement showing temperature gradient',
    '{"temperature_gradient_per_m": -0.18, "mixed_layer_depth": 35.5}'
),
(
    'CEMP2024_OCE_005_M001',
    (SELECT id FROM sampling_points WHERE point_id = 'CEMP2024_OCE_005_P01'),
    (SELECT id FROM sampling_events WHERE event_id = 'CEMP2024_OCE_005'),
    ST_GeogFromText('POINT(-66.0667 45.2833)'),
    '2024-09-02 07:00:00+00',
    10.0,
    16.8,
    31.5,
    7.95,
    8.12,
    15.2,
    2.8,
    10.3,
    1023.45,
    8.9,
    0.78,
    'RBR Concerto CTD',
    'RBR-C55-204367',
    'PROCESSED',
    1,
    'High turbidity coastal water with tidal influence',
    '{"tidal_mixing": true, "suspended_sediment": "high", "water_mass": "coastal"}'
),
(
    'DSEI2023_AMU_012_M001',
    (SELECT id FROM sampling_points WHERE point_id = 'DSEI2023_AMU_012_P01'),
    (SELECT id FROM sampling_events WHERE event_id = 'DSEI2023_AMU_012'),
    ST_GeogFromText('POINT(-58.7500 55.4167)'),
    '2024-04-20 18:30:00+00',
    2800.0,
    2.15,
    34.92,
    7.88,
    5.95,
    0.1,
    0.02,
    2850.5,
    1027.85,
    28.2,
    2.15,
    'Deep SBE 911plus CTD',
    'SBE-0845',
    'VALIDATED',
    2,
    'Deep water measurement with typical abyssal characteristics',
    '{"water_mass": "Labrador_Sea_Deep_Water", "pressure_correction": true, "bottom_distance": 50.0}'
);

-- =====================================================
-- SPECIES METADATA
-- =====================================================

INSERT INTO species_metadata (
    species_id, scientific_name, common_name, authority, taxonomic_status,
    kingdom, phylum, class, order_name, family, genus, species,
    iucn_status, habitat_type, depth_range_min_m, depth_range_max_m,
    temperature_range_min_c, temperature_range_max_c, feeding_type,
    trophic_level, reference_source, data_source, confidence_level,
    metadata
) VALUES
(
    'CFIN001',
    'Calanus finmarchicus',
    'Arctic Copepod',
    '(Gunnerus, 1770)',
    'ACCEPTED',
    'Animalia',
    'Arthropoda',
    'Copepoda',
    'Calanoida',
    'Calanidae',
    'Calanus',
    'finmarchicus',
    'LC',
    'pelagic',
    0.0,
    2000.0,
    -2.0,
    15.0,
    'filter_feeder',
    2.1,
    'WoRMS - World Register of Marine Species',
    'GBIF',
    'VERY_HIGH',
    '{"worms_id": 104464, "gbif_key": 2192628, "arctic_species": true}'
),
(
    'GMOR001',
    'Gadus morhua',
    'Atlantic Cod',
    'Linnaeus, 1758',
    'ACCEPTED',
    'Animalia',
    'Chordata',
    'Actinopterygii',
    'Gadiformes',
    'Gadidae',
    'Gadus',
    'morhua',
    'VU',
    'demersal',
    10.0,
    600.0,
    2.0,
    20.0,
    'predator',
    4.2,
    'FishBase',
    'OBIS',
    'VERY_HIGH',
    '{"fishbase_id": 69, "commercial_importance": "high", "stock_status": "overfished"}'
),
(
    'EHAM001',
    'Euphausiacea hamiltoni',
    'Hamilton Krill',
    'Tattersall, 1906',
    'ACCEPTED',
    'Animalia',
    'Arthropoda',
    'Malacostraca',
    'Euphausiacea',
    'Euphausiidae',
    'Euphausia',
    'hamiltoni',
    'LC',
    'pelagic',
    50.0,
    1000.0,
    -1.0,
    12.0,
    'filter_feeder',
    2.5,
    'World Register of Marine Species',
    'OBIS',
    'HIGH',
    '{"worms_id": 110675, "vertical_migration": true, "swarming_species": true}'
),
(
    'PMON001',
    'Pseudocalanus monachus',
    'Monk Copepod',
    'Willey, 1920',
    'ACCEPTED',
    'Animalia',
    'Arthropoda',
    'Copepoda',
    'Calanoida',
    'Pseudocalanidae',
    'Pseudocalanus',
    'monachus',
    'LC',
    'pelagic',
    0.0,
    500.0,
    -2.0,
    18.0,
    'filter_feeder',
    2.0,
    'COPEPODS - The Global Copepod Database',
    'GBIF',
    'HIGH',
    '{"cold_water_species": true, "biomass_indicator": true}'
);

-- =====================================================
-- BIOLOGICAL OBSERVATIONS
-- =====================================================

INSERT INTO biological_observations (
    observation_id, sampling_point_id, species_id, observed_name,
    identification_method, identification_confidence, abundance_count,
    abundance_density_per_m3, length_mean_mm, life_stage,
    data_quality, observer_name, comments, metadata
) VALUES
(
    'AMBS2024_HUD_001_OBS001',
    (SELECT id FROM sampling_points WHERE point_id = 'AMBS2024_HUD_001_P01'),
    'CFIN001',
    'Calanus finmarchicus',
    'microscopy',
    'HIGH',
    147,
    58.8,
    3.2,
    'adult',
    'VALIDATED',
    'Dr. Lisa Thompson',
    'Abundant population with high reproductive activity',
    '{"sex_ratio_f_m": 1.3, "egg_carrying_females": 42, "developmental_stage": "C5-Adult"}'
),
(
    'AMBS2024_HUD_001_OBS002',
    (SELECT id FROM sampling_points WHERE point_id = 'AMBS2024_HUD_001_P02'),
    'PMON001',
    'Pseudocalanus monachus',
    'microscopy',
    'MEDIUM',
    89,
    35.6,
    1.8,
    'copepodite',
    'VALIDATED',
    'Dr. Lisa Thompson',
    'Mixed population with mostly copepodite stages',
    '{"developmental_stages": ["C1", "C2", "C3", "C4"], "stage_C4_percent": 45}'
),
(
    'CEMP2024_OCE_005_OBS001',
    (SELECT id FROM sampling_points WHERE point_id = 'CEMP2024_OCE_005_P01'),
    'EHAM001',
    'Euphausiacea hamiltoni',
    'net_sampling',
    'HIGH',
    23,
    4.6,
    12.5,
    'juvenile',
    'PROCESSED',
    'Dr. Robert Kim',
    'Small swarm detected in coastal waters',
    '{"swarm_behavior": true, "vertical_position": "mid_water", "stomach_fullness": "moderate"}'
);

-- =====================================================
-- DATA PROCESSING LOG
-- =====================================================

INSERT INTO data_processing_log (
    process_id, process_type, input_table, processing_algorithm,
    algorithm_version, parameters, start_time, end_time, status,
    output_records, processing_notes, created_by
) VALUES
(
    'PROC_CTD_20240815_001',
    'CTD_data_processing',
    'oceanographic_data',
    'SBE Data Processing',
    'v7.26.7',
    '{"align_ctd": true, "cell_thermal_mass": true, "loop_edit": true, "derive": ["density", "sound_velocity"]}',
    '2024-08-15 14:00:00+00',
    '2024-08-15 14:15:00+00',
    'COMPLETED',
    2,
    'Standard CTD processing pipeline completed successfully',
    'system_auto'
),
(
    'PROC_BIO_20240815_001',
    'biological_identification',
    'biological_observations',
    'Taxonomic Verification',
    'v1.2',
    '{"expert_review": true, "cross_reference": ["WoRMS", "GBIF"], "confidence_threshold": 0.8}',
    '2024-08-16 09:00:00+00',
    '2024-08-16 10:30:00+00',
    'COMPLETED',
    2,
    'Expert taxonomic verification completed, all identifications confirmed',
    'dr.l.thompson'
);

-- Refresh materialized views
SELECT refresh_all_materialized_views();

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

\echo 'Sample data inserted successfully!'
\echo 'Running verification queries...'

-- Count records in each table
\echo 'Record counts:'
SELECT 'research_projects' as table_name, COUNT(*) as record_count FROM research_projects
UNION ALL
SELECT 'research_vessels', COUNT(*) FROM research_vessels
UNION ALL
SELECT 'sampling_events', COUNT(*) FROM sampling_events
UNION ALL
SELECT 'sampling_points', COUNT(*) FROM sampling_points
UNION ALL
SELECT 'oceanographic_data', COUNT(*) FROM oceanographic_data
UNION ALL
SELECT 'species_metadata', COUNT(*) FROM species_metadata
UNION ALL
SELECT 'biological_observations', COUNT(*) FROM biological_observations
UNION ALL
SELECT 'data_processing_log', COUNT(*) FROM data_processing_log;

-- Show sampling events with location
\echo 'Sampling events summary:'
SELECT 
    event_id,
    event_name,
    ST_AsText(location) as location_wkt,
    start_datetime,
    water_depth_meters,
    sampling_method
FROM sampling_events
ORDER BY start_datetime;

-- Show oceanographic measurements summary
\echo 'Oceanographic measurements summary:'
SELECT 
    measurement_id,
    depth_meters,
    temperature_celsius,
    salinity_psu,
    ph_level,
    dissolved_oxygen_mg_per_l
FROM oceanographic_data
ORDER BY depth_meters;

-- Show species observations summary
\echo 'Biological observations summary:'
SELECT 
    bo.observation_id,
    sm.scientific_name,
    bo.abundance_count,
    bo.identification_confidence,
    sp.depth_meters
FROM biological_observations bo
JOIN species_metadata sm ON bo.species_id = sm.species_id
JOIN sampling_points sp ON bo.sampling_point_id = sp.id
ORDER BY bo.abundance_count DESC;

\echo 'PostgreSQL sample data verification complete!'
\echo 'Database is ready for testing and development.'