#!/usr/bin/env python3
"""
SIH Data Processor - Corrected version with proper schema
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
        logging.FileHandler('logs/sih_processor_corrected.log'),
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

def process_sampling_points(file_path, postgres_conn):
    """Process sampling points files using correct schema"""
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Processing sampling points: {Path(file_path).name} ({len(df)} records)")
        
        cursor = postgres_conn.cursor()
        success_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Map location names to coordinates for location field
                location_str = str(row.get('location', ''))
                timestamp = pd.to_datetime(row.get('timestamp', datetime.now()))
                
                # Use INSERT with proper column names from schema
                cursor.execute("""
                    INSERT INTO sampling_points (
                        location, timestamp, depth_meters, parameters, metadata
                    ) VALUES (%s, %s, %s, %s, %s)
                """, (
                    location_str,
                    timestamp, 
                    10.0,  # Default depth
                    json.dumps(dict(row)),  # Store full row as parameters
                    row.get('metadata', 'SIH Import')
                ))
                success_count += 1
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                # Rollback and continue
                postgres_conn.rollback()
        
        if success_count > 0:
            postgres_conn.commit()
        cursor.close()
        logger.info(f"Successfully processed {success_count} sampling points")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error processing sampling points file {file_path}: {e}")
        return False

def process_oceanographic(file_path, postgres_conn):
    """Process oceanographic data files using correct schema"""
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
                
                # Handle 'parameters' column format from SIH data
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
                
                # Get coordinates for spatial location
                lat = row.get('latitude', 12.0)
                lon = row.get('longitude', 77.0)
                timestamp = pd.to_datetime(row.get('timestamp', datetime.now()))
                
                # Create spatial point if coordinates exist
                location_geom = f"POINT({lon} {lat})"
                
                # Use correct column names from schema
                cursor.execute("""
                    INSERT INTO oceanographic_data (
                        sampling_point_id, location, parameter_type, value, 
                        unit, measurement_depth, timestamp, instrument_type
                    ) VALUES (%s, ST_GeomFromText(%s, 4326), %s, %s, %s, %s, %s, %s)
                """, (
                    None,  # sampling_point_id can be null
                    location_geom,
                    parameter_type,
                    value,
                    'units',  # Default unit
                    10.0,  # measurement_depth
                    timestamp,
                    'SIH Data Import'  # instrument_type
                ))
                success_count += 1
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                # Rollback and continue
                postgres_conn.rollback()
        
        if success_count > 0:
            postgres_conn.commit()
        cursor.close()
        logger.info(f"Successfully processed {success_count} oceanographic measurements")
        return success_count > 0
        
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
                # Generate unique ID for SIH data
                species_id = row.get('species_id', f'sih_sp_{idx:03d}')
                
                species_doc = {
                    '_id': f"sih_{species_id}",  # Prefix to avoid conflicts
                    'species_id': f"sih_{species_id}",
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
        return success_count > 0
        
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
                # Parse metadata safely
                metadata = {}
                if 'sample_metadata' in row and pd.notna(row['sample_metadata']):
                    try:
                        metadata_str = str(row['sample_metadata'])
                        if metadata_str.startswith('{'):
                            metadata = ast.literal_eval(metadata_str)
                    except:
                        pass
                
                # Generate unique ID for SIH data
                sequence_id = row.get('sequence_id', f'sih_seq_{idx:03d}')
                
                sequence_doc = {
                    '_id': f"sih_{sequence_id}",  # Prefix to avoid conflicts
                    'sequence_id': f"sih_{sequence_id}",
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
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error processing eDNA file {file_path}: {e}")
        return False

def main():
    """Main processing function"""
    print("🌊 SIH MARINE DATA PROCESSOR (CORRECTED)")
    print("=" * 60)
    
    # Connect to databases
    postgres_conn, mongo_client, mongo_db = connect_databases()
    if not postgres_conn or mongo_db is None:
        logger.error("Failed to connect to databases")
        return
    
    # Define file mappings
    sih_data_path = Path("/home/rewansh57/SIH/data")
    
    file_mappings = {
        'sampling_points': [
            'sampling_points_dataset.csv',
            'Sampling_Points_Dataset (2).csv',
            'sampling_points.csv'
        ],
        'oceanographic': [
            'oceanographic_data.csv',
            'Oceanographic Data.csv'
        ],
        'species': [
            'species.csv',
            'Taxonomy.csv'
        ],
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
        logger.info("🚀 Starting SIH data processing with corrected schema...")
        
        # Process sampling points
        for filename in file_mappings['sampling_points']:
            file_path = sih_data_path / filename
            if file_path.exists():
                logger.info(f"📍 Processing sampling points file: {filename}")
                if process_sampling_points(file_path, postgres_conn):
                    results['processed_files'] += 1
                else:
                    results['failed_files'] += 1
        
        # Process oceanographic data
        for filename in file_mappings['oceanographic']:
            file_path = sih_data_path / filename
            if file_path.exists():
                logger.info(f"🌡️ Processing oceanographic file: {filename}")
                if process_oceanographic(file_path, postgres_conn):
                    results['processed_files'] += 1
                else:
                    results['failed_files'] += 1
        
        # Process species data
        for filename in file_mappings['species']:
            file_path = sih_data_path / filename
            if file_path.exists():
                logger.info(f"🐟 Processing species file: {filename}")
                if process_species(file_path, mongo_db):
                    results['processed_files'] += 1
                else:
                    results['failed_files'] += 1
        
        # Process eDNA data
        for filename in file_mappings['edna']:
            file_path = sih_data_path / filename
            if file_path.exists():
                logger.info(f"🧬 Processing eDNA file: {filename}")
                if process_edna(file_path, mongo_db):
                    results['processed_files'] += 1
                else:
                    results['failed_files'] += 1
        
        # Get final counts
        cursor = postgres_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sampling_points WHERE metadata = 'SIH Import'")
        sp_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM oceanographic_data WHERE instrument_type = 'SIH Data Import'")
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
        
        # Show some examples
        if sp_count > 0 or ocean_count > 0:
            print(f"\n🔍 SAMPLE DATA:")
            if sp_count > 0:
                cursor = postgres_conn.cursor()
                cursor.execute("SELECT location, timestamp FROM sampling_points WHERE metadata = 'SIH Import' LIMIT 3")
                samples = cursor.fetchall()
                print(f"   Sample Locations: {[f'{s[0]} ({s[1]})' for s in samples]}")
                cursor.close()
        
        if species_count > 0:
            sample_species = list(mongo_db.taxonomy_data.find({'data_source': 'SIH Data Import'}).limit(3))
            print(f"   Sample Species: {[f"{s.get('common_name', 'Unknown')} ({s.get('species', 'Unknown')})" for s in sample_species]}")
        
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