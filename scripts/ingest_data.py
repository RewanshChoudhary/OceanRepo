#!/usr/bin/env python3
"""
Marine Data Integration Platform - Data Ingestion Script
Inserts sample oceanographic, morphometric, and spatial data into PostgreSQL
"""

import os
import sys
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from datetime import datetime, timezone
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_postgres_connection():
    """Create PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'marine_db'),
            user=os.getenv('POSTGRES_USER', 'marineuser'),
            password=os.getenv('POSTGRES_PASSWORD', 'marinepass123')
        )
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        return None

def insert_sampling_points(conn):
    """Insert sample sampling points data"""
    cursor = conn.cursor()
    
    sample_points = [
        {
            'location': (76.2, 10.5),  # Kochi, Kerala
            'depth_meters': 15.5,
            'parameters': {
                'temperature': 29.5,
                'salinity': 35.2,
                'ph': 8.1,
                'dissolved_oxygen': 6.8
            },
            'metadata': {
                'method': 'CTD cast',
                'vessel': 'RV Sindhu Sadhana',
                'weather': 'Clear'
            }
        },
        {
            'location': (75.8, 11.2),  # Calicut, Kerala
            'depth_meters': 25.0,
            'parameters': {
                'temperature': 28.9,
                'salinity': 35.0,
                'ph': 8.0,
                'dissolved_oxygen': 7.1
            },
            'metadata': {
                'method': 'Water sampling',
                'vessel': 'RV Sindhu Sankalp',
                'weather': 'Partly cloudy'
            }
        },
        {
            'location': (76.5, 9.8),  # Kollam, Kerala
            'depth_meters': 8.2,
            'parameters': {
                'temperature': 30.1,
                'salinity': 34.8,
                'ph': 8.2,
                'dissolved_oxygen': 6.5
            },
            'metadata': {
                'method': 'Shore station',
                'vessel': 'Shore based',
                'weather': 'Sunny'
            }
        },
        {
            'location': (74.9, 12.1),  # Mangalore, Karnataka
            'depth_meters': 18.5,
            'parameters': {
                'temperature': 29.8,
                'salinity': 35.1,
                'ph': 8.1,
                'dissolved_oxygen': 6.9
            },
            'metadata': {
                'method': 'CTD cast',
                'vessel': 'RV Sindhu Sadhana',
                'weather': 'Overcast'
            }
        }
    ]
    
    sampling_point_ids = []
    
    for point in sample_points:
        point_id = str(uuid.uuid4())
        sampling_point_ids.append(point_id)
        
        cursor.execute("""
            INSERT INTO sampling_points (id, location, depth_meters, parameters, metadata, timestamp)
            VALUES (%s, ST_SetSRID(ST_Point(%s, %s), 4326), %s, %s, %s, %s)
        """, (
            point_id,
            point['location'][0], point['location'][1],
            point['depth_meters'],
            Json(point['parameters']),
            Json(point['metadata']),
            datetime.now(timezone.utc)
        ))
    
    conn.commit()
    print(f"✅ Inserted {len(sample_points)} sampling points")
    return sampling_point_ids

def insert_oceanographic_data(conn, sampling_point_ids):
    """Insert detailed oceanographic measurements"""
    cursor = conn.cursor()
    
    # Sample locations corresponding to sampling points
    locations = [
        (76.2, 10.5), (75.8, 11.2), (76.5, 9.8), (74.9, 12.1)
    ]
    
    parameters_data = [
        {'type': 'temperature', 'value': 29.5, 'unit': 'celsius', 'depth': 5.0},
        {'type': 'temperature', 'value': 29.2, 'unit': 'celsius', 'depth': 10.0},
        {'type': 'temperature', 'value': 28.8, 'unit': 'celsius', 'depth': 15.0},
        {'type': 'salinity', 'value': 35.2, 'unit': 'psu', 'depth': 5.0},
        {'type': 'salinity', 'value': 35.3, 'unit': 'psu', 'depth': 10.0},
        {'type': 'salinity', 'value': 35.5, 'unit': 'psu', 'depth': 15.0},
        {'type': 'dissolved_oxygen', 'value': 6.8, 'unit': 'mg/L', 'depth': 5.0},
        {'type': 'dissolved_oxygen', 'value': 6.5, 'unit': 'mg/L', 'depth': 10.0},
        {'type': 'dissolved_oxygen', 'value': 6.2, 'unit': 'mg/L', 'depth': 15.0},
        {'type': 'ph', 'value': 8.1, 'unit': 'ph_units', 'depth': 5.0},
        {'type': 'ph', 'value': 8.0, 'unit': 'ph_units', 'depth': 10.0},
        {'type': 'ph', 'value': 7.9, 'unit': 'ph_units', 'depth': 15.0}
    ]
    
    measurement_count = 0
    
    for i, location in enumerate(locations):
        sampling_point_id = sampling_point_ids[i] if i < len(sampling_point_ids) else sampling_point_ids[0]
        
        for param in parameters_data:
            cursor.execute("""
                INSERT INTO oceanographic_data 
                (sampling_point_id, location, parameter_type, value, unit, measurement_depth, timestamp, instrument_type)
                VALUES (%s, ST_SetSRID(ST_Point(%s, %s), 4326), %s, %s, %s, %s, %s, %s)
            """, (
                sampling_point_id,
                location[0], location[1],
                param['type'],
                param['value'],
                param['unit'],
                param['depth'],
                datetime.now(timezone.utc),
                'CTD Sensor'
            ))
            measurement_count += 1
    
    conn.commit()
    print(f"✅ Inserted {measurement_count} oceanographic measurements")

def insert_morphometric_data(conn):
    """Insert sample morphometric data for marine specimens"""
    cursor = conn.cursor()
    
    specimens = [
        {
            'species_id': 'sp_001',
            'specimen_id': 'SPEC_001_2024',
            'location': (76.2, 10.5),
            'depth': 15.0,
            'metrics': {
                'total_length_cm': 45.2,
                'standard_length_cm': 38.7,
                'weight_g': 1250,
                'body_depth_cm': 12.3,
                'head_length_cm': 14.1
            },
            'collector': 'Dr. Marine Biologist',
            'preservation': 'Formalin 10%',
            'condition': 'Excellent, complete specimen'
        },
        {
            'species_id': 'sp_003',
            'specimen_id': 'SPEC_003_2024',
            'location': (75.8, 11.2),
            'depth': 25.0,
            'metrics': {
                'mantle_length_cm': 28.5,
                'total_length_cm': 42.0,
                'weight_g': 890,
                'tentacle_length_cm': 35.2,
                'fin_width_cm': 15.8
            },
            'collector': 'Dr. Cephalopod Expert',
            'preservation': 'Ethanol 70%',
            'condition': 'Good, minor tentacle damage'
        },
        {
            'species_id': 'sp_001',
            'specimen_id': 'SPEC_001B_2024',
            'location': (76.5, 9.8),
            'depth': 8.0,
            'metrics': {
                'total_length_cm': 52.1,
                'standard_length_cm': 44.3,
                'weight_g': 1680,
                'body_depth_cm': 14.8,
                'head_length_cm': 16.2
            },
            'collector': 'Dr. Fish Taxonomist',
            'preservation': 'Formalin 10%',
            'condition': 'Excellent, breeding colors visible'
        }
    ]
    
    for specimen in specimens:
        cursor.execute("""
            INSERT INTO morphometric_data 
            (species_id, specimen_id, sample_location, depth_collected, metrics, 
             collector_name, preservation_method, condition_notes, timestamp)
            VALUES (%s, %s, ST_SetSRID(ST_Point(%s, %s), 4326), %s, %s, %s, %s, %s, %s)
        """, (
            specimen['species_id'],
            specimen['specimen_id'],
            specimen['location'][0], specimen['location'][1],
            specimen['depth'],
            Json(specimen['metrics']),
            specimen['collector'],
            specimen['preservation'],
            specimen['condition'],
            datetime.now(timezone.utc)
        ))
    
    conn.commit()
    print(f"✅ Inserted {len(specimens)} morphometric specimens")

def verify_data_insertion(conn):
    """Verify that data was inserted correctly"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check sampling points
    cursor.execute("SELECT COUNT(*) as count FROM sampling_points")
    sp_count = cursor.fetchone()['count']
    
    # Check oceanographic data
    cursor.execute("SELECT COUNT(*) as count FROM oceanographic_data")
    od_count = cursor.fetchone()['count']
    
    # Check morphometric data
    cursor.execute("SELECT COUNT(*) as count FROM morphometric_data")
    md_count = cursor.fetchone()['count']
    
    # Check environmental zones
    cursor.execute("SELECT COUNT(*) as count FROM environmental_zones")
    ez_count = cursor.fetchone()['count']
    
    print(f"\n📊 Data Verification:")
    print(f"   Sampling Points: {sp_count}")
    print(f"   Oceanographic Measurements: {od_count}")
    print(f"   Morphometric Specimens: {md_count}")
    print(f"   Environmental Zones: {ez_count}")
    
    # Show sample spatial query
    cursor.execute("""
        SELECT 
            ST_X(location) as longitude,
            ST_Y(location) as latitude,
            parameters->>'temperature' as temp,
            parameters->>'salinity' as salinity
        FROM sampling_points 
        ORDER BY timestamp DESC 
        LIMIT 3
    """)
    
    print(f"\n🌊 Sample Spatial Data:")
    for row in cursor.fetchall():
        print(f"   Location: ({row['longitude']:.2f}, {row['latitude']:.2f}) - "
              f"Temp: {row['temp']}°C, Salinity: {row['salinity']} PSU")

def main():
    """Main data ingestion function"""
    print("🌊 Marine Data Integration Platform - Data Ingestion")
    print("=" * 60)
    
    # Connect to PostgreSQL
    conn = get_postgres_connection()
    if not conn:
        print("❌ Failed to connect to PostgreSQL. Exiting.")
        sys.exit(1)
    
    try:
        print("📍 Inserting sampling points...")
        sampling_point_ids = insert_sampling_points(conn)
        
        print("🌡️  Inserting oceanographic data...")
        insert_oceanographic_data(conn, sampling_point_ids)
        
        print("🐟 Inserting morphometric data...")
        insert_morphometric_data(conn)
        
        print("✔️  Verifying data insertion...")
        verify_data_insertion(conn)
        
        print(f"\n🎉 Data ingestion completed successfully!")
        print(f"💡 You can now run 'python scripts/query_data.py' to explore the data")
        
    except Exception as e:
        print(f"❌ Error during data ingestion: {e}")
        conn.rollback()
        sys.exit(1)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()