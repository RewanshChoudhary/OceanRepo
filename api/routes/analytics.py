"""
Analytics API Routes
Provides cross-domain analysis and insights
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from api.utils.database import PostgreSQLCursor, MongoDB
from api.utils.response import APIResponse

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)

@analytics_bp.route('/cross-domain', methods=['POST'])
def cross_domain_analysis():
    """Perform cross-domain data analysis
    
    Request body:
    {
        "analysis_type": "correlation" | "comparison" | "temporal" | "spatial_temporal",
        "parameters": ["temperature_celsius", "salinity_psu", "ph_level"],
        "filters": {
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
            "location": {"lat": 45.0, "lon": -64.0, "radius_km": 100},
            "depth_range": {"min": 0, "max": 200},
            "projects": ["AMBS2024"]
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return APIResponse.validation_error({'request': ['Request body is required']})
        
        analysis_type = data.get('analysis_type', 'correlation')
        parameters = data.get('parameters', ['temperature_celsius', 'salinity_psu'])
        filters = data.get('filters', {})
        
        if analysis_type not in ['correlation', 'comparison', 'temporal', 'spatial_temporal']:
            return APIResponse.validation_error({
                'analysis_type': ['Invalid analysis type. Must be one of: correlation, comparison, temporal, spatial_temporal']
            })
        
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            if analysis_type == 'correlation':
                return _perform_correlation_analysis(cursor, parameters, filters)
            elif analysis_type == 'comparison':
                return _perform_comparison_analysis(cursor, parameters, filters)
            elif analysis_type == 'temporal':
                return _perform_temporal_analysis(cursor, parameters, filters)
            elif analysis_type == 'spatial_temporal':
                return _perform_spatial_temporal_analysis(cursor, parameters, filters)
                
    except Exception as e:
        logger.error(f"Cross-domain analysis error: {e}")
        return APIResponse.server_error(f"Cross-domain analysis failed: {str(e)}")

def _build_filter_conditions(filters):
    """Build SQL WHERE conditions from filters"""
    where_conditions = []
    params = []
    
    # Date range filter
    date_range = filters.get('date_range', {})
    if date_range.get('start'):
        where_conditions.append('od.timestamp >= %s')
        params.append(date_range['start'])
    if date_range.get('end'):
        where_conditions.append('od.timestamp <= %s')
        params.append(date_range['end'] + ' 23:59:59')
    
    # Location filter
    location = filters.get('location', {})
    if location.get('lat') and location.get('lon') and location.get('radius_km'):
        where_conditions.append(
            'ST_DWithin(od.location::geography, ST_MakePoint(%s, %s)::geography, %s)'
        )
        params.extend([location['lon'], location['lat'], location['radius_km'] * 1000])
    
    # Depth range filter
    depth_range = filters.get('depth_range', {})
    if depth_range.get('min') is not None:
        where_conditions.append('od.depth_meters >= %s')
        params.append(depth_range['min'])
    if depth_range.get('max') is not None:
        where_conditions.append('od.depth_meters <= %s')
        params.append(depth_range['max'])
    
    # Project filter
    projects = filters.get('projects', [])
    if projects:
        placeholders = ', '.join(['%s'] * len(projects))
        where_conditions.append(f'rp.project_code IN ({placeholders})')
        params.extend(projects)
    
    return where_conditions, params

def _perform_correlation_analysis(cursor, parameters, filters):
    """Perform correlation analysis between oceanographic parameters"""
    where_conditions, params = _build_filter_conditions(filters)
    where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
    
    # Build parameter selection with null checks
    valid_params = [p for p in parameters if p in [
        'temperature_celsius', 'salinity_psu', 'ph_level', 'dissolved_oxygen_mg_per_l',
        'turbidity_ntu', 'chlorophyll_a_mg_m3', 'nitrate_umol_l', 'phosphate_umol_l'
    ]]
    
    if len(valid_params) < 2:
        return APIResponse.validation_error({
            'parameters': ['At least 2 valid parameters required for correlation analysis']
        })
    
    # Get data for correlation calculation
    param_columns = ', '.join([f'od.{param}' for param in valid_params])
    query = f"""
        SELECT {param_columns}
        FROM oceanographic_data od
        LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
        LEFT JOIN research_projects rp ON se.project_id = rp.id
        {where_clause}
        AND {' IS NOT NULL AND '.join([f'od.{param}' for param in valid_params])} IS NOT NULL
        LIMIT 1000
    """
    
    cursor.execute(query, params)
    data_rows = cursor.fetchall()
    
    if len(data_rows) < 10:
        return APIResponse.validation_error({
            'data': ['Insufficient data points for correlation analysis (minimum 10 required)']
        })
    
    # Calculate correlations between all parameter pairs
    correlations = []
    for i, param1 in enumerate(valid_params):
        for j, param2 in enumerate(valid_params):
            if i < j:  # Avoid duplicates
                values1 = [float(row[param1]) for row in data_rows if row[param1] is not None]
                values2 = [float(row[param2]) for row in data_rows if row[param2] is not None]
                
                if len(values1) >= 10 and len(values2) >= 10:
                    # Simple Pearson correlation coefficient calculation
                    n = min(len(values1), len(values2))
                    values1, values2 = values1[:n], values2[:n]
                    
                    mean1, mean2 = sum(values1) / n, sum(values2) / n
                    
                    numerator = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(values1, values2))
                    denom1 = sum((v1 - mean1) ** 2 for v1 in values1) ** 0.5
                    denom2 = sum((v2 - mean2) ** 2 for v2 in values2) ** 0.5
                    
                    correlation = numerator / (denom1 * denom2) if denom1 > 0 and denom2 > 0 else 0
                    
                    correlations.append({
                        'parameter_1': param1,
                        'parameter_2': param2,
                        'correlation_coefficient': round(correlation, 4),
                        'strength': _classify_correlation_strength(abs(correlation)),
                        'data_points': n
                    })
    
    # Sort by absolute correlation strength
    correlations.sort(key=lambda x: abs(x['correlation_coefficient']), reverse=True)
    
    return APIResponse.success({
        'analysis_type': 'correlation',
        'parameters_analyzed': valid_params,
        'total_data_points': len(data_rows),
        'correlations': correlations,
        'filters_applied': filters,
        'generated_at': datetime.utcnow().isoformat()
    }, f"Calculated {len(correlations)} parameter correlations")

def _classify_correlation_strength(abs_corr):
    """Classify correlation strength based on absolute value"""
    if abs_corr >= 0.8:
        return 'very_strong'
    elif abs_corr >= 0.6:
        return 'strong'
    elif abs_corr >= 0.4:
        return 'moderate'
    elif abs_corr >= 0.2:
        return 'weak'
    else:
        return 'very_weak'

def _perform_comparison_analysis(cursor, parameters, filters):
    """Compare parameter values across different conditions"""
    where_conditions, params = _build_filter_conditions(filters)
    where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
    
    # Compare by depth ranges
    depth_comparison_query = f"""
        SELECT 
            CASE 
                WHEN depth_meters < 50 THEN 'Shallow (0-50m)'
                WHEN depth_meters < 200 THEN 'Medium (50-200m)'
                ELSE 'Deep (200m+)'
            END as depth_category,
            COUNT(*) as sample_count,
            AVG(temperature_celsius) as avg_temperature,
            AVG(salinity_psu) as avg_salinity,
            AVG(ph_level) as avg_ph,
            AVG(dissolved_oxygen_mg_per_l) as avg_oxygen,
            STDDEV(temperature_celsius) as std_temperature,
            STDDEV(salinity_psu) as std_salinity
        FROM oceanographic_data od
        LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
        LEFT JOIN research_projects rp ON se.project_id = rp.id
        {where_clause}
        AND depth_meters IS NOT NULL
        GROUP BY depth_category
        ORDER BY MIN(depth_meters)
    """
    
    cursor.execute(depth_comparison_query, params)
    depth_comparison = cursor.fetchall()
    
    # Compare by seasons (if date filter allows)
    seasonal_query = f"""
        SELECT 
            CASE 
                WHEN EXTRACT(MONTH FROM timestamp) IN (12, 1, 2) THEN 'Winter'
                WHEN EXTRACT(MONTH FROM timestamp) IN (3, 4, 5) THEN 'Spring'
                WHEN EXTRACT(MONTH FROM timestamp) IN (6, 7, 8) THEN 'Summer'
                ELSE 'Fall'
            END as season,
            COUNT(*) as sample_count,
            AVG(temperature_celsius) as avg_temperature,
            AVG(salinity_psu) as avg_salinity,
            AVG(ph_level) as avg_ph,
            AVG(dissolved_oxygen_mg_per_l) as avg_oxygen
        FROM oceanographic_data od
        LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
        LEFT JOIN research_projects rp ON se.project_id = rp.id
        {where_clause}
        GROUP BY season
        ORDER BY 
            CASE season
                WHEN 'Winter' THEN 1
                WHEN 'Spring' THEN 2
                WHEN 'Summer' THEN 3
                ELSE 4
            END
    """
    
    cursor.execute(seasonal_query, params)
    seasonal_comparison = cursor.fetchall()
    
    # Format results
    formatted_depth = []
    for row in depth_comparison:
        formatted_depth.append({
            'category': row['depth_category'],
            'sample_count': row['sample_count'],
            'averages': {
                'temperature_celsius': round(float(row['avg_temperature']), 2) if row['avg_temperature'] else None,
                'salinity_psu': round(float(row['avg_salinity']), 2) if row['avg_salinity'] else None,
                'ph_level': round(float(row['avg_ph']), 2) if row['avg_ph'] else None,
                'dissolved_oxygen_mg_per_l': round(float(row['avg_oxygen']), 2) if row['avg_oxygen'] else None
            },
            'standard_deviations': {
                'temperature_celsius': round(float(row['std_temperature']), 2) if row['std_temperature'] else None,
                'salinity_psu': round(float(row['std_salinity']), 2) if row['std_salinity'] else None
            }
        })
    
    formatted_seasonal = []
    for row in seasonal_comparison:
        formatted_seasonal.append({
            'season': row['season'],
            'sample_count': row['sample_count'],
            'averages': {
                'temperature_celsius': round(float(row['avg_temperature']), 2) if row['avg_temperature'] else None,
                'salinity_psu': round(float(row['avg_salinity']), 2) if row['avg_salinity'] else None,
                'ph_level': round(float(row['avg_ph']), 2) if row['avg_ph'] else None,
                'dissolved_oxygen_mg_per_l': round(float(row['avg_oxygen']), 2) if row['avg_oxygen'] else None
            }
        })
    
    return APIResponse.success({
        'analysis_type': 'comparison',
        'parameters_analyzed': parameters,
        'comparisons': {
            'by_depth': formatted_depth,
            'by_season': formatted_seasonal
        },
        'filters_applied': filters,
        'generated_at': datetime.utcnow().isoformat()
    }, "Generated comparative analysis across depth zones and seasons")

def _perform_temporal_analysis(cursor, parameters, filters):
    """Analyze temporal trends in oceanographic parameters"""
    where_conditions, params = _build_filter_conditions(filters)
    where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
    
    # Monthly trends
    monthly_query = f"""
        SELECT 
            DATE_TRUNC('month', timestamp) as month,
            COUNT(*) as sample_count,
            AVG(temperature_celsius) as avg_temperature,
            AVG(salinity_psu) as avg_salinity,
            AVG(ph_level) as avg_ph,
            AVG(dissolved_oxygen_mg_per_l) as avg_oxygen,
            AVG(chlorophyll_a_mg_m3) as avg_chlorophyll
        FROM oceanographic_data od
        LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
        LEFT JOIN research_projects rp ON se.project_id = rp.id
        {where_clause}
        GROUP BY DATE_TRUNC('month', timestamp)
        ORDER BY month
    """
    
    cursor.execute(monthly_query, params)
    monthly_trends = cursor.fetchall()
    
    # Daily patterns (hour of day analysis)
    daily_pattern_query = f"""
        SELECT 
            EXTRACT(HOUR FROM timestamp) as hour_of_day,
            COUNT(*) as sample_count,
            AVG(temperature_celsius) as avg_temperature,
            AVG(salinity_psu) as avg_salinity,
            AVG(ph_level) as avg_ph
        FROM oceanographic_data od
        LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
        LEFT JOIN research_projects rp ON se.project_id = rp.id
        {where_clause}
        GROUP BY EXTRACT(HOUR FROM timestamp)
        ORDER BY hour_of_day
    """
    
    cursor.execute(daily_pattern_query, params)
    daily_patterns = cursor.fetchall()
    
    # Format results
    formatted_monthly = []
    for row in monthly_trends:
        formatted_monthly.append({
            'month': row['month'].isoformat() if row['month'] else None,
            'sample_count': row['sample_count'],
            'parameters': {
                'temperature_celsius': round(float(row['avg_temperature']), 2) if row['avg_temperature'] else None,
                'salinity_psu': round(float(row['avg_salinity']), 2) if row['avg_salinity'] else None,
                'ph_level': round(float(row['avg_ph']), 2) if row['avg_ph'] else None,
                'dissolved_oxygen_mg_per_l': round(float(row['avg_oxygen']), 2) if row['avg_oxygen'] else None,
                'chlorophyll_a_mg_m3': round(float(row['avg_chlorophyll']), 2) if row['avg_chlorophyll'] else None
            }
        })
    
    formatted_daily = []
    for row in daily_patterns:
        formatted_daily.append({
            'hour': int(row['hour_of_day']) if row['hour_of_day'] is not None else None,
            'sample_count': row['sample_count'],
            'parameters': {
                'temperature_celsius': round(float(row['avg_temperature']), 2) if row['avg_temperature'] else None,
                'salinity_psu': round(float(row['avg_salinity']), 2) if row['avg_salinity'] else None,
                'ph_level': round(float(row['avg_ph']), 2) if row['avg_ph'] else None
            }
        })
    
    return APIResponse.success({
        'analysis_type': 'temporal',
        'parameters_analyzed': parameters,
        'trends': {
            'monthly': formatted_monthly,
            'daily_patterns': formatted_daily
        },
        'filters_applied': filters,
        'generated_at': datetime.utcnow().isoformat()
    }, f"Analyzed temporal trends across {len(formatted_monthly)} months")

def _perform_spatial_temporal_analysis(cursor, parameters, filters):
    """Combine spatial and temporal analysis"""
    where_conditions, params = _build_filter_conditions(filters)
    where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
    
    # Spatial-temporal grid analysis
    query = f"""
        SELECT 
            DATE_TRUNC('month', timestamp) as month,
            ROUND(ST_Y(location::geometry) / 0.5) * 0.5 as lat_grid,
            ROUND(ST_X(location::geometry) / 0.5) * 0.5 as lon_grid,
            COUNT(*) as sample_count,
            AVG(temperature_celsius) as avg_temperature,
            AVG(salinity_psu) as avg_salinity,
            AVG(ph_level) as avg_ph
        FROM oceanographic_data od
        LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
        LEFT JOIN research_projects rp ON se.project_id = rp.id
        {where_clause}
        GROUP BY month, lat_grid, lon_grid
        HAVING COUNT(*) >= 3
        ORDER BY month, lat_grid, lon_grid
        LIMIT 200
    """
    
    cursor.execute(query, params)
    spatiotemporal_data = cursor.fetchall()
    
    # Format results
    formatted_data = []
    for row in spatiotemporal_data:
        formatted_data.append({
            'month': row['month'].isoformat() if row['month'] else None,
            'location_grid': {
                'latitude': float(row['lat_grid']) if row['lat_grid'] else None,
                'longitude': float(row['lon_grid']) if row['lon_grid'] else None
            },
            'sample_count': row['sample_count'],
            'parameters': {
                'temperature_celsius': round(float(row['avg_temperature']), 2) if row['avg_temperature'] else None,
                'salinity_psu': round(float(row['avg_salinity']), 2) if row['avg_salinity'] else None,
                'ph_level': round(float(row['avg_ph']), 2) if row['avg_ph'] else None
            }
        })
    
    return APIResponse.success({
        'analysis_type': 'spatial_temporal',
        'parameters_analyzed': parameters,
        'grid_resolution': '0.5 degrees',
        'data': formatted_data,
        'filters_applied': filters,
        'generated_at': datetime.utcnow().isoformat()
    }, f"Generated spatial-temporal analysis with {len(formatted_data)} grid cells")

@analytics_bp.route('/trends', methods=['GET'])
def get_trends():
    """Get data trends and patterns
    
    Query parameters:
    - parameter: Oceanographic parameter to analyze
    - time_period: Time period (7d, 30d, 90d, 1y, all)
    - project_code: Filter by specific project
    - depth_range: Depth filter (shallow, medium, deep)
    """
    try:
        parameter = request.args.get('parameter', 'temperature_celsius')
        time_period = request.args.get('time_period', '90d')
        project_code = request.args.get('project_code')
        depth_range = request.args.get('depth_range')
        
        # Validate parameter
        valid_parameters = [
            'temperature_celsius', 'salinity_psu', 'ph_level', 'dissolved_oxygen_mg_per_l',
            'turbidity_ntu', 'chlorophyll_a_mg_m3', 'nitrate_umol_l', 'phosphate_umol_l'
        ]
        
        if parameter not in valid_parameters:
            return APIResponse.validation_error({
                'parameter': [f'Parameter must be one of: {", ".join(valid_parameters)}']
            })
        
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            # Build filters
            where_conditions = [f'od.{parameter} IS NOT NULL']
            params = []
            
            # Time period filter
            if time_period != 'all':
                days_map = {'7d': 7, '30d': 30, '90d': 90, '1y': 365}
                days = days_map.get(time_period, 90)
                where_conditions.append('od.timestamp >= %s')
                params.append((datetime.utcnow() - timedelta(days=days)).isoformat())
            
            # Project filter
            if project_code:
                where_conditions.append('rp.project_code = %s')
                params.append(project_code)
            
            # Depth filter
            if depth_range:
                depth_conditions = {
                    'shallow': 'od.depth_meters < 50',
                    'medium': 'od.depth_meters BETWEEN 50 AND 200',
                    'deep': 'od.depth_meters > 200'
                }
                if depth_range in depth_conditions:
                    where_conditions.append(depth_conditions[depth_range])
            
            where_clause = 'WHERE ' + ' AND '.join(where_conditions)
            
            # Time series data
            time_series_query = f"""
                SELECT 
                    DATE_TRUNC('day', timestamp) as date,
                    COUNT(*) as sample_count,
                    AVG({parameter}) as avg_value,
                    MIN({parameter}) as min_value,
                    MAX({parameter}) as max_value,
                    STDDEV({parameter}) as std_value,
                    percentile_cont(0.25) WITHIN GROUP (ORDER BY {parameter}) as q25,
                    percentile_cont(0.75) WITHIN GROUP (ORDER BY {parameter}) as q75
                FROM oceanographic_data od
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                {where_clause}
                GROUP BY DATE_TRUNC('day', timestamp)
                ORDER BY date
            """
            
            cursor.execute(time_series_query, params)
            time_series = cursor.fetchall()
            
            # Overall statistics
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_measurements,
                    AVG({parameter}) as overall_mean,
                    STDDEV({parameter}) as overall_std,
                    MIN({parameter}) as overall_min,
                    MAX({parameter}) as overall_max,
                    percentile_cont(0.5) WITHIN GROUP (ORDER BY {parameter}) as median
                FROM oceanographic_data od
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                {where_clause}
            """
            
            cursor.execute(stats_query, params)
            overall_stats = cursor.fetchone()
            
            # Calculate trend (simple linear regression)
            if len(time_series) >= 2:
                values = [float(row['avg_value']) for row in time_series if row['avg_value']]
                x_values = list(range(len(values)))
                
                if len(values) >= 2:
                    # Calculate slope
                    n = len(values)
                    x_mean = sum(x_values) / n
                    y_mean = sum(values) / n
                    
                    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
                    denominator = sum((x - x_mean) ** 2 for x in x_values)
                    
                    slope = numerator / denominator if denominator != 0 else 0
                    
                    if slope > 0.01:
                        trend_direction = 'increasing'
                    elif slope < -0.01:
                        trend_direction = 'decreasing'
                    else:
                        trend_direction = 'stable'
                else:
                    slope = 0
                    trend_direction = 'insufficient_data'
            else:
                slope = 0
                trend_direction = 'insufficient_data'
            
            # Format time series data
            formatted_time_series = []
            for row in time_series:
                formatted_time_series.append({
                    'date': row['date'].isoformat() if row['date'] else None,
                    'sample_count': row['sample_count'],
                    'statistics': {
                        'mean': round(float(row['avg_value']), 4) if row['avg_value'] else None,
                        'min': round(float(row['min_value']), 4) if row['min_value'] else None,
                        'max': round(float(row['max_value']), 4) if row['max_value'] else None,
                        'std': round(float(row['std_value']), 4) if row['std_value'] else None,
                        'quartiles': {
                            'q25': round(float(row['q25']), 4) if row['q25'] else None,
                            'q75': round(float(row['q75']), 4) if row['q75'] else None
                        }
                    }
                })
            
            return APIResponse.success({
                'parameter': parameter,
                'time_period': time_period,
                'filters': {
                    'project_code': project_code,
                    'depth_range': depth_range
                },
                'overall_statistics': {
                    'total_measurements': overall_stats['total_measurements'],
                    'mean': round(float(overall_stats['overall_mean']), 4) if overall_stats['overall_mean'] else None,
                    'std': round(float(overall_stats['overall_std']), 4) if overall_stats['overall_std'] else None,
                    'min': round(float(overall_stats['overall_min']), 4) if overall_stats['overall_min'] else None,
                    'max': round(float(overall_stats['overall_max']), 4) if overall_stats['overall_max'] else None,
                    'median': round(float(overall_stats['median']), 4) if overall_stats['median'] else None
                },
                'trend_analysis': {
                    'direction': trend_direction,
                    'slope': round(slope, 6),
                    'data_points': len(time_series)
                },
                'time_series': formatted_time_series,
                'generated_at': datetime.utcnow().isoformat()
            }, f"Analyzed trends for {parameter} over {time_period}")
            
    except Exception as e:
        logger.error(f"Trends analysis error: {e}")
        return APIResponse.server_error(f"Failed to analyze trends: {str(e)}")

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get dashboard summary data for analytics overview"""
    try:
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            # Recent activity (last 30 days)
            recent_query = """
                SELECT 
                    COUNT(*) as recent_measurements,
                    COUNT(DISTINCT od.sampling_event_id) as recent_events,
                    COUNT(DISTINCT rp.id) as active_projects
                FROM oceanographic_data od
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                WHERE od.timestamp >= %s
            """
            
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            cursor.execute(recent_query, [thirty_days_ago])
            recent_stats = cursor.fetchone()
            
            # Parameter coverage
            coverage_query = """
                SELECT 
                    COUNT(CASE WHEN temperature_celsius IS NOT NULL THEN 1 END) as temperature_count,
                    COUNT(CASE WHEN salinity_psu IS NOT NULL THEN 1 END) as salinity_count,
                    COUNT(CASE WHEN ph_level IS NOT NULL THEN 1 END) as ph_count,
                    COUNT(CASE WHEN dissolved_oxygen_mg_per_l IS NOT NULL THEN 1 END) as oxygen_count,
                    COUNT(CASE WHEN chlorophyll_a_mg_m3 IS NOT NULL THEN 1 END) as chlorophyll_count,
                    COUNT(*) as total_measurements
                FROM oceanographic_data
            """
            
            cursor.execute(coverage_query)
            coverage = cursor.fetchone()
            
            # Geographic coverage
            geo_query = """
                SELECT 
                    ST_XMin(ST_Extent(location::geometry)) as min_lon,
                    ST_YMin(ST_Extent(location::geometry)) as min_lat,
                    ST_XMax(ST_Extent(location::geometry)) as max_lon,
                    ST_YMax(ST_Extent(location::geometry)) as max_lat,
                    COUNT(DISTINCT 
                        CONCAT(
                            ROUND(ST_Y(location::geometry), 1), 
                            ',', 
                            ROUND(ST_X(location::geometry), 1)
                        )
                    ) as unique_locations
                FROM oceanographic_data
                WHERE location IS NOT NULL
            """
            
            cursor.execute(geo_query)
            geo_coverage = cursor.fetchone()
            
            dashboard_data = {
                'recent_activity': {
                    'measurements_30d': recent_stats['recent_measurements'],
                    'events_30d': recent_stats['recent_events'],
                    'active_projects': recent_stats['active_projects']
                },
                'parameter_coverage': {
                    'total_measurements': coverage['total_measurements'],
                    'parameters': {
                        'temperature': {
                            'count': coverage['temperature_count'],
                            'percentage': round((coverage['temperature_count'] / coverage['total_measurements']) * 100, 1) if coverage['total_measurements'] > 0 else 0
                        },
                        'salinity': {
                            'count': coverage['salinity_count'],
                            'percentage': round((coverage['salinity_count'] / coverage['total_measurements']) * 100, 1) if coverage['total_measurements'] > 0 else 0
                        },
                        'ph': {
                            'count': coverage['ph_count'],
                            'percentage': round((coverage['ph_count'] / coverage['total_measurements']) * 100, 1) if coverage['total_measurements'] > 0 else 0
                        },
                        'dissolved_oxygen': {
                            'count': coverage['oxygen_count'],
                            'percentage': round((coverage['oxygen_count'] / coverage['total_measurements']) * 100, 1) if coverage['total_measurements'] > 0 else 0
                        },
                        'chlorophyll_a': {
                            'count': coverage['chlorophyll_count'],
                            'percentage': round((coverage['chlorophyll_count'] / coverage['total_measurements']) * 100, 1) if coverage['total_measurements'] > 0 else 0
                        }
                    }
                },
                'geographic_coverage': {
                    'bounding_box': {
                        'west': float(geo_coverage['min_lon']) if geo_coverage['min_lon'] else None,
                        'south': float(geo_coverage['min_lat']) if geo_coverage['min_lat'] else None,
                        'east': float(geo_coverage['max_lon']) if geo_coverage['max_lon'] else None,
                        'north': float(geo_coverage['max_lat']) if geo_coverage['max_lat'] else None
                    },
                    'unique_locations': geo_coverage['unique_locations']
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return APIResponse.success(
                dashboard_data,
                "Retrieved analytics dashboard data"
            )
            
    except Exception as e:
        logger.error(f"Dashboard data error: {e}")
        return APIResponse.server_error(f"Failed to retrieve dashboard data: {str(e)}")
