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

class SchemaMatcher:
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
    
    def scan_directory(self, directory_path: str) -> Dict[str, Dict]:
        """Scan directory for JSON and CSV files"""
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        files_structure = {}
        supported_files = []
        
        # Find all supported files
        for ext in self.file_analyzer.supported_extensions:
            supported_files.extend(directory.rglob(f"*{ext}"))
        
        self.logger.info(f"Found {len(supported_files)} files to analyze in {directory_path}")
        
        for file_path in supported_files:
            self.logger.info(f"Analyzing: {file_path.name}")
            
            if file_path.suffix == '.json':
                structure = self.file_analyzer.analyze_json_file(file_path)
            elif file_path.suffix == '.csv':
                structure = self.file_analyzer.analyze_csv_file(file_path)
            else:
                continue
            
            if 'error' not in structure:
                files_structure[str(file_path)] = structure
            else:
                self.logger.warning(f"Error analyzing {file_path.name}: {structure['error']}")
        
        return files_structure
    
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
    
    def run_matching(self, directory_path: str) -> Dict:
        """Run the complete matching process"""
        self.logger.info("Starting Marine Data Schema Matcher")
        
        # Scan files
        files_structure = self.scan_directory(directory_path)
        
        # Extract database schemas
        schemas = self.extract_database_schemas()
        
        if not schemas:
            self.logger.error("No database schemas found. Check your database connections.")
            return {}
        
        # Perform matching
        self.logger.info(f"Matching {len(files_structure)} files against {len(schemas)} schemas")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'directory_scanned': directory_path,
            'files_analyzed': len(files_structure),
            'schemas_found': len(schemas),
            'matches': {}
        }
        
        for file_path, file_structure in files_structure.items():
            file_name = Path(file_path).name
            self.logger.info(f"Matching: {file_name}")
            matches = self.matcher.match_file_to_schema(file_structure, schemas)
            
            results['matches'][file_path] = {
                'file_info': file_structure,
                'potential_matches': matches[:3]  # Top 3 matches
            }
            
            if matches:
                best_match = matches[0]
                self.logger.info(f"Best match for {file_name}: {best_match['schema_name']} "
                               f"(score: {best_match['match_score']:.2f})")
            else:
                self.logger.warning(f"No suitable matches found for {file_name}")
        
        # Clean up
        self.db_extractor.close_connections()
        
        return results
    
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
    
    matcher = SchemaMatcher(config)
    
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