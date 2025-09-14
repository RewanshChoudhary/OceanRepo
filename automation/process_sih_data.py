#!/usr/bin/env python3
"""
Direct SIH Data Processor - Process all SIH data files immediately
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import logging
import psycopg2
from pymongo import MongoClient
import ast
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sih_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def connect_databases():
    """Connect to databases"""
    try:
        postgres_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5433'),
            database=os.getenv('POSTGRES_DB', 'marine_db'),
            user=os.getenv('POSTGRES_USER', 'marineuser'),
            password=os.getenv('POSTGRES_PASSWORD', 'marine123')
        )
        logger.info("Connected to PostgreSQL")
        
        mongo_client = MongoClient(
            host=os.getenv('MONGODB_HOST', 'localhost'),
            port=int(os.getenv('MONGODB_PORT', '27018'))
        )
        mongo_db = mongo_client[os.getenv('MONGODB_DB', 'marine_db')]
        
        # Test MongoDB connection
        mongo_client.admin.command('ismaster')
        logger.info("Connected to MongoDB")
        
        return postgres_conn, mongo_client, mongo_db
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None, None, None

def parse_metadata(metadata_str):
    """Parse metadata string"""
    try:
        if isinstance(metadata_str, str) and metadata_str.startswith('{'):
            return ast.literal_eval(metadata_str)
        return {}
    except:
        return {}

def process_sampling_points(file_path, postgres_conn):
    """Process sampling points files"""
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Processing sampling points: {Path(file_path).name} ({len(df)} records)")
        
        cursor = postgres_conn.cursor()
        success_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Map location names to coordinates
                location_coords = {
                    'indian ocean': (10.0, 75.0),
                    'arabian sea': (15.0, 65.0),
                    'bay of bengal': (15.0, 85.0),
                    'lakshadweep': (10.0, 72.0),
                    'andaman sea': (12.0, 95.0)
                }
                
                location_str = str(row.get('location', ''))
                lat, lon = 12.0, 77.0  # Default
                
                for location, coords in location_coords.items():
                    if location in location_str.lower():
                        lat, lon = coords
                        break
                
                point_id = f"SIH_{row.get('id', idx)}"
                timestamp = pd.to_datetime(row.get('timestamp', datetime.now()))
                
                # Insert with UPSERT
                cursor.execute("""
                    INSERT INTO sampling_points (
                        point_id, location, latitude, longitude, depth_m, 
                        sampling_date, sampling_method, vessel_name, parameters
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (point_id) DO UPDATE SET
                        location = EXCLUDED.location,
                        sampling_date = EXCLUDED.sampling_date
                """, (
                    point_id, location_str, lat, lon, 10.0,
                    timestamp, row.get('metadata', 'Unknown'), 'Research Vessel',
                    json.dumps(dict(row))
                ))
                success_count += 1
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
        
        postgres_conn.commit()
        cursor.close()
        logger.info(f"Successfully processed {success_count} sampling points")
        return True
        
    except Exception as e:
        logger.error(f"Error processing sampling points file {file_path}: {e}")
        return False

def process_oceanographic(file_path, postgres_conn):
    """Process oceanographic data files"""
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Processing oceanographic data: {Path(file_path).name} ({len(df)} records)")
        
        cursor = postgres_conn.cursor()
        success_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Extract parameter info
                parameter_type = row.get('parameter_type', 'unknown')
                value = row.get('value', 0)
                
                # Handle 'parameters' column format
                if 'parameters' in row and pd.notna(row['parameters']):
                    param_str = str(row['parameters'])
                    if ':' in param_str:
                        parts = param_str.split(':')
                        if len(parts) >= 2:
                            parameter_type = parts[0].strip().lower().replace(' ', '_')
                            try:
                                value = float(parts[1].strip())
                            except:
                                value = 0.0
                
                lat = row.get('latitude', 12.0)
                lon = row.get('longitude', 77.0)
                timestamp = pd.to_datetime(row.get('timestamp', datetime.now()))
                
                measurement_id = f"SIH_OCEAN_{idx}_{int(timestamp.timestamp())}"
                point_id = f"SIH_POINT_{idx}"
                
                cursor.execute("""
                    INSERT INTO oceanographic_data (
                        measurement_id, point_id, measurement_date, parameter_type,
                        value, unit, depth_m, location
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, ST_Point(%s, %s))
                    ON CONFLICT (measurement_id) DO UPDATE SET
                        value = EXCLUDED.value,
                        parameter_type = EXCLUDED.parameter_type
                """, (
                    measurement_id, point_id, timestamp, parameter_type,
                    value, 'units', 10.0, lon, lat
                ))
                success_count += 1
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
        
        postgres_conn.commit()
        cursor.close()
        logger.info(f"Successfully processed {success_count} oceanographic measurements")
        return True
        
    except Exception as e:
        logger.error(f"Error processing oceanographic file {file_path}: {e}")
        return False

def process_species(file_path, mongo_db):
    """Process species/taxonomy files"""
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Processing species data: {Path(file_path).name} ({len(df)} records)")
        
        collection = mongo_db.taxonomy_data
        success_count = 0
        
        for idx, row in df.iterrows():
            try:
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
                
                collection.replace_one(
                    {'_id': species_doc['_id']},
                    species_doc,
                    upsert=True
                )
                success_count += 1
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
        
        logger.info(f"Successfully processed {success_count} species records")
        return True
        
    except Exception as e:
        logger.error(f"Error processing species file {file_path}: {e}")
        return False

def process_edna(file_path, mongo_db):
    """Process eDNA sequence files"""
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Processing eDNA data: {Path(file_path).name} ({len(df)} records)")
        
        collection = mongo_db.edna_sequences
        success_count = 0
        
        for idx, row in df.iterrows():
            try:
                metadata = parse_metadata(row.get('sample_metadata', '{}'))
                
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
                
                collection.replace_one(
                    {'_id': sequence_doc['_id']},
                    sequence_doc,
                    upsert=True
                )
                success_count += 1
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
        
        logger.info(f"Successfully processed {success_count} eDNA sequences")
        return True
        
    except Exception as e:
        logger.error(f"Error processing eDNA file {file_path}: {e}")
        return False

def main():
    """Main processing function"""
    print("🌊 SIH MARINE DATA PROCESSOR")
    print("=" * 50)
    
    # Connect to databases
    postgres_conn, mongo_client, mongo_db = connect_databases()
    if not postgres_conn or mongo_db is None:
        logger.error("Failed to connect to databases")
        return
    
    # Define file mappings based on schema matcher results
    sih_data_path = Path("/home/rewansh57/SIH/data")
    
    file_mappings = {
        # Sampling points files
        'sampling_points': [
            'sampling_points_dataset.csv',
            'Sampling_Points_Dataset (2).csv',
            'sampling_points.csv'
        ],
        # Oceanographic data files
        'oceanographic': [
            'oceanographic_data.csv',
            'Oceanographic Data.csv'
        ],
        # Species/taxonomy files
        'species': [
            'species.csv',
            'Taxonomy.csv'
        ],
        # eDNA files
        'edna': [
            'eDNA Sequence.csv'
        ]
    }
    
    results = {
        'processed_files': 0,
        'failed_files': 0,
        'total_records': 0
    }
    
    try:
        # Process sampling points
        for filename in file_mappings['sampling_points']:
            file_path = sih_data_path / filename
            if file_path.exists():
                if process_sampling_points(file_path, postgres_conn):
                    results['processed_files'] += 1
                else:
                    results['failed_files'] += 1
        
        # Process oceanographic data
        for filename in file_mappings['oceanographic']:
            file_path = sih_data_path / filename
            if file_path.exists():
                if process_oceanographic(file_path, postgres_conn):
                    results['processed_files'] += 1
                else:
                    results['failed_files'] += 1
        
        # Process species data
        for filename in file_mappings['species']:
            file_path = sih_data_path / filename
            if file_path.exists():
                if process_species(file_path, mongo_db):
                    results['processed_files'] += 1
                else:
                    results['failed_files'] += 1
        
        # Process eDNA data
        for filename in file_mappings['edna']:
            file_path = sih_data_path / filename
            if file_path.exists():
                if process_edna(file_path, mongo_db):
                    results['processed_files'] += 1
                else:
                    results['failed_files'] += 1
        
        # Get final counts
        cursor = postgres_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sampling_points WHERE point_id LIKE 'SIH_%'")
        sp_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM oceanographic_data WHERE measurement_id LIKE 'SIH_%'")
        ocean_count = cursor.fetchone()[0]
        
        species_count = mongo_db.taxonomy_data.count_documents({'data_source': 'SIH Data Import'})
        edna_count = mongo_db.edna_sequences.count_documents({'data_source': 'SIH Data Import'})
        
        cursor.close()
        
        print(f"\n📊 PROCESSING RESULTS:")
        print(f"   Files processed: {results['processed_files']}")
        print(f"   Files failed: {results['failed_files']}")
        print(f"\n📈 DATABASE COUNTS:")
        print(f"   SIH Sampling Points: {sp_count}")
        print(f"   SIH Oceanographic Data: {ocean_count}")
        print(f"   SIH Species Data: {species_count}")
        print(f"   SIH eDNA Sequences: {edna_count}")
        print(f"   Total SIH Records: {sp_count + ocean_count + species_count + edna_count}")
        
        logger.info("✅ SIH data processing completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
    
    finally:
        if postgres_conn:
            postgres_conn.close()
        if mongo_client:
            mongo_client.close()

if __name__ == "__main__":
    main()