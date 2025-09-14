#!/usr/bin/env python3
"""
Marine Data Integration Platform - Automated Data Processor
Processes discovered data files and ingests them into the appropriate databases
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Any
import hashlib
import uuid
import ast
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import psycopg2
from pymongo import MongoClient
from automation.run_schema_matcher import AutomationRunner

class DataProcessor:
    def __init__(self):
        """Initialize the data processor"""
        self.postgres_conn = None
        self.mongo_client = None
        self.mongo_db = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/data_processor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Track processed files
        self.processed_files_log = Path('logs/processed_files.json')
        self.processed_files = self.load_processed_files()
        
    def load_processed_files(self) -> Dict[str, Dict]:
        """Load record of previously processed files"""
        if self.processed_files_log.exists():
            try:
                with open(self.processed_files_log, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load processed files log: {e}")
        return {}
    
    def save_processed_files(self):
        """Save record of processed files"""
        self.processed_files_log.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.processed_files_log, 'w') as f:
                json.dump(self.processed_files, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Could not save processed files log: {e}")
    
    def connect_databases(self):
        """Connect to PostgreSQL and MongoDB"""
        try:
            self.postgres_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5433'),
                database=os.getenv('POSTGRES_DB', 'marine_db'),
                user=os.getenv('POSTGRES_USER', 'marineuser'),
                password=os.getenv('POSTGRES_PASSWORD', 'marine123')
            )
            if self.postgres_conn:
                self.logger.info("Connected to PostgreSQL")
            else:
                self.logger.error("Failed to connect to PostgreSQL")
                return False
        except Exception as e:
            self.logger.error(f"PostgreSQL connection error: {e}")
            return False
        
        try:
            self.mongo_client = MongoClient(
                host=os.getenv('MONGODB_HOST', 'localhost'),
                port=int(os.getenv('MONGODB_PORT', '27018'))
            )
            self.mongo_db = self.mongo_client[os.getenv('MONGODB_DB', 'marine_db')]
            
            if self.mongo_db is not None:
                # Test the connection
                self.mongo_client.admin.command('ismaster')
                self.logger.info("Connected to MongoDB")
            else:
                self.logger.error("Failed to connect to MongoDB")
                return False
        except Exception as e:
            self.logger.error(f"MongoDB connection error: {e}")
            return False
        
        return True
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for tracking changes"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed (new or changed)"""
        file_hash = self.calculate_file_hash(Path(file_path))
        
        if file_path in self.processed_files:
            stored_hash = self.processed_files[file_path].get('hash', '')
            if stored_hash == file_hash:
                self.logger.info(f"File unchanged, skipping: {Path(file_path).name}")
                return False
        
        return True
    
    def parse_metadata(self, metadata_str: str) -> Dict:
        """Safely parse metadata string to dictionary"""
        try:
            if isinstance(metadata_str, str):
                # Try to parse as literal dict or JSON
                if metadata_str.startswith('{'):
                    try:
                        return ast.literal_eval(metadata_str)
                    except:
                        return json.loads(metadata_str)
                else:
                    return {}
            elif isinstance(metadata_str, dict):
                return metadata_str
            else:
                return {}
        except Exception as e:
            self.logger.warning(f"Could not parse metadata: {metadata_str} - {e}")
            return {}
    
    def process_sampling_points_file(self, file_path: str) -> bool:
        """Process sampling points data"""
        try:
            df = pd.read_csv(file_path)
            self.logger.info(f"Processing sampling points file: {Path(file_path).name} ({len(df)} records)")
            
            cursor = self.postgres_conn.cursor()
            
            for idx, row in df.iterrows():
                # Extract location coordinates if available
                lat, lon = None, None
                location_str = str(row.get('location', ''))
                
                # Map location names to approximate coordinates
                location_coords = {
                    'indian ocean': (10.0, 75.0),
                    'arabian sea': (15.0, 65.0),
                    'bay of bengal': (15.0, 85.0),
                    'lakshadweep': (10.0, 72.0),
                    'andaman sea': (12.0, 95.0)
                }
                
                for location, coords in location_coords.items():
                    if location in location_str.lower():
                        lat, lon = coords
                        break
                
                if lat is None or lon is None:
                    lat, lon = 12.0, 77.0  # Default to approximate Indian Ocean
                
                # Insert sampling point
                insert_query = """
                INSERT INTO sampling_points (
                    point_id, location, latitude, longitude, depth_m, 
                    sampling_date, sampling_method, vessel_name, parameters
                ) VALUES (%s, %s, ST_Point(%s, %s), %s, %s, %s, %s, %s, %s)
                ON CONFLICT (point_id) DO UPDATE SET
                    location = EXCLUDED.location,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    depth_m = EXCLUDED.depth_m,
                    sampling_date = EXCLUDED.sampling_date,
                    sampling_method = EXCLUDED.sampling_method,
                    vessel_name = EXCLUDED.vessel_name,
                    parameters = EXCLUDED.parameters
                """
                
                point_id = f"SIH_{row.get('id', idx)}"
                timestamp = pd.to_datetime(row.get('timestamp', datetime.now()))
                
                cursor.execute(insert_query, (
                    point_id,
                    location_str,
                    lon, lat,  # ST_Point takes longitude first
                    10.0,  # Default depth
                    timestamp,
                    row.get('metadata', 'Unknown'),
                    'Research Vessel',
                    json.dumps(dict(row))
                ))
            
            self.postgres_conn.commit()
            cursor.close()
            
            self.logger.info(f"Successfully processed {len(df)} sampling points")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing sampling points file: {e}")
            return False
    
    def process_oceanographic_file(self, file_path: str) -> bool:
        """Process oceanographic data"""
        try:
            df = pd.read_csv(file_path)
            self.logger.info(f"Processing oceanographic file: {Path(file_path).name} ({len(df)} records)")
            
            cursor = self.postgres_conn.cursor()
            
            for idx, row in df.iterrows():
                # Handle different parameter formats
                parameter_type = row.get('parameter_type', 'unknown')
                value = row.get('value', 0)
                
                # Extract parameters from 'parameters' column if present
                if 'parameters' in row:
                    param_str = str(row['parameters'])
                    if ':' in param_str:
                        parts = param_str.split(':')
                        if len(parts) >= 2:
                            parameter_type = parts[0].strip().lower().replace(' ', '_')
                            try:
                                value = float(parts[1].strip())
                            except ValueError:
                                value = 0.0
                
                # Get coordinates
                lat = row.get('latitude', 12.0)
                lon = row.get('longitude', 77.0)
                timestamp = pd.to_datetime(row.get('timestamp', datetime.now()))
                
                # Insert oceanographic data
                insert_query = """
                INSERT INTO oceanographic_data (
                    measurement_id, point_id, measurement_date, parameter_type,
                    value, unit, depth_m, location
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, ST_Point(%s, %s))
                ON CONFLICT (measurement_id) DO UPDATE SET
                    parameter_type = EXCLUDED.parameter_type,
                    value = EXCLUDED.value,
                    measurement_date = EXCLUDED.measurement_date
                """
                
                measurement_id = f"SIH_OCEAN_{idx}_{int(timestamp.timestamp())}"
                point_id = f"SIH_POINT_{idx}"
                
                cursor.execute(insert_query, (
                    measurement_id,
                    point_id,
                    timestamp,
                    parameter_type,
                    value,
                    'units',  # Default unit
                    10.0,  # Default depth
                    lon, lat  # ST_Point takes longitude first
                ))
            
            self.postgres_conn.commit()
            cursor.close()
            
            self.logger.info(f"Successfully processed {len(df)} oceanographic measurements")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing oceanographic file: {e}")
            return False
    
    def process_species_file(self, file_path: str) -> bool:
        """Process species/taxonomy data into MongoDB"""
        try:
            df = pd.read_csv(file_path)
            self.logger.info(f"Processing species file: {Path(file_path).name} ({len(df)} records)")
            
            collection = self.mongo_db.taxonomy_data
            
            for idx, row in df.iterrows():
                species_doc = {
                    '_id': row.get('species_id', f'sih_sp_{idx:03d}'),
                    'species_id': row.get('species_id', f'sih_sp_{idx:03d}'),
                    'kingdom': row.get('kingdom', 'Unknown'),
                    'phylum': row.get('phylum', 'Unknown'),
                    'class': row.get('class', 'Unknown'),
                    'order': row.get('order', 'Unknown'),
                    'family': row.get('family', 'Unknown'),
                    'genus': row.get('genus', 'Unknown'),
                    'species': row.get('species', 'Unknown'),
                    'common_name': row.get('common_name', 'Unknown'),
                    'description': row.get('description', ''),
                    'reference_link': row.get('reference_link', ''),
                    'data_source': 'SIH Data Import',
                    'import_date': datetime.now(timezone.utc)
                }
                
                # Upsert the document
                collection.replace_one(
                    {'_id': species_doc['_id']},
                    species_doc,
                    upsert=True
                )
            
            self.logger.info(f"Successfully processed {len(df)} species records")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing species file: {e}")
            return False
    
    def process_edna_file(self, file_path: str) -> bool:
        """Process eDNA sequence data into MongoDB"""
        try:
            df = pd.read_csv(file_path)
            self.logger.info(f"Processing eDNA file: {Path(file_path).name} ({len(df)} records)")
            
            collection = self.mongo_db.edna_sequences
            
            for idx, row in df.iterrows():
                # Parse metadata if present
                metadata = {}
                if 'sample_metadata' in row:
                    metadata = self.parse_metadata(row['sample_metadata'])
                
                sequence_doc = {
                    '_id': row.get('sequence_id', f'sih_seq_{idx:03d}'),
                    'sequence_id': row.get('sequence_id', f'sih_seq_{idx:03d}'),
                    'sequence': row.get('sequence', ''),
                    'matched_species_id': row.get('matched_species_id', None),
                    'matching_score': float(row.get('matching_score', 0.0)),
                    'sequencing_method': row.get('method', 'Unknown'),
                    'sample_location': metadata.get('sample_location', 'Unknown'),
                    'collection_date': metadata.get('collection_date', datetime.now().isoformat()),
                    'water_temperature': metadata.get('water_temp_celsius', None),
                    'ph': metadata.get('ph', None),
                    'water_type': metadata.get('water_type', 'unknown'),
                    'confidence_level': 'high' if float(row.get('matching_score', 0)) > 0.9 
                                     else 'medium' if float(row.get('matching_score', 0)) > 0.7 
                                     else 'low',
                    'data_source': 'SIH Data Import',
                    'import_date': datetime.now(timezone.utc)
                }
                
                # Add coordinates if available in metadata
                if 'latitude' in metadata and 'longitude' in metadata:
                    sequence_doc['coordinates'] = {
                        'latitude': float(metadata['latitude']),
                        'longitude': float(metadata['longitude'])
                    }
                
                # Upsert the document
                collection.replace_one(
                    {'_id': sequence_doc['_id']},
                    sequence_doc,
                    upsert=True
                )
            
            self.logger.info(f"Successfully processed {len(df)} eDNA sequences")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing eDNA file: {e}")
            return False
    
    def process_file(self, file_info: Dict) -> bool:
        """Process a single file based on its schema match"""
        file_path = file_info['file_path']
        schema_match = file_info.get('best_match', {}).get('table_name', '')
        
        if not self.should_process_file(file_path):
            return True
        
        self.logger.info(f"Processing file: {Path(file_path).name} -> {schema_match}")
        
        success = False
        
        try:
            if 'sampling_points' in schema_match.lower():
                success = self.process_sampling_points_file(file_path)
            elif 'oceanographic' in schema_match.lower():
                success = self.process_oceanographic_file(file_path)
            elif 'taxonomy' in schema_match.lower() or 'species' in Path(file_path).name.lower():
                success = self.process_species_file(file_path)
            elif 'edna' in schema_match.lower() or 'sequence' in Path(file_path).name.lower():
                success = self.process_edna_file(file_path)
            else:
                self.logger.warning(f"No processor for schema: {schema_match}")
                return False
            
            if success:
                # Record successful processing
                self.processed_files[file_path] = {
                    'hash': self.calculate_file_hash(Path(file_path)),
                    'processed_date': datetime.now(timezone.utc).isoformat(),
                    'schema_match': schema_match,
                    'status': 'success'
                }
                self.save_processed_files()
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            self.processed_files[file_path] = {
                'hash': self.calculate_file_hash(Path(file_path)),
                'processed_date': datetime.now(timezone.utc).isoformat(),
                'schema_match': schema_match,
                'status': 'error',
                'error': str(e)
            }
            self.save_processed_files()
            return False
    
    def run_automated_processing(self) -> Dict:
        """Run the complete automated processing pipeline"""
        self.logger.info("🚀 Starting automated data processing pipeline")
        
        results = {
            'start_time': datetime.now(timezone.utc).isoformat(),
            'files_discovered': 0,
            'files_processed': 0,
            'files_failed': 0,
            'files_skipped': 0,
            'errors': []
        }
        
        try:
            # Step 1: Connect to databases
            if not self.connect_databases():
                results['errors'].append("Failed to connect to databases")
                return results
            
            # Step 2: Run schema matcher to discover files
            self.logger.info("🔍 Running schema matcher to discover files...")
            automation_runner = AutomationRunner()
            if not automation_runner.run():
                results['errors'].append("Schema matching failed")
                return results
            
            # Step 3: Find the latest schema matching results
            reports_dir = Path('reports')
            if not reports_dir.exists():
                results['errors'].append("No reports directory found")
                return results
            
            # Get the most recent schema match report
            report_files = sorted(reports_dir.glob('schema_matches_*.json'), reverse=True)
            if not report_files:
                results['errors'].append("No schema match reports found")
                return results
            
            latest_report = report_files[0]
            self.logger.info(f"📊 Using schema match report: {latest_report.name}")
            
            # Step 4: Load and process matched files
            with open(latest_report, 'r') as f:
                schema_results = json.load(f)
            
            # Extract file information from the schema results
            files_to_process = []
            
            # Handle different report formats
            if 'matches' in schema_results:
                # Old format
                for file_name, file_data in schema_results['matches'].items():
                    if file_data.get('potential_matches'):
                        best_match = file_data['potential_matches'][0]
                        files_to_process.append({
                            'file_path': file_data.get('file_path', f"/home/rewansh57/SIH/data/{file_name}"),
                            'file_name': file_name,
                            'best_match': best_match
                        })
            else:
                # New format - search for processable files in scan directories
                scan_dirs = ['/home/rewansh57/SIH/data', '/home/rewansh57/SIH/marine-data-platform/data']
                for scan_dir in scan_dirs:
                    scan_path = Path(scan_dir)
                    if scan_path.exists():
                        for file_path in scan_path.rglob('*.csv'):
                            file_name = file_path.name.lower()
                            schema_match = None
                            
                            if any(keyword in file_name for keyword in ['sampling', 'point']):
                                schema_match = 'sampling_points'
                            elif any(keyword in file_name for keyword in ['ocean', 'data']):
                                schema_match = 'oceanographic_data'
                            elif any(keyword in file_name for keyword in ['species', 'taxonomy']):
                                schema_match = 'taxonomy_data'
                            elif any(keyword in file_name for keyword in ['edna', 'sequence']):
                                schema_match = 'edna_sequences'
                            
                            if schema_match:
                                files_to_process.append({
                                    'file_path': str(file_path),
                                    'file_name': file_path.name,
                                    'best_match': {'table_name': schema_match}
                                })
            
            results['files_discovered'] = len(files_to_process)
            self.logger.info(f"📁 Discovered {len(files_to_process)} files to process")
            
            # Step 5: Process each file
            for file_info in files_to_process:
                try:
                    if self.process_file(file_info):
                        results['files_processed'] += 1
                    else:
                        results['files_failed'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error processing {file_info['file_name']}: {e}")
                    results['files_failed'] += 1
                    results['errors'].append(f"{file_info['file_name']}: {str(e)}")
            
            results['end_time'] = datetime.now(timezone.utc).isoformat()
            
            self.logger.info("✅ Automated processing completed")
            self.logger.info(f"📊 Summary: {results['files_processed']} processed, {results['files_failed']} failed, {results['files_skipped']} skipped")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fatal error in automated processing: {e}")
            results['errors'].append(f"Fatal error: {str(e)}")
            results['end_time'] = datetime.now(timezone.utc).isoformat()
            return results
        
        finally:
            # Close database connections
            if self.postgres_conn:
                self.postgres_conn.close()
            if self.mongo_client:
                self.mongo_client.close()

def main():
    """Main entry point for automated data processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated Marine Data Processor")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without doing it')
    
    args = parser.parse_args()
    
    print("🌊 AUTOMATED MARINE DATA PROCESSOR")
    print("=" * 50)
    
    processor = DataProcessor()
    results = processor.run_automated_processing()
    
    # Print results
    print(f"\n📊 PROCESSING RESULTS:")
    print(f"   Files discovered: {results['files_discovered']}")
    print(f"   Files processed: {results['files_processed']}")
    print(f"   Files failed: {results['files_failed']}")
    print(f"   Files skipped: {results['files_skipped']}")
    
    if results['errors']:
        print(f"\n❌ ERRORS:")
        for error in results['errors']:
            print(f"   - {error}")
    
    # Save results
    results_file = f"reports/processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    Path(results_file).parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("✨ Processing completed!")

if __name__ == "__main__":
    main()