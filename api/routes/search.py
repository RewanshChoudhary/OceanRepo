"""
Search API Routes
Provides unified search capabilities across all data types
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

search_bp = Blueprint('search', __name__)
logger = logging.getLogger(__name__)

@search_bp.route('/', methods=['GET'])
def search_data():
    """Search across all data types
    
    Query parameters:
    - q: Search query string
    - type: Data type filter (oceanographic, species, projects, vessels)
    - location: Geographic filter (lat,lon,radius_km)
    - date_from: Start date filter (YYYY-MM-DD)
    - date_to: End date filter (YYYY-MM-DD)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    """
    try:
        query = request.args.get('q', '').strip()
        data_type = request.args.get('type', 'all')
        location = request.args.get('location')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
        
        if not query and not location and not date_from:
            return APIResponse.validation_error({
                'query': ['At least one search parameter (q, location, or date_from) is required']
            })
        
        results = {
            'query': query,
            'filters': {
                'type': data_type,
                'location': location,
                'date_range': f"{date_from} to {date_to}" if date_from or date_to else None
            },
            'results': {},
            'total_results': 0,
            'search_time': datetime.utcnow().isoformat()
        }
        
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            # Search in different data types based on filter
            if data_type in ['all', 'oceanographic']:
                ocean_results = _search_oceanographic_data(cursor, query, location, date_from, date_to, per_page)
                results['results']['oceanographic'] = ocean_results
                results['total_results'] += len(ocean_results.get('data', []))
            
            if data_type in ['all', 'projects']:
                project_results = _search_projects(cursor, query, date_from, date_to, per_page)
                results['results']['projects'] = project_results
                results['total_results'] += len(project_results.get('data', []))
            
            if data_type in ['all', 'vessels']:
                vessel_results = _search_vessels(cursor, query, per_page)
                results['results']['vessels'] = vessel_results
                results['total_results'] += len(vessel_results.get('data', []))
            
            # Search species data if MongoDB is available
            if data_type in ['all', 'species']:
                try:
                    species_results = _search_species_data(query, per_page)
                    results['results']['species'] = species_results
                    results['total_results'] += len(species_results.get('data', []))
                except Exception as e:
                    logger.warning(f"Species search failed (MongoDB unavailable?): {e}")
                    results['results']['species'] = {'data': [], 'message': 'Species database unavailable'}
        
        return APIResponse.success(
            results,
            f"Found {results['total_results']} total results"
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return APIResponse.server_error(f"Search failed: {str(e)}")

def _search_oceanographic_data(cursor, query, location, date_from, date_to, limit):
    """Search oceanographic data"""
    where_conditions = []
    params = []
    
    # Text search in comments, event names, project names
    if query:
        where_conditions.append(
            "(od.comments ILIKE %s OR se.event_name ILIKE %s OR rp.project_name ILIKE %s)"
        )
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    
    # Location-based search
    if location:
        try:
            lat, lon, radius_km = map(float, location.split(','))
            where_conditions.append(
                'ST_DWithin(od.location::geography, ST_MakePoint(%s, %s)::geography, %s)'
            )
            params.extend([lon, lat, radius_km * 1000])
        except ValueError:
            pass
    
    # Date range filter
    if date_from:
        where_conditions.append('od.timestamp >= %s')
        params.append(date_from)
    if date_to:
        where_conditions.append('od.timestamp <= %s')
        params.append(date_to + ' 23:59:59')
    
    where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
    
    search_query = f"""
        SELECT 
            od.measurement_id,
            ST_Y(od.location::geometry) as latitude,
            ST_X(od.location::geometry) as longitude,
            od.timestamp,
            od.depth_meters,
            od.temperature_celsius,
            od.salinity_psu,
            od.ph_level,
            od.dissolved_oxygen_mg_per_l,
            od.data_quality,
            od.comments,
            se.event_name,
            rp.project_name,
            rp.project_code
        FROM oceanographic_data od
        LEFT JOIN sampling_events se ON od.sampling_event_id = se.id
        LEFT JOIN research_projects rp ON se.project_id = rp.id
        {where_clause}
        ORDER BY od.timestamp DESC
        LIMIT %s
    """
    
    cursor.execute(search_query, params + [limit])
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        data.append({
            'type': 'oceanographic',
            'id': row['measurement_id'],
            'title': f"Measurement {row['measurement_id']}",
            'description': row['comments'] or 'Oceanographic measurement',
            'location': {
                'latitude': float(row['latitude']) if row['latitude'] else None,
                'longitude': float(row['longitude']) if row['longitude'] else None
            },
            'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
            'parameters': {
                'depth_meters': float(row['depth_meters']) if row['depth_meters'] else None,
                'temperature_celsius': float(row['temperature_celsius']) if row['temperature_celsius'] else None,
                'salinity_psu': float(row['salinity_psu']) if row['salinity_psu'] else None,
                'ph_level': float(row['ph_level']) if row['ph_level'] else None,
                'dissolved_oxygen_mg_per_l': float(row['dissolved_oxygen_mg_per_l']) if row['dissolved_oxygen_mg_per_l'] else None
            },
            'metadata': {
                'event_name': row['event_name'],
                'project_name': row['project_name'],
                'project_code': row['project_code'],
                'data_quality': row['data_quality']
            }
        })
    
    return {'data': data, 'count': len(data)}

def _search_projects(cursor, query, date_from, date_to, limit):
    """Search research projects"""
    where_conditions = []
    params = []
    
    if query:
        where_conditions.append(
            "(project_name ILIKE %s OR description ILIKE %s OR principal_investigator ILIKE %s)"
        )
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    
    if date_from:
        where_conditions.append('start_date >= %s')
        params.append(date_from)
    if date_to:
        where_conditions.append('end_date <= %s OR end_date IS NULL')
        params.append(date_to)
    
    where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
    
    search_query = f"""
        SELECT 
            project_code,
            project_name,
            description,
            principal_investigator,
            institution,
            start_date,
            end_date,
            budget,
            status,
            metadata
        FROM research_projects
        {where_clause}
        ORDER BY start_date DESC
        LIMIT %s
    """
    
    cursor.execute(search_query, params + [limit])
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        data.append({
            'type': 'project',
            'id': row['project_code'],
            'title': row['project_name'],
            'description': row['description'],
            'principal_investigator': row['principal_investigator'],
            'institution': row['institution'],
            'date_range': {
                'start': row['start_date'].isoformat() if row['start_date'] else None,
                'end': row['end_date'].isoformat() if row['end_date'] else None
            },
            'budget': float(row['budget']) if row['budget'] else None,
            'status': row['status'],
            'metadata': row['metadata']
        })
    
    return {'data': data, 'count': len(data)}

def _search_vessels(cursor, query, limit):
    """Search research vessels"""
    where_conditions = []
    params = []
    
    if query:
        where_conditions.append(
            "(vessel_name ILIKE %s OR vessel_code ILIKE %s)"
        )
        params.extend([f"%{query}%", f"%{query}%"])
    
    where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
    
    search_query = f"""
        SELECT 
            vessel_code,
            vessel_name,
            country_flag,
            length_meters,
            crew_capacity,
            scientific_capacity,
            equipment_capabilities,
            metadata
        FROM research_vessels
        {where_clause}
        ORDER BY vessel_name
        LIMIT %s
    """
    
    cursor.execute(search_query, params + [limit])
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        data.append({
            'type': 'vessel',
            'id': row['vessel_code'],
            'title': row['vessel_name'],
            'description': f"{row['length_meters']}m research vessel with capacity for {row['scientific_capacity']} scientists",
            'country': row['country_flag'],
            'specifications': {
                'length_meters': float(row['length_meters']) if row['length_meters'] else None,
                'crew_capacity': row['crew_capacity'],
                'scientific_capacity': row['scientific_capacity']
            },
            'equipment': row['equipment_capabilities'],
            'metadata': row['metadata']
        })
    
    return {'data': data, 'count': len(data)}

def _search_species_data(query, limit):
    """Search species data in MongoDB"""
    try:
        with MongoDB() as db:
            if db is None:
                return {'data': [], 'count': 0}
            
            # Build search filter
            search_filter = {}
            if query:
                search_filter = {
                    '$or': [
                        {'species': {'$regex': query, '$options': 'i'}},
                        {'common_name': {'$regex': query, '$options': 'i'}},
                        {'genus': {'$regex': query, '$options': 'i'}},
                        {'family': {'$regex': query, '$options': 'i'}}
                    ]
                }
            
            cursor = db.taxonomy_data.find(search_filter).limit(limit)
            
            data = []
            for doc in cursor:
                data.append({
                    'type': 'species',
                    'id': doc.get('species_id'),
                    'title': doc.get('species', 'Unknown species'),
                    'description': doc.get('description', ''),
                    'common_name': doc.get('common_name'),
                    'taxonomy': {
                        'kingdom': doc.get('kingdom'),
                        'phylum': doc.get('phylum'),
                        'class': doc.get('class'),
                        'family': doc.get('family'),
                        'genus': doc.get('genus')
                    },
                    'data_source': doc.get('data_source'),
                    'reference_link': doc.get('reference_link')
                })
            
            return {'data': data, 'count': len(data)}
            
    except Exception as e:
        logger.error(f"MongoDB species search error: {e}")
        return {'data': [], 'count': 0}

@search_bp.route('/suggestions', methods=['GET'])
def get_search_suggestions():
    """Get search suggestions based on query
    
    Query parameters:
    - q: Partial search query
    - type: Data type for suggestions
    """
    try:
        query = request.args.get('q', '').strip()
        data_type = request.args.get('type', 'all')
        
        if len(query) < 2:
            return APIResponse.validation_error({
                'q': ['Query must be at least 2 characters long']
            })
        
        suggestions = []
        
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            # Get project name suggestions
            if data_type in ['all', 'projects']:
                cursor.execute(
                    "SELECT DISTINCT project_name FROM research_projects WHERE project_name ILIKE %s LIMIT 5",
                    [f"%{query}%"]
                )
                for row in cursor.fetchall():
                    suggestions.append({
                        'text': row['project_name'],
                        'type': 'project',
                        'category': 'Research Projects'
                    })
            
            # Get vessel name suggestions
            if data_type in ['all', 'vessels']:
                cursor.execute(
                    "SELECT DISTINCT vessel_name FROM research_vessels WHERE vessel_name ILIKE %s LIMIT 5",
                    [f"%{query}%"]
                )
                for row in cursor.fetchall():
                    suggestions.append({
                        'text': row['vessel_name'],
                        'type': 'vessel',
                        'category': 'Research Vessels'
                    })
            
            # Get event name suggestions
            if data_type in ['all', 'oceanographic']:
                cursor.execute(
                    "SELECT DISTINCT event_name FROM sampling_events WHERE event_name ILIKE %s LIMIT 5",
                    [f"%{query}%"]
                )
                for row in cursor.fetchall():
                    suggestions.append({
                        'text': row['event_name'],
                        'type': 'oceanographic',
                        'category': 'Sampling Events'
                    })
        
        # Get species suggestions from MongoDB
        if data_type in ['all', 'species']:
            try:
                with MongoDB() as db:
                    if db is not None:
                        cursor = db.taxonomy_data.find({
                            '$or': [
                                {'species': {'$regex': query, '$options': 'i'}},
                                {'common_name': {'$regex': query, '$options': 'i'}}
                            ]
                        }).limit(5)
                        
                        for doc in cursor:
                            suggestions.append({
                                'text': doc.get('species', 'Unknown'),
                                'type': 'species',
                                'category': 'Species',
                                'common_name': doc.get('common_name')
                            })
            except Exception:
                pass  # MongoDB unavailable
        
        return APIResponse.success({
            'query': query,
            'suggestions': suggestions[:20],  # Limit total suggestions
            'total': len(suggestions)
        }, f"Found {len(suggestions)} suggestions")
        
    except Exception as e:
        logger.error(f"Search suggestions error: {e}")
        return APIResponse.server_error(f"Failed to get suggestions: {str(e)}")

@search_bp.route('/filters', methods=['GET'])
def get_search_filters():
    """Get available search filters and their options"""
    try:
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return APIResponse.server_error("Database connection failed")
            
            # Get available data quality options
            cursor.execute(
                "SELECT DISTINCT data_quality FROM oceanographic_data WHERE data_quality IS NOT NULL ORDER BY data_quality"
            )
            data_quality_options = [row['data_quality'] for row in cursor.fetchall()]
            
            # Get available project codes
            cursor.execute(
                "SELECT project_code, project_name FROM research_projects ORDER BY project_name LIMIT 20"
            )
            project_options = [
                {'code': row['project_code'], 'name': row['project_name']}
                for row in cursor.fetchall()
            ]
            
            # Get sampling methods
            cursor.execute(
                "SELECT DISTINCT sampling_method FROM sampling_events WHERE sampling_method IS NOT NULL ORDER BY sampling_method"
            )
            sampling_methods = [row['sampling_method'] for row in cursor.fetchall()]
            
            # Get date range of available data
            cursor.execute(
                "SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date FROM oceanographic_data"
            )
            date_range = cursor.fetchone()
            
            filters = {
                'data_types': [
                    {'id': 'all', 'name': 'All Data Types'},
                    {'id': 'oceanographic', 'name': 'Oceanographic Data'},
                    {'id': 'species', 'name': 'Species Data'},
                    {'id': 'projects', 'name': 'Research Projects'},
                    {'id': 'vessels', 'name': 'Research Vessels'}
                ],
                'data_quality': data_quality_options,
                'projects': project_options,
                'sampling_methods': sampling_methods,
                'date_range': {
                    'min': date_range['min_date'].isoformat() if date_range['min_date'] else None,
                    'max': date_range['max_date'].isoformat() if date_range['max_date'] else None
                },
                'parameters': [
                    {'id': 'temperature_celsius', 'name': 'Temperature (°C)'},
                    {'id': 'salinity_psu', 'name': 'Salinity (PSU)'},
                    {'id': 'ph_level', 'name': 'pH Level'},
                    {'id': 'dissolved_oxygen_mg_per_l', 'name': 'Dissolved Oxygen (mg/L)'},
                    {'id': 'turbidity_ntu', 'name': 'Turbidity (NTU)'},
                    {'id': 'chlorophyll_a_mg_m3', 'name': 'Chlorophyll-a (mg/m³)'}
                ]
            }
            
            return APIResponse.success(
                filters,
                "Retrieved available search filters"
            )
            
    except Exception as e:
        logger.error(f"Search filters error: {e}")
        return APIResponse.server_error(f"Failed to retrieve search filters: {str(e)}")
