"""
Oceanographic Data API Routes
Provides access to oceanographic measurements and analysis
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from api.utils.database import PostgreSQLCursor
from api.utils.response import APIResponse

oceanographic_bp = Blueprint('oceanographic', __name__)
logger = logging.getLogger(__name__)

@oceanographic_bp.route('/data', methods=['GET'])
def get_oceanographic_data():
    """Get oceanographic measurements with filtering and pagination
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - start_date: Start date filter (YYYY-MM-DD)
    - end_date: End date filter (YYYY-MM-DD)
    - min_depth: Minimum depth filter (meters)
    - max_depth: Maximum depth filter (meters)
    - location: Location filter (lat,lon,radius_km)
    - data_quality: Data quality filter (RAW, PROCESSED, VALIDATED, PUBLISHED)
    """
    try:
        # Parse query parameters
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
        
        # Date filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Depth filters
        min_depth = request.args.get('min_depth', type=float)
        max_depth = request.args.get('max_depth', type=float)
        
        # Location filter (lat,lon,radius_km)
        location = request.args.get('location')
        
        # Data quality filter
        data_quality = request.args.get('data_quality')
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if start_date:
            where_conditions.append('timestamp >= %s')
            params.append(start_date)
            
        if end_date:
            where_conditions.append('timestamp <= %s')
            params.append(end_date + ' 23:59:59')
            
        if min_depth is not None:
            where_conditions.append('depth_meters >= %s')
            params.append(min_depth)
            
        if max_depth is not None:
            where_conditions.append('depth_meters <= %s')
            params.append(max_depth)
            
        if data_quality:
            where_conditions.append('data_quality = %s')
            params.append(data_quality)
            
        # Location-based filtering using PostGIS
        if location:
            try:
                lat, lon, radius_km = map(float, location.split(','))
                where_conditions.append(
                    'ST_DWithin(location::geography, ST_MakePoint(%s, %s)::geography, %s)'
                )
                params.extend([lon, lat, radius_km * 1000])  # Convert km to meters
            except ValueError:
                return APIResponse.validation_error({
                    'location': ['Location must be in format: lat,lon,radius_km']
                })
        
        # Build full query
        where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
        
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(*) 
                FROM oceanographic_data od
                LEFT JOIN sampling_points sp ON od.sampling_point_id = sp.id
                {where_clause}
            """
            
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()['count']
            
            # Get paginated data
            offset = (page - 1) * per_page
            
            data_query = f"""
                SELECT 
                    od.id,
                    ST_Y(od.location::geometry) as latitude,
                    ST_X(od.location::geometry) as longitude,
                    od.timestamp,
                    od.measurement_depth as depth_meters,
                    od.parameter_type,
                    od.value,
                    od.unit,
                    od.quality_flag,
                    od.instrument_type,
                    od.created_at
                FROM oceanographic_data od
                LEFT JOIN sampling_points sp ON od.sampling_point_id = sp.id
                {where_clause}
                ORDER BY od.timestamp DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(data_query, params + [per_page, offset])
            measurements = cursor.fetchall()
            
            # Format results
            formatted_data = []
            for row in measurements:
                measurement = {
                    'id': str(row['id']),
                    'location': {
                        'latitude': float(row['latitude']) if row['latitude'] else None,
                        'longitude': float(row['longitude']) if row['longitude'] else None
                    },
                    'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
                    'depth_meters': float(row['depth_meters']) if row['depth_meters'] else None,
                    'parameter_type': row['parameter_type'],
                    'value': float(row['value']) if row['value'] else None,
                    'unit': row['unit'],
                    'quality_flag': row['quality_flag'],
                    'instrument_type': row['instrument_type'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                }
                formatted_data.append(measurement)
            
            return APIResponse.paginated(
                data=formatted_data,
                page=page,
                per_page=per_page,
                total=total_count,
                message=f"Retrieved {len(formatted_data)} oceanographic measurements"
            )
            
    except Exception as e:
        logger.error(f"Oceanographic data retrieval error: {e}")
        return APIResponse.server_error(f"Failed to retrieve oceanographic data: {str(e)}")

@oceanographic_bp.route('/statistics', methods=['GET'])
def get_oceanographic_statistics():
    """Get statistics about oceanographic measurements
    
    Query parameters:
    - start_date: Start date for statistics (YYYY-MM-DD)
    - end_date: End date for statistics (YYYY-MM-DD)
    - project_code: Filter by specific project
    """
    try:
        # Parse filters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        project_code = request.args.get('project_code')
        
        # Build WHERE clause for filters
        where_conditions = []
        params = []
        
        if start_date:
            where_conditions.append('od.timestamp >= %s')
            params.append(start_date)
            
        if end_date:
            where_conditions.append('od.timestamp <= %s')
            params.append(end_date + ' 23:59:59')
            
        if project_code:
            where_conditions.append('rp.project_code = %s')
            params.append(project_code)
            
        where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
        
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            # Overall statistics
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_measurements,
                    COUNT(DISTINCT od.sampling_event_id) as unique_events,
                    COUNT(DISTINCT rp.id) as unique_projects,
                    MIN(od.timestamp) as earliest_measurement,
                    MAX(od.timestamp) as latest_measurement,
                    MIN(od.depth_meters) as min_depth,
                    MAX(od.depth_meters) as max_depth,
                    AVG(od.temperature_celsius) as avg_temperature,
                    AVG(od.salinity_psu) as avg_salinity,
                    AVG(od.ph_level) as avg_ph,
                    AVG(od.dissolved_oxygen_mg_per_l) as avg_dissolved_oxygen
                FROM oceanographic_data od
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                {where_clause}
            """
            
            cursor.execute(stats_query, params)
            overall_stats = cursor.fetchone()
            
            # Data quality distribution
            quality_query = f"""
                SELECT 
                    data_quality,
                    COUNT(*) as count
                FROM oceanographic_data od
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                {where_clause}
                GROUP BY data_quality
                ORDER BY count DESC
            """
            
            cursor.execute(quality_query, params)
            quality_distribution = cursor.fetchall()
            
            # Depth distribution (bins)
            depth_query = f"""
                SELECT 
                    CASE 
                        WHEN depth_meters < 10 THEN '0-10m'
                        WHEN depth_meters < 50 THEN '10-50m'
                        WHEN depth_meters < 100 THEN '50-100m'
                        WHEN depth_meters < 500 THEN '100-500m'
                        WHEN depth_meters < 1000 THEN '500-1000m'
                        ELSE '1000m+'
                    END as depth_range,
                    COUNT(*) as count
                FROM oceanographic_data od
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                {where_clause}
                GROUP BY depth_range
                ORDER BY MIN(depth_meters)
            """
            
            cursor.execute(depth_query, params)
            depth_distribution = cursor.fetchall()
            
            # Project distribution
            project_query = f"""
                SELECT 
                    rp.project_code,
                    rp.project_name,
                    COUNT(*) as measurement_count
                FROM oceanographic_data od
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                {where_clause}
                GROUP BY rp.id, rp.project_code, rp.project_name
                ORDER BY measurement_count DESC
                LIMIT 10
            """
            
            cursor.execute(project_query, params)
            project_distribution = cursor.fetchall()
            
            # Parameter availability
            param_query = f"""
                SELECT 
                    COUNT(CASE WHEN temperature_celsius IS NOT NULL THEN 1 END) as temperature_count,
                    COUNT(CASE WHEN salinity_psu IS NOT NULL THEN 1 END) as salinity_count,
                    COUNT(CASE WHEN ph_level IS NOT NULL THEN 1 END) as ph_count,
                    COUNT(CASE WHEN dissolved_oxygen_mg_per_l IS NOT NULL THEN 1 END) as oxygen_count,
                    COUNT(CASE WHEN turbidity_ntu IS NOT NULL THEN 1 END) as turbidity_count,
                    COUNT(CASE WHEN chlorophyll_a_mg_m3 IS NOT NULL THEN 1 END) as chlorophyll_count,
                    COUNT(CASE WHEN nitrate_umol_l IS NOT NULL THEN 1 END) as nitrate_count,
                    COUNT(CASE WHEN phosphate_umol_l IS NOT NULL THEN 1 END) as phosphate_count
                FROM oceanographic_data od
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                {where_clause}
            """
            
            cursor.execute(param_query, params)
            param_availability = cursor.fetchone()
            
            # Build response
            statistics = {
                'summary': {
                    'total_measurements': overall_stats['total_measurements'],
                    'unique_sampling_events': overall_stats['unique_events'],
                    'unique_projects': overall_stats['unique_projects'],
                    'date_range': {
                        'earliest': overall_stats['earliest_measurement'].isoformat() if overall_stats['earliest_measurement'] else None,
                        'latest': overall_stats['latest_measurement'].isoformat() if overall_stats['latest_measurement'] else None
                    },
                    'depth_range': {
                        'min_meters': float(overall_stats['min_depth']) if overall_stats['min_depth'] else None,
                        'max_meters': float(overall_stats['max_depth']) if overall_stats['max_depth'] else None
                    }
                },
                'parameter_averages': {
                    'temperature_celsius': round(float(overall_stats['avg_temperature']), 2) if overall_stats['avg_temperature'] else None,
                    'salinity_psu': round(float(overall_stats['avg_salinity']), 2) if overall_stats['avg_salinity'] else None,
                    'ph_level': round(float(overall_stats['avg_ph']), 2) if overall_stats['avg_ph'] else None,
                    'dissolved_oxygen_mg_per_l': round(float(overall_stats['avg_dissolved_oxygen']), 2) if overall_stats['avg_dissolved_oxygen'] else None
                },
                'data_quality_distribution': [
                    {'quality': row['data_quality'], 'count': row['count']}
                    for row in quality_distribution
                ],
                'depth_distribution': [
                    {'depth_range': row['depth_range'], 'count': row['count']}
                    for row in depth_distribution
                ],
                'project_distribution': [
                    {
                        'project_code': row['project_code'],
                        'project_name': row['project_name'],
                        'measurement_count': row['measurement_count']
                    }
                    for row in project_distribution
                ],
                'parameter_availability': {
                    'temperature': param_availability['temperature_count'],
                    'salinity': param_availability['salinity_count'],
                    'ph': param_availability['ph_count'],
                    'dissolved_oxygen': param_availability['oxygen_count'],
                    'turbidity': param_availability['turbidity_count'],
                    'chlorophyll_a': param_availability['chlorophyll_count'],
                    'nitrate': param_availability['nitrate_count'],
                    'phosphate': param_availability['phosphate_count']
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return APIResponse.success(
                statistics,
                "Retrieved oceanographic data statistics"
            )
            
    except Exception as e:
        logger.error(f"Statistics retrieval error: {e}")
        return APIResponse.server_error(f"Failed to retrieve statistics: {str(e)}")

@oceanographic_bp.route('/data/<measurement_id>', methods=['GET'])
def get_measurement_details(measurement_id):
    """Get detailed information about a specific measurement"""
    try:
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            query = """
                SELECT 
                    od.*,
                    ST_Y(od.location::geometry) as latitude,
                    ST_X(od.location::geometry) as longitude,
                    sp.station_name,
                    sp.habitat_type,
                    sp.substrate_type,
                    sp.sampling_protocol,
                    se.event_name,
                    se.event_type,
                    se.sampling_method,
                    se.weather_conditions,
                    rp.project_name,
                    rp.project_code,
                    rp.principal_investigator,
                    rv.vessel_name,
                    rv.vessel_code
                FROM oceanographic_data od
                LEFT JOIN sampling_points sp ON od.sampling_point_id = sp.id
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                LEFT JOIN research_vessels rv ON se.vessel_id = rv.id
                WHERE od.measurement_id = %s
            """
            
            cursor.execute(query, [measurement_id])
            result = cursor.fetchone()
            
            if not result:
                return APIResponse.not_found("Measurement")
            
            # Format detailed response
            measurement_details = {
                'id': str(result['id']),
                'measurement_id': result['measurement_id'],
                'location': {
                    'latitude': float(result['latitude']) if result['latitude'] else None,
                    'longitude': float(result['longitude']) if result['longitude'] else None
                },
                'timestamp': result['timestamp'].isoformat() if result['timestamp'] else None,
                'depth_meters': float(result['depth_meters']) if result['depth_meters'] else None,
                'physical_parameters': {
                    'temperature_celsius': float(result['temperature_celsius']) if result['temperature_celsius'] else None,
                    'salinity_psu': float(result['salinity_psu']) if result['salinity_psu'] else None,
                    'pressure_dbar': float(result['pressure_dbar']) if result['pressure_dbar'] else None,
                    'density_kg_m3': float(result['density_kg_m3']) if result['density_kg_m3'] else None,
                    'sound_velocity_ms': float(result['sound_velocity_ms']) if result['sound_velocity_ms'] else None
                },
                'chemical_parameters': {
                    'ph_level': float(result['ph_level']) if result['ph_level'] else None,
                    'dissolved_oxygen_mg_per_l': float(result['dissolved_oxygen_mg_per_l']) if result['dissolved_oxygen_mg_per_l'] else None,
                    'dissolved_oxygen_percent': float(result['dissolved_oxygen_percent']) if result['dissolved_oxygen_percent'] else None,
                    'nitrate_umol_l': float(result['nitrate_umol_l']) if result['nitrate_umol_l'] else None,
                    'nitrite_umol_l': float(result['nitrite_umol_l']) if result['nitrite_umol_l'] else None,
                    'ammonia_umol_l': float(result['ammonia_umol_l']) if result['ammonia_umol_l'] else None,
                    'phosphate_umol_l': float(result['phosphate_umol_l']) if result['phosphate_umol_l'] else None,
                    'silicate_umol_l': float(result['silicate_umol_l']) if result['silicate_umol_l'] else None,
                    'total_alkalinity_umol_kg': float(result['total_alkalinity_umol_kg']) if result['total_alkalinity_umol_kg'] else None,
                    'dissolved_inorganic_carbon_umol_kg': float(result['dissolved_inorganic_carbon_umol_kg']) if result['dissolved_inorganic_carbon_umol_kg'] else None
                },
                'optical_parameters': {
                    'turbidity_ntu': float(result['turbidity_ntu']) if result['turbidity_ntu'] else None,
                    'chlorophyll_a_mg_m3': float(result['chlorophyll_a_mg_m3']) if result['chlorophyll_a_mg_m3'] else None,
                    'suspended_particulate_matter_mg_l': float(result['suspended_particulate_matter_mg_l']) if result['suspended_particulate_matter_mg_l'] else None,
                    'colored_dissolved_organic_matter_ppb': float(result['colored_dissolved_organic_matter_ppb']) if result['colored_dissolved_organic_matter_ppb'] else None
                },
                'current_data': {
                    'speed_cm_s': float(result['current_speed_cm_s']) if result['current_speed_cm_s'] else None,
                    'direction_degrees': int(result['current_direction_degrees']) if result['current_direction_degrees'] else None
                },
                'quality_control': {
                    'data_quality': result['data_quality'],
                    'processing_level': result['processing_level'],
                    'qc_flags': result['qc_flags'],
                    'measurement_uncertainty': float(result['measurement_uncertainty']) if result['measurement_uncertainty'] else None,
                    'detection_limit': float(result['detection_limit']) if result['detection_limit'] else None
                },
                'instrument': {
                    'type': result['instrument_type'],
                    'serial': result['instrument_serial'],
                    'calibration_date': result['calibration_date'].isoformat() if result['calibration_date'] else None
                },
                'sampling_context': {
                    'station_name': result['station_name'],
                    'habitat_type': result['habitat_type'],
                    'substrate_type': result['substrate_type'],
                    'sampling_protocol': result['sampling_protocol'],
                    'event_name': result['event_name'],
                    'event_type': result['event_type'],
                    'sampling_method': result['sampling_method'],
                    'weather_conditions': result['weather_conditions']
                },
                'project_info': {
                    'project_name': result['project_name'],
                    'project_code': result['project_code'],
                    'principal_investigator': result['principal_investigator'],
                    'vessel_name': result['vessel_name'],
                    'vessel_code': result['vessel_code']
                },
                'metadata': result['metadata'],
                'comments': result['comments'],
                'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                'updated_at': result['updated_at'].isoformat() if result['updated_at'] else None
            }
            
            return APIResponse.success(
                measurement_details,
                f"Retrieved details for measurement {measurement_id}"
            )
            
    except Exception as e:
        logger.error(f"Measurement details retrieval error: {e}")
        return APIResponse.server_error(f"Failed to retrieve measurement details: {str(e)}")
