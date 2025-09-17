"""
Data Ingestion API Routes
Handles file uploads, data processing, and ingestion into the platform
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, List, Optional
import json
import os
from datetime import datetime
import sys
import tempfile
from werkzeug.utils import secure_filename
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from api.utils.database import PostgreSQLCursor, MongoDB
from api.utils.response import APIResponse
from scripts.schema_matcher import SchemaMatcher

data_ingestion_bp = Blueprint('data_ingestion', __name__)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.csv', '.json', '.xlsx', '.xls', '.tsv', '.txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit

def allowed_file(filename):
    """Check if file extension is allowed"""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

@data_ingestion_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload and process data files
    
    POST /api/ingestion/upload
    
    Form data:
    - file: Data file to upload
    - description: Optional file description
    - metadata: Optional JSON metadata
    - auto_process: Whether to automatically process the file (default: true)
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return APIResponse.validation_error({
                'file': ['No file uploaded']
            })
        
        file = request.files['file']
        
        if file.filename == '':
            return APIResponse.validation_error({
                'file': ['No file selected']
            })
        
        if not allowed_file(file.filename):
            return APIResponse.validation_error({
                'file': [f'File type not allowed. Supported formats: {", ".join(ALLOWED_EXTENSIONS)}']
            })
        
        # Get optional parameters
        description = request.form.get('description', '')
        metadata_str = request.form.get('metadata', '{}')
        auto_process = request.form.get('auto_process', 'true').lower() == 'true'
        
        # Parse metadata
        try:
            metadata = json.loads(metadata_str) if metadata_str else {}
        except json.JSONDecodeError:
            return APIResponse.validation_error({
                'metadata': ['Invalid JSON format for metadata']
            })
        
        # Create secure filename
        filename = secure_filename(file.filename)
        file_id = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        # Save file temporarily
        upload_dir = os.path.join(tempfile.gettempdir(), 'marine_platform_uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        temp_file_path = os.path.join(upload_dir, file_id)
        file.save(temp_file_path)
        
        # Get file info
        file_size = os.path.getsize(temp_file_path)
        
        if file_size > MAX_FILE_SIZE:
            os.remove(temp_file_path)
            return APIResponse.validation_error({
                'file': [f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB']
            })
        
        # Store file metadata in database
        file_record = {
            'file_id': file_id,
            'original_filename': file.filename,
            'description': description,
            'file_size': file_size,
            'file_path': temp_file_path,
            'upload_timestamp': datetime.utcnow(),
            'status': 'uploaded',
            'metadata': metadata,
            'processing_results': {},
            'error_log': []
        }
        
        # Save to MongoDB
        with MongoDB() as db:
            if db is None:
                os.remove(temp_file_path)
                return APIResponse.server_error("Database connection failed")
            
            db.uploaded_files.insert_one(file_record)
            
            # Auto-process if requested
            if auto_process:
                try:
                    processing_result = process_uploaded_file(file_id, temp_file_path, db)
                    file_record['processing_results'] = processing_result
                    file_record['status'] = 'processed' if processing_result.get('success') else 'failed'
                    
                    # Update record
                    db.uploaded_files.update_one(
                        {'file_id': file_id},
                        {'$set': {
                            'processing_results': processing_result,
                            'status': file_record['status'],
                            'processed_timestamp': datetime.utcnow()
                        }}
                    )
                    
                except Exception as e:
                    logger.error(f"Auto-processing failed for {file_id}: {e}")
                    db.uploaded_files.update_one(
                        {'file_id': file_id},
                        {'$set': {
                            'status': 'processing_failed',
                            'error_log': [f'Auto-processing failed: {str(e)}']
                        }}
                    )
            
            return APIResponse.success({
                'file_id': file_id,
                'original_filename': file.filename,
                'file_size': file_size,
                'status': file_record['status'],
                'upload_timestamp': file_record['upload_timestamp'].isoformat(),
                'auto_processed': auto_process,
                'processing_results': file_record.get('processing_results', {})
            }, f"File '{file.filename}' uploaded successfully")
            
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return APIResponse.server_error(f"File upload failed: {str(e)}")

def process_uploaded_file(file_id: str, file_path: str, db) -> Dict:
    """Process uploaded file using schema matcher"""
    try:
        # Initialize schema matcher
        matcher = SchemaMatcher()
        
        # Load available schemas
        schemas_config_path = os.path.join(project_root, 'config', 'schemas.yaml')
        if not os.path.exists(schemas_config_path):
            logger.warning(f"Schema config not found at {schemas_config_path}, using basic schema detection")
            # Use basic schema detection based on file content
            return detect_schema_basic(file_path, db)
        
        matcher.load_schemas(schemas_config_path)
        
        # Detect file schema
        schema_results = matcher.match_file_schema(file_path)
        
        if not schema_results:
            return {
                'success': False,
                'error': 'No matching schema found',
                'file_analyzed': True,
                'schema_matches': []
            }
        
        best_match = schema_results[0]  # Highest confidence match
        schema_name = best_match['schema']
        confidence = best_match['confidence']
        
        # Process based on schema type
        ingestion_results = []
        
        if schema_name in ['oceanographic_data', 'sampling_points']:
            result = ingest_to_postgresql(file_path, schema_name, db)
            ingestion_results.append(result)
        
        elif schema_name in ['species_data', 'edna_sequences']:
            result = ingest_to_mongodb(file_path, schema_name, db)
            ingestion_results.append(result)
        
        return {
            'success': True,
            'schema_detected': schema_name,
            'confidence': confidence,
            'ingestion_results': ingestion_results,
            'processed_timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Processing failed: {str(e)}',
            'file_analyzed': False
        }

def ingest_to_postgresql(file_path: str, schema_name: str, db) -> Dict:
    """Ingest data to PostgreSQL based on schema"""
    try:
        # Read the data file
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.json'):
            df = pd.read_json(file_path)
        else:
            return {'success': False, 'error': 'Unsupported file format for PostgreSQL ingestion'}
        
        # Connect to PostgreSQL
        with PostgreSQLCursor() as cursor:
            if cursor is None:
                return {'success': False, 'error': 'PostgreSQL connection failed'}
            
            if schema_name == 'oceanographic_data':
                return ingest_oceanographic_data(df, cursor)
            elif schema_name == 'sampling_points':
                return ingest_sampling_points(df, cursor)
            else:
                return {'success': False, 'error': f'Unknown PostgreSQL schema: {schema_name}'}
                
    except Exception as e:
        return {'success': False, 'error': f'PostgreSQL ingestion failed: {str(e)}'}

def ingest_to_mongodb(file_path: str, schema_name: str, db) -> Dict:
    """Ingest data to MongoDB based on schema"""
    try:
        # Read the data file
        if file_path.lower().endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = [data]
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
            data = df.to_dict('records')
        else:
            return {'success': False, 'error': 'Unsupported file format for MongoDB ingestion'}
        
        if schema_name == 'species_data':
            collection = db.taxonomy_data
        elif schema_name == 'edna_sequences':
            collection = db.edna_sequences
        else:
            return {'success': False, 'error': f'Unknown MongoDB schema: {schema_name}'}
        
        # Insert data
        result = collection.insert_many(data)
        
        return {
            'success': True,
            'collection': schema_name,
            'inserted_count': len(result.inserted_ids),
            'inserted_ids': [str(id) for id in result.inserted_ids[:10]]  # First 10 IDs
        }
        
    except Exception as e:
        return {'success': False, 'error': f'MongoDB ingestion failed: {str(e)}'}

def ingest_oceanographic_data(df: pd.DataFrame, cursor) -> Dict:
    """Ingest oceanographic data to PostgreSQL"""
    try:
        records_inserted = 0
        
        for _, row in df.iterrows():
            insert_query = """
                INSERT INTO oceanographic_data 
                (location, timestamp, depth_meters, temperature_celsius, salinity_psu, 
                 ph_level, dissolved_oxygen_mg_per_l, turbidity_ntu, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                row.get('location', ''),
                pd.to_datetime(row.get('timestamp', datetime.utcnow())),
                float(row.get('depth_meters', 0)),
                float(row.get('temperature_celsius', 0)),
                float(row.get('salinity_psu', 0)),
                float(row.get('ph_level', 0)),
                float(row.get('dissolved_oxygen_mg_per_l', 0)),
                float(row.get('turbidity_ntu', 0)),
                json.dumps(row.get('metadata', {}))
            ))
            records_inserted += 1
        
        cursor.connection.commit()
        
        return {
            'success': True,
            'table': 'oceanographic_data',
            'records_inserted': records_inserted
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Oceanographic data ingestion failed: {str(e)}'}

def ingest_sampling_points(df: pd.DataFrame, cursor) -> Dict:
    """Ingest sampling points data to PostgreSQL"""
    try:
        records_inserted = 0
        
        for _, row in df.iterrows():
            insert_query = """
                INSERT INTO sampling_points 
                (location, timestamp, depth_meters, metadata)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                row.get('location', ''),
                pd.to_datetime(row.get('timestamp', datetime.utcnow())),
                float(row.get('depth_meters', 0)),
                json.dumps(row.get('metadata', {}))
            ))
            records_inserted += 1
        
        cursor.connection.commit()
        
        return {
            'success': True,
            'table': 'sampling_points',
            'records_inserted': records_inserted
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Sampling points ingestion failed: {str(e)}'}

def detect_schema_basic(file_path: str, db) -> Dict:
    """Basic schema detection when config file is not available"""
    try:
        # Analyze file based on extension and content
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path, nrows=5)  # Read first 5 rows
            columns = [col.lower() for col in df.columns]
            
            # Simple heuristic-based detection
            if any('sequence' in col for col in columns) or any('dna' in col for col in columns):
                schema_name = 'edna_sequences'
            elif any('species' in col for col in columns) or any('scientific' in col for col in columns):
                schema_name = 'species_data'
            elif any('temp' in col for col in columns) or any('salinity' in col for col in columns):
                schema_name = 'oceanographic_data'
            elif any('lat' in col for col in columns) and any('lon' in col for col in columns):
                schema_name = 'sampling_points'
            else:
                schema_name = 'oceanographic_data'  # Default fallback
            
            # Process based on detected schema
            if schema_name in ['oceanographic_data', 'sampling_points']:
                result = ingest_to_postgresql(file_path, schema_name, db)
            else:
                result = ingest_to_mongodb(file_path, schema_name, db)
            
            return {
                'success': True,
                'schema_detected': schema_name,
                'confidence': 75.0,  # Basic confidence
                'ingestion_results': [result],
                'processed_timestamp': datetime.utcnow().isoformat()
            }
            
        elif file_path.lower().endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Simple JSON detection
            sample = data[0] if isinstance(data, list) and data else data
            
            if 'sequence' in str(sample).lower():
                schema_name = 'edna_sequences'
            elif 'species' in str(sample).lower():
                schema_name = 'species_data'
            else:
                schema_name = 'species_data'  # Default for JSON
            
            result = ingest_to_mongodb(file_path, schema_name, db)
            
            return {
                'success': True,
                'schema_detected': schema_name,
                'confidence': 70.0,  # Basic confidence
                'ingestion_results': [result],
                'processed_timestamp': datetime.utcnow().isoformat()
            }
        
        return {
            'success': False,
            'error': 'Unsupported file format',
            'file_analyzed': False
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Basic schema detection failed: {str(e)}',
            'file_analyzed': False
        }

@data_ingestion_bp.route('/process/<file_id>', methods=['POST'])
def process_file(file_id):
    """
    Process a previously uploaded file
    
    POST /api/ingestion/process/{file_id}
    """
    try:
        with MongoDB() as db:
            if db is None:
                return APIResponse.server_error("Database connection failed")
            
            # Find the file record
            file_record = db.uploaded_files.find_one({'file_id': file_id})
            
            if not file_record:
                return APIResponse.not_found("File")
            
            if not os.path.exists(file_record['file_path']):
                return APIResponse.error('File no longer available for processing', 404)
            
            # Process the file
            processing_result = process_uploaded_file(file_id, file_record['file_path'], db)
            
            # Update file record
            db.uploaded_files.update_one(
                {'file_id': file_id},
                {'$set': {
                    'processing_results': processing_result,
                    'status': 'processed' if processing_result.get('success') else 'processing_failed',
                    'processed_timestamp': datetime.utcnow()
                }}
            )
            
            return APIResponse.success({
                'file_id': file_id,
                'processing_results': processing_result,
                'status': 'processed' if processing_result.get('success') else 'processing_failed'
            }, f"File {file_id} processing completed")
            
    except Exception as e:
        logger.error(f"File processing error: {e}")
        return APIResponse.server_error(f"File processing failed: {str(e)}")

@data_ingestion_bp.route('/files', methods=['GET'])
def list_files():
    """
    List uploaded files with pagination and filtering
    
    GET /api/ingestion/files?page=1&per_page=20&status=processed
    """
    try:
        # Get query parameters
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
        status = request.args.get('status')  # uploaded, processed, processing_failed
        
        # Build filter query
        filter_query = {}
        if status:
            filter_query['status'] = status
        
        with MongoDB() as db:
            if db is None:
                return APIResponse.server_error("Database connection failed")
            
            # Get total count
            total = db.uploaded_files.count_documents(filter_query)
            
            # Calculate skip
            skip = (page - 1) * per_page
            
            # Get files with pagination
            cursor = db.uploaded_files.find(filter_query).sort('upload_timestamp', -1).skip(skip).limit(per_page)
            
            files_list = []
            for doc in cursor:
                file_info = {
                    'file_id': doc.get('file_id'),
                    'original_filename': doc.get('original_filename'),
                    'description': doc.get('description'),
                    'file_size': doc.get('file_size'),
                    'status': doc.get('status'),
                    'upload_timestamp': doc.get('upload_timestamp').isoformat() if hasattr(doc.get('upload_timestamp'), 'isoformat') else doc.get('upload_timestamp'),
                    'processed_timestamp': doc.get('processed_timestamp').isoformat() if hasattr(doc.get('processed_timestamp'), 'isoformat') else doc.get('processed_timestamp'),
                    'metadata': doc.get('metadata', {}),
                    'processing_summary': {
                        'success': doc.get('processing_results', {}).get('success', False),
                        'schema_detected': doc.get('processing_results', {}).get('schema_detected'),
                        'confidence': doc.get('processing_results', {}).get('confidence')
                    }
                }
                files_list.append(file_info)
            
            return APIResponse.paginated(
                data=files_list,
                page=page,
                per_page=per_page,
                total=total,
                message=f"Retrieved {len(files_list)} uploaded files"
            )
            
    except Exception as e:
        logger.error(f"File listing error: {e}")
        return APIResponse.server_error(f"Failed to retrieve files: {str(e)}")

@data_ingestion_bp.route('/files/<file_id>', methods=['GET'])
def get_file_details(file_id):
    """
    Get detailed information about a specific uploaded file
    
    GET /api/ingestion/files/{file_id}
    """
    try:
        with MongoDB() as db:
            if db is None:
                return APIResponse.server_error("Database connection failed")
            
            file_record = db.uploaded_files.find_one({'file_id': file_id})
            
            if not file_record:
                return APIResponse.not_found("File")
            
            file_details = {
                'file_id': file_record.get('file_id'),
                'original_filename': file_record.get('original_filename'),
                'description': file_record.get('description'),
                'file_size': file_record.get('file_size'),
                'status': file_record.get('status'),
                'upload_timestamp': file_record.get('upload_timestamp').isoformat() if hasattr(file_record.get('upload_timestamp'), 'isoformat') else file_record.get('upload_timestamp'),
                'processed_timestamp': file_record.get('processed_timestamp').isoformat() if hasattr(file_record.get('processed_timestamp'), 'isoformat') else file_record.get('processed_timestamp'),
                'metadata': file_record.get('metadata', {}),
                'processing_results': file_record.get('processing_results', {}),
                'error_log': file_record.get('error_log', []),
                'file_exists': os.path.exists(file_record.get('file_path', ''))
            }
            
            return APIResponse.success(
                file_details,
                f"Retrieved details for file {file_id}"
            )
            
    except Exception as e:
        logger.error(f"File details error: {e}")
        return APIResponse.server_error(f"Failed to retrieve file details: {str(e)}")

@data_ingestion_bp.route('/process-uploads', methods=['POST'])
def process_uploaded_files():
    """
    Process uploaded files using enhanced schema matching
    
    POST /api/ingestion/process-uploads
    
    Request body:
    {
        "status_filter": "uploaded",  // Optional: filter by file status
        "upload_type_filter": "edna", // Optional: filter by upload type
        "process_matches": true        // Whether to actually process the files
    }
    """
    try:
        data = request.get_json() or {}
        
        status_filter = data.get('status_filter')
        upload_type_filter = data.get('upload_type_filter')
        process_matches = data.get('process_matches', True)
        
        # Initialize the enhanced schema matcher
        from scripts.schema_matcher import SchemaMatchingOrchestrator
        
        config = {
            'similarity_threshold': 0.6,
            'log_level': 'INFO',
            'console_logging': True
        }
        
        matcher = SchemaMatchingOrchestrator(config)
        
        # Run matching on uploaded files
        results = matcher.run_matching_on_uploads(
            status_filter=status_filter,
            upload_type_filter=upload_type_filter,
            process_matches=process_matches
        )
        
        if 'error' in results:
            return APIResponse.server_error(f"Processing failed: {results['error']}")
        
        # Summarize results
        total_files = results['files_analyzed']
        total_processed = len([r for r in results.get('processing_results', []) if r.get('success')])
        total_failed = len([r for r in results.get('processing_results', []) if not r.get('success')])
        
        response_data = {
            'summary': {
                'total_files_analyzed': total_files,
                'files_processed_successfully': total_processed,
                'files_failed_processing': total_failed,
                'schemas_available': results['schemas_found']
            },
            'detailed_results': results,
            'processing_timestamp': results['timestamp']
        }
        
        return APIResponse.success(
            response_data,
            f"Processed {total_files} uploaded files. {total_processed} successful, {total_failed} failed."
        )
        
    except Exception as e:
        logger.error(f"Upload processing error: {e}")
        return APIResponse.server_error(f"Failed to process uploads: {str(e)}")

@data_ingestion_bp.route('/reprocess/<file_id>', methods=['POST'])
def reprocess_single_file(file_id):
    """
    Reprocess a specific uploaded file
    
    POST /api/ingestion/reprocess/{file_id}
    """
    try:
        with MongoDB() as db:
            if db is None:
                return APIResponse.server_error("Database connection failed")
            
            # Check if file exists
            file_record = db.uploaded_files.find_one({'file_id': file_id})
            if not file_record:
                return APIResponse.not_found("File")
            
            # Initialize schema matcher
            from scripts.schema_matcher import SchemaMatchingOrchestrator
            
            config = {
                'similarity_threshold': 0.6,
                'log_level': 'INFO',
                'console_logging': True
            }
            
            matcher = SchemaMatchingOrchestrator(config)
            
            # Process just this one file
            results = matcher.run_matching_on_uploads(
                status_filter=None,
                upload_type_filter=None,
                process_matches=True
            )
            
            # Filter results for this specific file
            if file_id in results.get('matches', {}):
                file_result = next((r for r in results.get('processing_results', []) if r.get('file_id') == file_id), None)
                
                if file_result:
                    return APIResponse.success(
                        file_result,
                        f"File {file_id} reprocessed successfully"
                    )
                else:
                    return APIResponse.error("File processing failed", 500)
            else:
                return APIResponse.error("File not found in processing results", 404)
                
    except Exception as e:
        logger.error(f"File reprocessing error: {e}")
        return APIResponse.server_error(f"Failed to reprocess file: {str(e)}")

@data_ingestion_bp.route('/schemas', methods=['GET'])
def get_supported_schemas():
    """
    Get information about supported data schemas
    
    GET /api/ingestion/schemas
    """
    try:
        schemas = {
            'oceanographic_data': {
                'target_database': 'postgresql',
                'table': 'oceanographic_data',
                'required_fields': ['location', 'timestamp', 'depth_meters'],
                'optional_fields': ['temperature_celsius', 'salinity_psu', 'ph_level', 
                                  'dissolved_oxygen_mg_per_l', 'turbidity_ntu', 'metadata'],
                'description': 'Physical and chemical oceanographic measurements'
            },
            'sampling_points': {
                'target_database': 'postgresql',
                'table': 'sampling_points',
                'required_fields': ['location', 'timestamp'],
                'optional_fields': ['depth_meters', 'metadata'],
                'description': 'Geographical sampling point locations'
            },
            'species_data': {
                'target_database': 'mongodb',
                'collection': 'taxonomy_data',
                'required_fields': ['species_id', 'species'],
                'optional_fields': ['common_name', 'kingdom', 'phylum', 'class', 
                                  'order', 'family', 'genus', 'description'],
                'description': 'Species taxonomy and classification data'
            },
            'edna_sequences': {
                'target_database': 'mongodb',
                'collection': 'edna_sequences',
                'required_fields': ['sequence_id', 'sequence'],
                'optional_fields': ['matched_species_id', 'matching_score', 'confidence_level',
                                  'sample_location', 'sequencing_method'],
                'description': 'Environmental DNA sequences and analysis results'
            }
        }
        
        return APIResponse.success(
            schemas,
            "Retrieved supported data schemas"
        )
        
    except Exception as e:
        logger.error(f"Schema retrieval error: {e}")
        return APIResponse.server_error(f"Failed to retrieve schemas: {str(e)}")