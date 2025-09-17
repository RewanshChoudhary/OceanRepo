"""
Spatial Analysis API Routes
Provides geospatial analysis and visualization capabilities
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
import json
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from api.utils.database import PostgreSQLCursor
from api.utils.response import APIResponse

spatial_bp = Blueprint('spatial', __name__)
logger = logging.getLogger(__name__)

@spatial_bp.route('/analysis', methods=['POST'])
def perform_spatial_analysis():
    """Perform spatial analysis on geographic data
    
    Request body:
    {
        "analysis_type": "distance" | "density" | "cluster" | "hotspot",
        "geometry": {
            "type": "Point" | "Polygon" | "LineString",
            "coordinates": [...]
        },
        "radius_km": 50,
        "parameters": ["temperature", "salinity", "ph"]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return APIResponse.validation_error({'request': ['Request body is required']})
        
        analysis_type = data.get('analysis_type')
        geometry = data.get('geometry')
        radius_km = data.get('radius_km', 10)
        parameters = data.get('parameters', ['temperature_celsius', 'salinity_psu'])
        
        if not analysis_type:
            return APIResponse.validation_error({'analysis_type': ['Analysis type is required']})
        
        if analysis_type not in ['distance', 'density', 'cluster', 'hotspot']:
            return APIResponse.validation_error({'analysis_type': ['Invalid analysis type']})
        
        if not geometry:
            return APIResponse.validation_error({'geometry': ['Geometry is required']})
        
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            if analysis_type == 'distance':
                return _perform_distance_analysis(cursor, geometry, radius_km, parameters)
            elif analysis_type == 'density':
                return _perform_density_analysis(cursor, geometry, radius_km)
            elif analysis_type == 'cluster':
                return _perform_cluster_analysis(cursor, parameters)
            elif analysis_type == 'hotspot':
                return _perform_hotspot_analysis(cursor, parameters)
                
    except Exception as e:
        logger.error(f"Spatial analysis error: {e}")
        return APIResponse.server_error(f"Spatial analysis failed: {str(e)}")

def _perform_distance_analysis(cursor, geometry, radius_km, parameters):
    """Perform distance-based analysis"""
    # Create geometry from GeoJSON
    if geometry['type'] == 'Point':
        lon, lat = geometry['coordinates']
        geom_clause = f"ST_MakePoint({lon}, {lat})"
    else:
        return APIResponse.validation_error({'geometry': ['Only Point geometry supported for distance analysis']})
    
    # Build parameter selection - simplified for actual schema
    param_columns = 'od.parameter_type, od.value, od.unit'
    
    query = f"""
        SELECT 
            od.id,
            ST_Y(od.location::geometry) as latitude,
            ST_X(od.location::geometry) as longitude,
            ST_Distance(od.location::geography, {geom_clause}::geography) / 1000 as distance_km,
            od.measurement_depth as depth_meters,
            od.timestamp,
            od.parameter_type,
            od.value,
            od.unit,
            od.quality_flag,
            od.instrument_type
        FROM oceanographic_data od
        WHERE ST_DWithin(od.location::geography, {geom_clause}::geography, {radius_km * 1000})
        ORDER BY distance_km ASC
        LIMIT 100
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Calculate statistics
    if results:
        distances = [float(r['distance_km']) for r in results]
        avg_distance = sum(distances) / len(distances)
        min_distance = min(distances)
        max_distance = max(distances)
    else:
        avg_distance = min_distance = max_distance = 0
    
    formatted_results = []
    for row in results:
        result_data = {
            'id': str(row['id']),
            'location': {
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude'])
            },
            'distance_km': float(row['distance_km']),
            'depth_meters': float(row['depth_meters']) if row['depth_meters'] else None,
            'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
            'parameter_type': row['parameter_type'],
            'value': float(row['value']) if row['value'] else None,
            'unit': row['unit'],
            'quality_flag': row['quality_flag'],
            'instrument_type': row['instrument_type']
        }
        
        formatted_results.append(result_data)
    
    return APIResponse.success({
        'analysis_type': 'distance',
        'query_point': geometry,
        'radius_km': radius_km,
        'statistics': {
            'total_points': len(results),
            'avg_distance_km': round(avg_distance, 2),
            'min_distance_km': round(min_distance, 2),
            'max_distance_km': round(max_distance, 2)
        },
        'results': formatted_results
    }, f"Found {len(results)} measurements within {radius_km}km")

def _perform_density_analysis(cursor, geometry, radius_km):
    """Perform sampling density analysis"""
    if geometry['type'] == 'Point':
        lon, lat = geometry['coordinates']
        geom_clause = f"ST_MakePoint({lon}, {lat})"
    else:
        return APIResponse.validation_error({'geometry': ['Only Point geometry supported for density analysis']})
    
    # Create grid for density analysis
    query = f"""
        WITH grid AS (
            SELECT 
                ST_MakePoint(
                    {lon} + (x * 0.1), 
                    {lat} + (y * 0.1)
                ) as grid_point,
                x, y
            FROM generate_series(-5, 5) x,
                 generate_series(-5, 5) y
        ),
        density_points AS (
            SELECT 
                g.x, g.y,
                g.grid_point,
                COUNT(od.id) as measurement_count,
                AVG(od.temperature_celsius) as avg_temperature,
                AVG(od.salinity_psu) as avg_salinity
            FROM grid g
            LEFT JOIN oceanographic_data od ON 
                ST_DWithin(od.location::geography, g.grid_point::geography, {radius_km * 1000 / 10})
            WHERE ST_DWithin(g.grid_point::geography, {geom_clause}::geography, {radius_km * 1000})
            GROUP BY g.x, g.y, g.grid_point
        )
        SELECT 
            x, y,
            ST_Y(grid_point::geometry) as latitude,
            ST_X(grid_point::geometry) as longitude,
            measurement_count,
            avg_temperature,
            avg_salinity
        FROM density_points
        ORDER BY measurement_count DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Calculate density statistics
    densities = [r['measurement_count'] for r in results]
    max_density = max(densities) if densities else 0
    avg_density = sum(densities) / len(densities) if densities else 0
    
    formatted_results = []
    for row in results:
        formatted_results.append({
            'grid_position': {'x': row['x'], 'y': row['y']},
            'location': {
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude'])
            },
            'measurement_count': row['measurement_count'],
            'density_score': round(row['measurement_count'] / max_density, 2) if max_density > 0 else 0,
            'avg_temperature': round(float(row['avg_temperature']), 2) if row['avg_temperature'] else None,
            'avg_salinity': round(float(row['avg_salinity']), 2) if row['avg_salinity'] else None
        })
    
    return APIResponse.success({
        'analysis_type': 'density',
        'center_point': geometry,
        'radius_km': radius_km,
        'grid_size': '0.1 degrees',
        'statistics': {
            'total_grid_cells': len(results),
            'max_density': max_density,
            'avg_density': round(avg_density, 2)
        },
        'results': formatted_results
    }, f"Generated density grid with {len(results)} cells")

def _perform_cluster_analysis(cursor, parameters):
    """Perform clustering analysis on oceanographic parameters"""
    # Simple clustering using K-means approach with SQL
    param_columns = ', '.join([f'od.{param}' for param in parameters if param in [
        'temperature_celsius', 'salinity_psu', 'ph_level', 'dissolved_oxygen_mg_per_l'
    ]])
    
    if not param_columns:
        param_columns = 'od.temperature_celsius, od.salinity_psu'
    
    query = f"""
        WITH normalized_data AS (
            SELECT 
                od.measurement_id,
                ST_Y(od.location::geometry) as latitude,
                ST_X(od.location::geometry) as longitude,
                {param_columns},
                CASE 
                    WHEN od.depth_meters < 50 THEN 'shallow'
                    WHEN od.depth_meters < 200 THEN 'medium'
                    ELSE 'deep'
                END as depth_cluster
            FROM oceanographic_data od
            WHERE {param_columns.replace(', od.', ' IS NOT NULL AND od.').replace('od.', '').split(',')[0]} IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 500
        )
        SELECT 
            depth_cluster,
            COUNT(*) as point_count,
            AVG(latitude) as center_lat,
            AVG(longitude) as center_lon,
            {param_columns.replace('od.', '').replace(', ', ', AVG(').replace(param_columns.replace('od.', ''), f'AVG({param_columns.replace("od.", "")})')}
        FROM normalized_data
        GROUP BY depth_cluster
        ORDER BY point_count DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    formatted_results = []
    for row in results:
        cluster_data = {
            'cluster_id': row['depth_cluster'],
            'point_count': row['point_count'],
            'center_location': {
                'latitude': float(row['center_lat']),
                'longitude': float(row['center_lon'])
            },
            'characteristics': {}
        }
        
        # Add parameter averages
        for param in parameters:
            avg_col = f'avg_{param}'
            if avg_col in row and row[avg_col] is not None:
                cluster_data['characteristics'][param] = round(float(row[avg_col]), 2)
        
        formatted_results.append(cluster_data)
    
    return APIResponse.success({
        'analysis_type': 'cluster',
        'clustering_method': 'depth-based',
        'parameters_used': parameters,
        'total_clusters': len(results),
        'results': formatted_results
    }, f"Generated {len(results)} clusters based on depth and oceanographic parameters")

def _perform_hotspot_analysis(cursor, parameters):
    """Perform hotspot analysis to identify areas of high parameter values"""
    # Find hotspots for specific parameters
    hotspots = []
    
    for param in parameters:
        if param not in ['temperature_celsius', 'salinity_psu', 'ph_level', 'dissolved_oxygen_mg_per_l']:
            continue
            
        query = f"""
            WITH percentiles AS (
                SELECT 
                    percentile_cont(0.9) WITHIN GROUP (ORDER BY {param}) as p90_value
                FROM oceanographic_data
                WHERE {param} IS NOT NULL
            ),
            hotspot_points AS (
                SELECT 
                    od.measurement_id,
                    ST_Y(od.location::geometry) as latitude,
                    ST_X(od.location::geometry) as longitude,
                    od.{param} as value,
                    od.timestamp,
                    se.event_name,
                    rp.project_code
                FROM oceanographic_data od
                LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                LEFT JOIN research_projects rp ON se.project_id = rp.id
                CROSS JOIN percentiles p
                WHERE od.{param} >= p.p90_value
                ORDER BY od.{param} DESC
                LIMIT 20
            )
            SELECT * FROM hotspot_points
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        hotspot_data = {
            'parameter': param,
            'hotspot_count': len(results),
            'threshold': 'top 10% values',
            'locations': []
        }
        
        for row in results:
            hotspot_data['locations'].append({
                'measurement_id': row['measurement_id'],
                'location': {
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude'])
                },
                'value': float(row['value']),
                'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
                'event_name': row['event_name'],
                'project_code': row['project_code']
            })
        
        hotspots.append(hotspot_data)
    
    return APIResponse.success({
        'analysis_type': 'hotspot',
        'parameters_analyzed': parameters,
        'hotspots': hotspots
    }, f"Identified hotspots for {len(hotspots)} parameters")

@spatial_bp.route('/maps', methods=['GET'])
def get_map_data():
    """Get map data for visualization
    
    Query parameters:
    - bbox: Bounding box (west,south,east,north)
    - zoom_level: Map zoom level (1-18)
    - layer: Data layer (points, heatmap, contours)
    - parameter: Oceanographic parameter for visualization
    """
    try:
        bbox = request.args.get('bbox')  # west,south,east,north
        zoom_level = int(request.args.get('zoom_level', 10))
        layer = request.args.get('layer', 'points')
        parameter = request.args.get('parameter', 'temperature_celsius')
        
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            # Base query conditions
            where_conditions = [f'od.{parameter} IS NOT NULL']
            params = []
            
            # Bounding box filter
            if bbox:
                try:
                    west, south, east, north = map(float, bbox.split(','))
                    where_conditions.append(
                        'ST_Within(od.location::geometry, ST_MakeEnvelope(%s, %s, %s, %s, 4326))'
                    )
                    params.extend([west, south, east, north])
                except ValueError:
                    return APIResponse.validation_error({
                        'bbox': ['Bounding box must be in format: west,south,east,north']
                    })
            
            where_clause = 'WHERE ' + ' AND '.join(where_conditions)
            
            if layer == 'points':
                # Return individual data points
                query = f"""
                    SELECT 
                        od.measurement_id,
                        ST_Y(od.location::geometry) as latitude,
                        ST_X(od.location::geometry) as longitude,
                        od.{parameter} as value,
                        od.depth_meters,
                        od.timestamp,
                        se.event_name,
                        rp.project_code
                    FROM oceanographic_data od
                    LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                    LEFT JOIN research_projects rp ON se.project_id = rp.id
                    {where_clause}
                    ORDER BY od.timestamp DESC
                    LIMIT 1000
                """
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                map_data = {
                    'type': 'FeatureCollection',
                    'features': []
                }
                
                for row in results:
                    feature = {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [float(row['longitude']), float(row['latitude'])]
                        },
                        'properties': {
                            'measurement_id': row['measurement_id'],
                            'value': float(row['value']),
                            'parameter': parameter,
                            'depth_meters': float(row['depth_meters']) if row['depth_meters'] else None,
                            'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
                            'event_name': row['event_name'],
                            'project_code': row['project_code']
                        }
                    }
                    map_data['features'].append(feature)
                
            elif layer == 'heatmap':
                # Return aggregated data for heatmap visualization
                grid_size = 0.1 if zoom_level < 10 else 0.01  # Adjust grid based on zoom
                
                query = f"""
                    SELECT 
                        ROUND(ST_Y(od.location::geometry) / {grid_size}) * {grid_size} as grid_lat,
                        ROUND(ST_X(od.location::geometry) / {grid_size}) * {grid_size} as grid_lon,
                        COUNT(*) as point_count,
                        AVG(od.{parameter}) as avg_value,
                        MIN(od.{parameter}) as min_value,
                        MAX(od.{parameter}) as max_value
                    FROM oceanographic_data od
                    LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
                    LEFT JOIN research_projects rp ON se.project_id = rp.id
                    {where_clause}
                    GROUP BY grid_lat, grid_lon
                    HAVING COUNT(*) >= 3
                    ORDER BY point_count DESC
                    LIMIT 500
                """
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                map_data = {
                    'type': 'FeatureCollection',
                    'features': []
                }
                
                for row in results:
                    feature = {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': [float(row['grid_lon']), float(row['grid_lat'])]
                        },
                        'properties': {
                            'point_count': row['point_count'],
                            'avg_value': round(float(row['avg_value']), 2),
                            'min_value': round(float(row['min_value']), 2),
                            'max_value': round(float(row['max_value']), 2),
                            'parameter': parameter,
                            'intensity': min(row['point_count'] / 10.0, 1.0)  # Normalized intensity
                        }
                    }
                    map_data['features'].append(feature)
            
            # Get parameter statistics for legend
            stats_query = f"""
                SELECT 
                    COUNT(*) as total_points,
                    MIN({parameter}) as min_value,
                    MAX({parameter}) as max_value,
                    AVG({parameter}) as avg_value,
                    percentile_cont(0.25) WITHIN GROUP (ORDER BY {parameter}) as q25,
                    percentile_cont(0.75) WITHIN GROUP (ORDER BY {parameter}) as q75
                FROM oceanographic_data od
                {where_clause}
            """
            
            cursor.execute(stats_query, params)
            stats = cursor.fetchone()
            
            return APIResponse.success({
                'layer_type': layer,
                'parameter': parameter,
                'zoom_level': zoom_level,
                'bbox': bbox,
                'statistics': {
                    'total_points': stats['total_points'],
                    'min_value': round(float(stats['min_value']), 2),
                    'max_value': round(float(stats['max_value']), 2),
                    'avg_value': round(float(stats['avg_value']), 2),
                    'quartiles': {
                        'q25': round(float(stats['q25']), 2),
                        'q75': round(float(stats['q75']), 2)
                    }
                },
                'data': map_data
            }, f"Retrieved map data with {len(map_data['features'])} features")
            
    except Exception as e:
        logger.error(f"Map data retrieval error: {e}")
        return APIResponse.server_error(f"Failed to retrieve map data: {str(e)}")

@spatial_bp.route('/boundaries', methods=['GET'])
def get_spatial_boundaries():
    """Get spatial boundaries of the dataset"""
    try:
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            query = """
                SELECT 
                    ST_XMin(ST_Extent(location::geometry)) as min_longitude,
                    ST_YMin(ST_Extent(location::geometry)) as min_latitude,
                    ST_XMax(ST_Extent(location::geometry)) as max_longitude,
                    ST_YMax(ST_Extent(location::geometry)) as max_latitude,
                    COUNT(*) as total_points,
                    MIN(depth_meters) as min_depth,
                    MAX(depth_meters) as max_depth
                FROM oceanographic_data
                WHERE location IS NOT NULL
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if not result or result['total_points'] == 0:
                return APIResponse.success({
                    'boundaries': None,
                    'message': 'No spatial data found'
                })
            
            boundaries = {
                'bbox': {
                    'west': float(result['min_longitude']),
                    'south': float(result['min_latitude']),
                    'east': float(result['max_longitude']),
                    'north': float(result['max_latitude'])
                },
                'center': {
                    'latitude': (float(result['min_latitude']) + float(result['max_latitude'])) / 2,
                    'longitude': (float(result['min_longitude']) + float(result['max_longitude'])) / 2
                },
                'depth_range': {
                    'min_meters': float(result['min_depth']) if result['min_depth'] else None,
                    'max_meters': float(result['max_depth']) if result['max_depth'] else None
                },
                'total_points': result['total_points']
            }
            
            return APIResponse.success(
                boundaries,
                f"Retrieved spatial boundaries covering {result['total_points']} data points"
            )
            
    except Exception as e:
        logger.error(f"Spatial boundaries error: {e}")
        return APIResponse.server_error(f"Failed to retrieve spatial boundaries: {str(e)}")
