#!/usr/bin/env python3
"""
Marine Data Integration Platform - Schema Matcher
Automatically scans folders for JSON and CSV files and matches their structure
with existing database tables and collections.
"""

import os
import sys
import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import re
from difflib import SequenceMatcher
from datetime import datetime
import argparse
import logging

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FileStructureAnalyzer:
    """Analyzes the structure of JSON and CSV files"""
    
    def __init__(self):
        self.supported_extensions = {'.json', '.csv'}
    
    def analyze_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze JSON file structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            structure = {
                'file_path': str(file_path),
                'file_type': 'json',
                'file_size': file_path.stat().st_size,
                'fields': {},
                'sample_data': {},
                'nested_structures': {},
                'arrays': []
            }
            
            # Analyze structure
            if isinstance(data, dict):
                structure['fields'], structure['sample_data'], structure['nested_structures'] = \
                    self._analyze_dict_structure(data)
            elif isinstance(data, list) and len(data) > 0:
                structure['arrays'].append('root')
                if isinstance(data[0], dict):
                    structure['fields'], structure['sample_data'], structure['nested_structures'] = \
                        self._analyze_dict_structure(data[0])
                    structure['array_length'] = len(data)
            
            return structure
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'file_type': 'json',
                'error': str(e)
            }
    
    def analyze_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze CSV file structure"""
        try:
            # Read a sample of the CSV to understand structure
            df = pd.read_csv(file_path, nrows=5)  # Read only first 5 rows for analysis
            
            structure = {
                'file_path': str(file_path),
                'file_type': 'csv',
                'file_size': file_path.stat().st_size,
                'fields': {},
                'sample_data': {},
                'total_rows': None,
                'columns': list(df.columns)
            }
            
            # Get column info and data types
            for col in df.columns:
                col_data = df[col].dropna()
                structure['fields'][col] = {
                    'type': str(df[col].dtype),
                    'nullable': df[col].isnull().any(),
                    'unique_values': len(col_data.unique()) if len(col_data) > 0 else 0
                }
                
                # Sample value (first non-null value)
                if len(col_data) > 0:
                    structure['sample_data'][col] = col_data.iloc[0]
            
            # Get total row count (approximately)
            try:
                full_df = pd.read_csv(file_path)
                structure['total_rows'] = len(full_df)
            except:
                structure['total_rows'] = 'unknown'
            
            return structure
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'file_type': 'csv',
                'error': str(e)
            }
    
    def _analyze_dict_structure(self, data: dict, prefix: str = '') -> Tuple[Dict, Dict, Dict]:
        """Recursively analyze dictionary structure"""
        fields = {}
        samples = {}
        nested = {}
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                nested[full_key] = 'object'
                nested_fields, nested_samples, nested_nested = \
                    self._analyze_dict_structure(value, full_key)
                fields.update(nested_fields)
                samples.update(nested_samples)
                nested.update(nested_nested)
            
            elif isinstance(value, list):
                if len(value) > 0:
                    if isinstance(value[0], dict):
                        nested[full_key] = 'array_of_objects'
                        nested_fields, nested_samples, nested_nested = \
                            self._analyze_dict_structure(value[0], full_key)
                        fields.update(nested_fields)
                        samples.update(nested_samples)
                        nested.update(nested_nested)
                    else:
                        fields[full_key] = {
                            'type': f"array_of_{type(value[0]).__name__}",
                            'array_length': len(value)
                        }
                        samples[full_key] = value[0]
                else:
                    fields[full_key] = {'type': 'empty_array'}
                    
            else:
                fields[full_key] = {
                    'type': type(value).__name__,
                    'nullable': value is None
                }
                samples[full_key] = value
        
        return fields, samples, nested

class DatabaseSchemaExtractor:
    """Extracts schema information from databases"""
    
    def __init__(self):
        self.postgres_conn = None
        self.mongo_client = None
        self.mongo_db = None
        self.logger = logging.getLogger(__name__)
    
    def connect_postgres(self) -> bool:
        """Connect to PostgreSQL database"""
        try:
            self.postgres_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DB', 'marine_db'),
                user=os.getenv('POSTGRES_USER', 'marineuser'),
                password=os.getenv('POSTGRES_PASSWORD', 'marinepass123')
            )
            return True
        except Exception as e:
            self.logger.warning(f"Could not connect to PostgreSQL: {e}")
            return False
    
    def connect_mongo(self) -> bool:
        """Connect to MongoDB database"""
        try:
            connection_string = os.getenv('MONGO_CONNECTION', 'mongodb://localhost:27017/')
            db_name = os.getenv('MONGO_DB', 'marine_db')
            
            self.mongo_client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.mongo_db = self.mongo_client[db_name]
            # Test connection
            self.mongo_client.server_info()
            return True
        except Exception as e:
            self.logger.warning(f"Could not connect to MongoDB: {e}")
            return False

class SchemaMatcher:
    """Matches file schemas with database schemas using pattern recognition and confidence scoring"""
    
    def __init__(self):
        self.schemas = {}
        self.field_mappings = {}
        self.validation_rules = {}
        self.logger = logging.getLogger(__name__)
        
    def load_schemas(self, config_path: str) -> bool:
        """Load schema definitions from YAML config file"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            self.schemas = config.get('schemas', {})
            self.field_mappings = config.get('field_mappings', {})
            self.validation_rules = config.get('validation_rules', {})
            
            self.logger.info(f"Loaded {len(self.schemas)} schema definitions from {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load schemas from {config_path}: {e}")
            return False
    
    def match_file_schema(self, file_path: str) -> List[Dict[str, Any]]:
        """Match file structure against available schemas with confidence scoring"""
        try:
            # Analyze file structure
            analyzer = FileStructureAnalyzer()
            
            if file_path.lower().endswith('.json'):
                file_structure = analyzer.analyze_json_file(Path(file_path))
            elif file_path.lower().endswith(('.csv', '.tsv')):
                file_structure = analyzer.analyze_csv_file(Path(file_path))
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
            
            if 'error' in file_structure:
                raise ValueError(f"File analysis failed: {file_structure['error']}")
            
            # Score against each schema
            schema_matches = []
            file_fields = list(file_structure.get('fields', {}).keys())
            
            if file_structure['file_type'] == 'csv':
                file_fields = file_structure.get('columns', [])
            
            for schema_name, schema_config in self.schemas.items():
                confidence = self._calculate_schema_confidence(file_fields, schema_config)
                
                if confidence >= schema_config.get('confidence_threshold', 50.0):
                    field_mappings = self._map_fields(file_fields, schema_config)
                    
                    schema_matches.append({
                        'schema': schema_name,
                        'confidence': confidence,
                        'target_database': schema_config.get('target_database'),
                        'target_table': schema_config.get('table') or schema_config.get('collection'),
                        'field_mappings': field_mappings,
                        'required_fields_found': self._check_required_fields(field_mappings, schema_config),
                        'description': schema_config.get('description', '')
                    })
            
            # Sort by confidence (highest first)
            schema_matches.sort(key=lambda x: x['confidence'], reverse=True)
            
            return schema_matches
            
        except Exception as e:
            self.logger.error(f"Schema matching failed for {file_path}: {e}")
            return []
    
    def _calculate_schema_confidence(self, file_fields: List[str], schema_config: Dict) -> float:
        """Calculate confidence score for schema match"""
        if not file_fields:
            return 0.0
        
        total_score = 0.0
        max_possible_score = 0.0
        
        required_fields = schema_config.get('required_fields', [])
        optional_fields = schema_config.get('optional_fields', [])
        all_schema_fields = required_fields + optional_fields
        field_patterns = schema_config.get('field_patterns', [])
        
        # Track which file fields have been matched to avoid double scoring
        matched_file_fields = set()
        
        # Score based on exact field matches
        for schema_field in all_schema_fields:
            weight = 2.0 if schema_field in required_fields else 1.0
            max_possible_score += weight
            
            # Find exact matches
            for file_field in file_fields:
                if file_field.lower() == schema_field.lower():
                    total_score += weight
                    matched_file_fields.add(file_field)
                    break
        
        # Score based on pattern matches for unmatched fields only
        for file_field in file_fields:
            if file_field not in matched_file_fields:
                best_pattern_score = 0.0
                
                for pattern in field_patterns:
                    pattern_score = self._match_field_pattern(file_field.lower(), pattern)
                    if pattern_score > best_pattern_score:
                        best_pattern_score = pattern_score
                
                # Give stronger weight to good pattern matches
                weight = 1.5 if best_pattern_score >= 0.8 else 0.5
                total_score += best_pattern_score * weight
                max_possible_score += weight
        
        # Calculate percentage confidence
        if max_possible_score == 0:
            return 0.0
        
        confidence = (total_score / max_possible_score) * 100
        return min(confidence, 100.0)
    
    def _match_field_pattern(self, field_name: str, pattern: str) -> float:
        """Match field name against regex pattern"""
        try:
            import re
            
            # Handle OR patterns (e.g., 'lat|latitude')
            if '|' in pattern:
                pattern_variants = [p.strip() for p in pattern.split('|')]
                best_score = 0.0
                
                for variant in pattern_variants:
                    # Check for exact match first
                    if field_name.lower() == variant.lower():
                        return 1.0
                    # Check if field contains the variant
                    elif variant.lower() in field_name.lower():
                        score = 0.8 if len(variant) > 5 else 0.6
                        best_score = max(best_score, score)
                    # Check regex match
                    elif re.search(variant.lower(), field_name.lower()):
                        score = 0.7 if len(variant) > 3 else 0.5
                        best_score = max(best_score, score)
                
                return best_score
            else:
                # Single pattern matching
                if re.search(pattern.lower(), field_name.lower()):
                    # More specific matches get higher scores
                    if field_name.lower() == pattern.lower():
                        return 1.0
                    elif len(pattern) > 5:  # Longer patterns are more specific
                        return 0.8
                    else:
                        return 0.6
                return 0.0
        except Exception:
            return 0.0
    
    def _map_fields(self, file_fields: List[str], schema_config: Dict) -> Dict[str, str]:
        """Map file fields to schema fields using patterns and mappings"""
        field_mappings = {}
        
        required_fields = schema_config.get('required_fields', [])
        optional_fields = schema_config.get('optional_fields', [])
        all_schema_fields = required_fields + optional_fields
        
        # Direct mapping first
        for file_field in file_fields:
            for schema_field in all_schema_fields:
                if file_field.lower() == schema_field.lower():
                    field_mappings[file_field] = schema_field
                    break
        
        # Pattern-based mapping for unmapped fields
        unmapped_fields = [f for f in file_fields if f not in field_mappings]
        
        for file_field in unmapped_fields:
            best_match = None
            best_score = 0.0
            
            # Check against global field mappings
            for mapping_group, mapping_sets in self.field_mappings.items():
                for mapping_set in mapping_sets:
                    if isinstance(mapping_set, list):
                        for variant in mapping_set:
                            if file_field.lower() == variant.lower():
                                # Find corresponding schema field
                                canonical_field = mapping_set[0]  # First one is canonical
                                if canonical_field in all_schema_fields:
                                    field_mappings[file_field] = canonical_field
                                    break
            
            # Pattern matching as fallback
            if file_field not in field_mappings:
                field_patterns = schema_config.get('field_patterns', [])
                for pattern in field_patterns:
                    score = self._match_field_pattern(file_field, pattern)
                    if score > best_score:
                        best_score = score
                        # Try to find corresponding schema field
                        for schema_field in all_schema_fields:
                            if self._match_field_pattern(schema_field, pattern) > 0.5:
                                best_match = schema_field
                                break
                
                if best_match and best_score > 0.6:
                    field_mappings[file_field] = best_match
        
        return field_mappings
    
    def _check_required_fields(self, field_mappings: Dict[str, str], schema_config: Dict) -> Dict[str, bool]:
        """Check which required fields are satisfied by the mapping"""
        required_fields = schema_config.get('required_fields', [])
        found_fields = {}
        
        mapped_schema_fields = set(field_mappings.values())
        
        for required_field in required_fields:
            found_fields[required_field] = required_field in mapped_schema_fields
        
        return found_fields
    
    def validate_data(self, data: Dict[str, Any], schema_name: str) -> Tuple[bool, List[str]]:
        """Validate data against schema rules"""
        if schema_name not in self.schemas:
            return False, [f"Unknown schema: {schema_name}"]
        
        errors = []
        schema_config = self.schemas[schema_name]
        
        # Check required fields
        required_fields = schema_config.get('required_fields', [])
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Required field missing: {field}")
        
        # Validate field values against rules
        for field, value in data.items():
            field_errors = self._validate_field_value(field, value, schema_name)
            errors.extend(field_errors)
        
        return len(errors) == 0, errors
    
    def _validate_field_value(self, field_name: str, value: Any, schema_name: str) -> List[str]:
        """Validate individual field value"""
        errors = []
        
        # Find validation rules for this field
        validation_rules = None
        for rule_group, rules in self.validation_rules.items():
            if field_name in rules:
                validation_rules = rules[field_name]
                break
        
        if not validation_rules:
            return errors
        
        # Check numeric ranges
        if isinstance(value, (int, float)):
            if 'min' in validation_rules and value < validation_rules['min']:
                errors.append(f"{field_name} value {value} below minimum {validation_rules['min']}")
            if 'max' in validation_rules and value > validation_rules['max']:
                errors.append(f"{field_name} value {value} above maximum {validation_rules['max']}")
        
        # Check string patterns
        if isinstance(value, str):
            if 'pattern' in validation_rules:
                import re
                if not re.match(validation_rules['pattern'], value):
                    errors.append(f"{field_name} value '{value}' doesn't match required pattern")
            
            if 'min_length' in validation_rules and len(value) < validation_rules['min_length']:
                errors.append(f"{field_name} length {len(value)} below minimum {validation_rules['min_length']}")
            
            if 'max_length' in validation_rules and len(value) > validation_rules['max_length']:
                errors.append(f"{field_name} length {len(value)} above maximum {validation_rules['max_length']}")
        
        return errors
    
    def get_postgres_tables(self) -> Dict[str, Dict]:
        """Get PostgreSQL table schemas"""
        if not self.postgres_conn:
            return {}
        
        cursor = self.postgres_conn.cursor(cursor_factory=RealDictCursor)
        tables = {}
        
        try:
            # Get all tables in the database
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            
            table_names = [row['table_name'] for row in cursor.fetchall()]
            
            for table_name in table_names:
                # Get column information
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = {}
                for col in cursor.fetchall():
                    columns[col['column_name']] = {
                        'type': col['data_type'],
                        'nullable': col['is_nullable'] == 'YES',
                        'default': col['column_default']
                    }
                
                tables[table_name] = {
                    'type': 'postgres_table',
                    'columns': columns
                }
        
        except Exception as e:
            self.logger.error(f"Error extracting PostgreSQL schema: {e}")
        
        return tables
    
    def get_mongo_collections(self) -> Dict[str, Dict]:
        """Get MongoDB collection schemas by sampling documents"""
        if self.mongo_client is None or self.mongo_db is None:
            return {}
        
        collections = {}
        
        try:
            collection_names = self.mongo_db.list_collection_names()
            
            for collection_name in collection_names:
                collection = self.mongo_db[collection_name]
                
                # Sample a few documents to understand schema
                sample_docs = list(collection.find().limit(5))
                
                if not sample_docs:
                    collections[collection_name] = {
                        'type': 'mongo_collection',
                        'fields': {},
                        'document_count': 0
                    }
                    continue
                
                # Analyze field structure from sample documents
                all_fields = set()
                field_types = defaultdict(set)
                
                for doc in sample_docs:
                    fields, _, _ = self._analyze_mongo_document(doc)
                    all_fields.update(fields.keys())
                    
                    for field, info in fields.items():
                        field_types[field].add(info['type'])
                
                schema_fields = {}
                for field in all_fields:
                    types = list(field_types[field])
                    schema_fields[field] = {
                        'type': types[0] if len(types) == 1 else f"mixed({', '.join(types)})",
                        'appears_in_all': all(field in doc for doc in sample_docs if isinstance(doc, dict))
                    }
                
                collections[collection_name] = {
                    'type': 'mongo_collection',
                    'fields': schema_fields,
                    'document_count': collection.count_documents({})
                }
        
        except Exception as e:
            self.logger.error(f"Error extracting MongoDB schema: {e}")
        
        return collections
    
    def _analyze_mongo_document(self, doc: dict, prefix: str = '') -> Tuple[Dict, Dict, Dict]:
        """Analyze a single MongoDB document structure"""
        fields = {}
        samples = {}
        nested = {}
        
        for key, value in doc.items():
            if key.startswith('_'):  # Skip MongoDB internal fields
                continue
                
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                nested_fields, nested_samples, nested_nested = \
                    self._analyze_mongo_document(value, full_key)
                fields.update(nested_fields)
                samples.update(nested_samples)
                nested.update(nested_nested)
            
            elif isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], dict):
                    nested_fields, nested_samples, nested_nested = \
                        self._analyze_mongo_document(value[0], full_key)
                    fields.update(nested_fields)
                    samples.update(nested_samples)
                    nested.update(nested_nested)
                else:
                    fields[full_key] = {
                        'type': f"array_of_{type(value[0]).__name__}" if value else "empty_array"
                    }
            else:
                fields[full_key] = {
                    'type': type(value).__name__
                }
                samples[full_key] = value
        
        return fields, samples, nested
    
    def close_connections(self):
        """Close database connections"""
        if self.postgres_conn:
            self.postgres_conn.close()
        if self.mongo_client:
            self.mongo_client.close()

class SchemaMatching:
    """Matches file structures with database schemas"""
    
    def __init__(self, similarity_threshold=0.6):
        self.similarity_threshold = similarity_threshold
    
    def calculate_field_similarity(self, field1: str, field2: str) -> float:
        """Calculate similarity between two field names"""
        # Normalize field names (remove underscores, convert to lowercase)
        norm1 = re.sub(r'[_\-\.]', '', field1.lower())
        norm2 = re.sub(r'[_\-\.]', '', field2.lower())
        
        # Use sequence matcher for similarity
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Boost for exact matches after normalization
        if norm1 == norm2:
            similarity = 1.0
        
        # Boost for substring matches
        elif norm1 in norm2 or norm2 in norm1:
            similarity = max(similarity, 0.8)
        
        return similarity
    
    def match_file_to_schema(self, file_structure: Dict, schemas: Dict[str, Dict]) -> List[Dict]:
        """Match a file structure to database schemas"""
        matches = []
        
        file_fields = set(file_structure.get('fields', {}).keys())
        if file_structure['file_type'] == 'csv':
            file_fields = set(file_structure.get('columns', []))
        
        for schema_name, schema_info in schemas.items():
            schema_fields = set(schema_info.get('columns', {}).keys()) or set(schema_info.get('fields', {}).keys())
            
            if not schema_fields or not file_fields:
                continue
            
            # Calculate field matches
            field_matches = []
            total_similarity = 0
            
            for file_field in file_fields:
                best_match = None
                best_similarity = 0
                
                for schema_field in schema_fields:
                    similarity = self.calculate_field_similarity(file_field, schema_field)
                    if similarity > best_similarity and similarity >= self.similarity_threshold:
                        best_similarity = similarity
                        best_match = schema_field
                
                if best_match:
                    field_matches.append({
                        'file_field': file_field,
                        'schema_field': best_match,
                        'similarity': best_similarity
                    })
                    total_similarity += best_similarity
            
            if field_matches:
                # Calculate overall match score
                match_score = total_similarity / max(len(file_fields), len(schema_fields))
                coverage = len(field_matches) / len(file_fields)
                
                matches.append({
                    'schema_name': schema_name,
                    'schema_type': schema_info.get('type', 'unknown'),
                    'match_score': match_score,
                    'coverage': coverage,
                    'field_matches': field_matches,
                    'matched_fields': len(field_matches),
                    'total_file_fields': len(file_fields),
                    'total_schema_fields': len(schema_fields)
                })
        
        # Sort by match score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches

class SchemaMatchingOrchestrator:
    """Main class that orchestrates the schema matching process"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.file_analyzer = FileStructureAnalyzer()
        self.db_extractor = DatabaseSchemaExtractor()
        
        # Configuration
        similarity_threshold = self.config.get('similarity_threshold', 0.6)
        self.matcher = SchemaMatching(similarity_threshold)
        
        self.output_format = self.config.get('output_format', 'console')
        self.output_file = self.config.get('output_file', 'schema_matches.json')
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('log_level', 'INFO')
        log_file = self.config.get('log_file', '/tmp/schema_matcher.log')
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout) if self.config.get('console_logging', True) else logging.NullHandler()
            ]
        )
    
    def scan_uploaded_files(self, db, status_filter: str = None, upload_type_filter: str = None) -> Dict[str, Dict]:
        """Scan uploaded files from database instead of directory"""
        files_structure = {}
        
        try:
            # Build query filter
            query_filter = {}
            if status_filter:
                query_filter['status'] = status_filter
            if upload_type_filter:
                query_filter['metadata.upload_type'] = upload_type_filter
            
            # Get uploaded files from database
            uploaded_files = list(db.uploaded_files.find(query_filter))
            
            self.logger.info(f"Found {len(uploaded_files)} uploaded files to analyze")
            
            for file_doc in uploaded_files:
                file_path = file_doc.get('file_path')
                file_id = file_doc.get('file_id')
                original_filename = file_doc.get('original_filename', 'unknown')
                upload_type = file_doc.get('metadata', {}).get('upload_type', 'unknown')
                
                if not file_path or not os.path.exists(file_path):
                    self.logger.warning(f"File not found: {original_filename} (ID: {file_id})")
                    continue
                
                self.logger.info(f"Analyzing uploaded file: {original_filename} (Type: {upload_type})")
                
                # Determine file type and analyze
                if file_path.lower().endswith('.json'):
                    structure = self.file_analyzer.analyze_json_file(Path(file_path))
                elif file_path.lower().endswith(('.csv', '.tsv')):
                    structure = self.file_analyzer.analyze_csv_file(Path(file_path))
                else:
                    self.logger.warning(f"Unsupported file type: {original_filename}")
                    continue
                
                if 'error' not in structure:
                    # Add upload metadata to structure
                    structure['upload_info'] = {
                        'file_id': file_id,
                        'original_filename': original_filename,
                        'upload_type': upload_type,
                        'upload_timestamp': file_doc.get('upload_timestamp'),
                        'file_size': file_doc.get('file_size'),
                        'description': file_doc.get('description', '')
                    }
                    files_structure[file_id] = structure
                else:
                    self.logger.warning(f"Error analyzing {original_filename}: {structure['error']}")
            
            return files_structure
            
        except Exception as e:
            self.logger.error(f"Failed to scan uploaded files: {e}")
            return {}
    
    def extract_database_schemas(self) -> Dict[str, Dict]:
        """Extract schemas from both PostgreSQL and MongoDB"""
        all_schemas = {}
        
        # PostgreSQL schemas
        if self.db_extractor.connect_postgres():
            self.logger.info("Extracting PostgreSQL table schemas...")
            postgres_schemas = self.db_extractor.get_postgres_tables()
            all_schemas.update(postgres_schemas)
            self.logger.info(f"Found {len(postgres_schemas)} PostgreSQL tables")
        
        # MongoDB schemas
        if self.db_extractor.connect_mongo():
            self.logger.info("Extracting MongoDB collection schemas...")
            mongo_schemas = self.db_extractor.get_mongo_collections()
            all_schemas.update(mongo_schemas)
            self.logger.info(f"Found {len(mongo_schemas)} MongoDB collections")
        
        return all_schemas
    
    def run_matching_on_uploads(self, status_filter: str = None, upload_type_filter: str = None, process_matches: bool = True) -> Dict:
        """Run the complete matching process on uploaded files"""
        self.logger.info("Starting Marine Data Schema Matcher for uploaded files")
        
        # Connect to database first
        db_connected = False
        db = None
        
        try:
            from api.utils.database import MongoDB
            with MongoDB() as database:
                if database is None:
                    raise Exception("Database connection failed")
                db = database
                db_connected = True
                
                # Scan uploaded files
                files_structure = self.scan_uploaded_files(db, status_filter, upload_type_filter)
                
                if not files_structure:
                    self.logger.warning("No uploaded files found to process")
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'files_analyzed': 0,
                        'schemas_found': 0,
                        'matches': {},
                        'processing_results': []
                    }
                
                # Extract database schemas
                schemas = self.extract_database_schemas()
                
                if not schemas:
                    self.logger.error("No database schemas found. Check your database connections.")
                    return {}
                
                # Perform matching
                self.logger.info(f"Matching {len(files_structure)} files against {len(schemas)} schemas")
                
                results = {
                    'timestamp': datetime.now().isoformat(),
                    'files_analyzed': len(files_structure),
                    'schemas_found': len(schemas),
                    'matches': {},
                    'processing_results': []
                }
                
                for file_id, file_structure in files_structure.items():
                    upload_info = file_structure.get('upload_info', {})
                    file_name = upload_info.get('original_filename', file_id)
                    upload_type = upload_info.get('upload_type', 'unknown')
                    
                    self.logger.info(f"Matching: {file_name} (Upload type: {upload_type})")
                    matches = self.matcher.match_file_to_schema(file_structure, schemas)
                    
                    # Filter matches based on upload type if specified
                    if upload_type != 'unknown':
                        filtered_matches = self.filter_matches_by_upload_type(matches, upload_type)
                        if filtered_matches:
                            matches = filtered_matches
                    
                    results['matches'][file_id] = {
                        'file_info': file_structure,
                        'potential_matches': matches[:3],  # Top 3 matches
                        'upload_info': upload_info
                    }
                    
                    if matches:
                        best_match = matches[0]
                        self.logger.info(f"Best match for {file_name}: {best_match['schema_name']} "
                                       f"(score: {best_match['match_score']:.2f})")
                        
                        # Process the match if requested
                        if process_matches:
                            processing_result = self.process_matched_file(file_id, file_structure, best_match, db)
                            results['processing_results'].append(processing_result)
                    else:
                        self.logger.warning(f"No suitable matches found for {file_name}")
                
                return results
                
        except Exception as e:
            self.logger.error(f"Error during matching process: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'files_analyzed': 0,
                'schemas_found': 0,
                'matches': {},
                'processing_results': []
            }
        finally:
            # Clean up database connections
            if hasattr(self, 'db_extractor'):
                self.db_extractor.close_connections()
    
    def filter_matches_by_upload_type(self, matches: List[Dict], upload_type: str) -> List[Dict]:
        """Filter schema matches based on frontend upload type"""
        type_mapping = {
            'edna': ['edna_sequences'],
            'oceanographic': ['oceanographic_data', 'sampling_points'],
            'species': ['species_data', 'taxonomy_data'],
            'taxonomy': ['taxonomy_data', 'species_data']
        }
        
        target_schemas = type_mapping.get(upload_type, [])
        if not target_schemas:
            return matches
        
        filtered = [match for match in matches if match.get('schema_name') in target_schemas]
        return filtered if filtered else matches  # Return original if no matches
    
    def process_matched_file(self, file_id: str, file_structure: Dict, best_match: Dict, db) -> Dict:
        """Process a file that has been matched to a schema"""
        try:
            upload_info = file_structure.get('upload_info', {})
            file_path = upload_info.get('file_path')
            schema_name = best_match.get('schema_name')
            
            if not file_path:
                # Get file path from database
                file_doc = db.uploaded_files.find_one({'file_id': file_id})
                if not file_doc:
                    raise Exception(f"File document not found: {file_id}")
                file_path = file_doc.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                raise Exception(f"File not found: {file_path}")
            
            # Import ingestion functions from data_ingestion module
            from api.routes.data_ingestion import ingest_to_postgresql, ingest_to_mongodb
            
            # Determine target database and process
            if schema_name in ['oceanographic_data', 'sampling_points']:
                result = ingest_to_postgresql(file_path, schema_name, db)
            elif schema_name in ['species_data', 'edna_sequences', 'taxonomy_data']:
                result = ingest_to_mongodb(file_path, schema_name, db)
            else:
                raise Exception(f"Unknown schema type: {schema_name}")
            
            # Update file status in database
            update_data = {
                'status': 'processed' if result.get('success') else 'processing_failed',
                'processing_results': {
                    'schema_detected': schema_name,
                    'confidence': best_match.get('match_score', 0),
                    'ingestion_results': [result],
                    'processed_timestamp': datetime.now().isoformat()
                },
                'processed_timestamp': datetime.now()
            }
            
            if not result.get('success'):
                update_data['error_log'] = [result.get('error', 'Processing failed')]
            
            db.uploaded_files.update_one(
                {'file_id': file_id},
                {'$set': update_data}
            )
            
            return {
                'file_id': file_id,
                'file_name': upload_info.get('original_filename', file_id),
                'schema_matched': schema_name,
                'confidence': best_match.get('match_score', 0),
                'processing_result': result,
                'success': result.get('success', False)
            }
            
        except Exception as e:
            error_msg = f"Failed to process {file_id}: {str(e)}"
            self.logger.error(error_msg)
            
            # Update file status with error
            try:
                db.uploaded_files.update_one(
                    {'file_id': file_id},
                    {'$set': {
                        'status': 'processing_failed',
                        'error_log': [error_msg],
                        'processed_timestamp': datetime.now()
                    }}
                )
            except:
                pass  # Don't fail if we can't update the error status
            
            return {
                'file_id': file_id,
                'file_name': upload_info.get('original_filename', file_id),
                'success': False,
                'error': error_msg
            }
    
    def generate_report(self, results: Dict):
        """Generate reports in various formats"""
        if self.output_format in ['console', 'all']:
            self._print_console_report(results)
        if self.output_format in ['json', 'all']:
            self._save_json_report(results)
        if self.output_format in ['csv', 'all']:
            self._save_csv_report(results)
    
    def _print_console_report(self, results: Dict):
        """Print detailed console report"""
        print(f"\n📊 SCHEMA MATCHING REPORT")
        print("=" * 60)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Files Analyzed: {results['files_analyzed']}")
        print(f"Database Schemas: {results['schemas_found']}")
        
        for file_path, file_info in results['matches'].items():
            file_name = Path(file_path).name
            print(f"\n📄 {file_name}")
            print("-" * 40)
            
            matches = file_info['potential_matches']
            if matches:
                print(f"🎯 Top Matches:")
                for i, match in enumerate(matches[:3], 1):
                    print(f"  {i}. {match['schema_name']} ({match['schema_type']})")
                    print(f"     Score: {match['match_score']:.2f}, Coverage: {match['coverage']:.2f}")
            else:
                print("❌ No matches found")
    
    def _save_json_report(self, results: Dict):
        """Save detailed JSON report"""
        output_path = Path(self.output_file)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        self.logger.info(f"JSON report saved to: {output_path}")
    
    def _save_csv_report(self, results: Dict):
        """Save CSV summary report"""
        csv_path = Path(self.output_file).with_suffix('.csv')
        
        rows = []
        for file_path, file_info in results['matches'].items():
            file_name = Path(file_path).name
            file_data = file_info['file_info']
            
            if file_info['potential_matches']:
                for match in file_info['potential_matches']:
                    rows.append({
                        'file_name': file_name,
                        'file_type': file_data['file_type'],
                        'schema_name': match['schema_name'],
                        'schema_type': match['schema_type'],
                        'match_score': round(match['match_score'], 3),
                        'coverage': round(match['coverage'], 3),
                        'matched_fields': match['matched_fields']
                    })
            else:
                rows.append({
                    'file_name': file_name,
                    'file_type': file_data['file_type'],
                    'schema_name': 'NO_MATCH',
                    'schema_type': 'NO_MATCH',
                    'match_score': 0,
                    'coverage': 0,
                    'matched_fields': 0
                })
        
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(csv_path, index=False)
            self.logger.info(f"CSV report saved to: {csv_path}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Marine Data Schema Matcher')
    parser.add_argument('directory', help='Directory to scan for JSON and CSV files')
    parser.add_argument('--output-format', choices=['console', 'json', 'csv', 'all'], 
                       default='all', help='Output format')
    parser.add_argument('--output-file', default='schema_matches.json', 
                       help='Output file name (for JSON/CSV reports)')
    parser.add_argument('--similarity-threshold', type=float, default=0.6,
                       help='Minimum similarity threshold for field matching')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    parser.add_argument('--log-file', default='/tmp/schema_matcher.log',
                       help='Log file path')
    parser.add_argument('--no-console-logging', action='store_true',
                       help='Disable console logging (useful for cron jobs)')
    
    args = parser.parse_args()
    
    config = {
        'similarity_threshold': args.similarity_threshold,
        'output_format': args.output_format,
        'output_file': args.output_file,
        'log_level': args.log_level,
        'log_file': args.log_file,
        'console_logging': not args.no_console_logging
    }
    
    matcher = SchemaMatchingOrchestrator(config)
    
    try:
        results = matcher.run_matching(args.directory)
        if results:
            matcher.generate_report(results)
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()