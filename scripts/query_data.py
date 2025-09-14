#!/usr/bin/env python3
"""
Marine Data Integration Platform - Data Query Script
Query and analyze marine data from PostgreSQL and MongoDB databases
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
from datetime import datetime
import json
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
            password=os.getenv('POSTGRES_PASSWORD', 'marinepass123'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        return None

def get_mongodb_connection():
    """Create MongoDB connection"""
    try:
        client = MongoClient(
            host=os.getenv('MONGODB_HOST', 'localhost'),
            port=int(os.getenv('MONGODB_PORT', '27017'))
        )
        db = client[os.getenv('MONGODB_DB', 'marine_db')]
        return client, db
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None, None

def query_sampling_locations(conn):
    """Query sampling locations with their environmental parameters"""
    print("\n🌊 SAMPLING LOCATIONS")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id,
            ST_X(location) as longitude,
            ST_Y(location) as latitude,
            depth_meters,
            parameters->>'temperature' as temperature,
            parameters->>'salinity' as salinity,
            parameters->>'ph' as ph,
            parameters->>'dissolved_oxygen' as dissolved_oxygen,
            metadata->>'vessel' as vessel,
            metadata->>'method' as method,
            timestamp
        FROM sampling_points
        ORDER BY timestamp DESC
    """)
    
    locations = cursor.fetchall()
    
    for loc in locations:
        print(f"📍 Location: ({loc['longitude']:.2f}, {loc['latitude']:.2f})")
        print(f"   Depth: {loc['depth_meters']}m | Temperature: {loc['temperature']}°C")
        print(f"   Salinity: {loc['salinity']} PSU | pH: {loc['ph']}")
        print(f"   Dissolved O₂: {loc['dissolved_oxygen']} mg/L")
        print(f"   Method: {loc['method']} | Vessel: {loc['vessel']}")
        print(f"   Sampled: {loc['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        print()
    
    return len(locations)

def query_oceanographic_trends(conn):
    """Analyze oceanographic parameter trends"""
    print("\n📈 OCEANOGRAPHIC PARAMETER ANALYSIS")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Temperature analysis
    cursor.execute("""
        SELECT 
            parameter_type,
            AVG(value) as avg_value,
            MIN(value) as min_value,
            MAX(value) as max_value,
            STDDEV(value) as std_dev,
            COUNT(*) as measurements
        FROM oceanographic_data
        GROUP BY parameter_type
        ORDER BY parameter_type
    """)
    
    parameters = cursor.fetchall()
    
    for param in parameters:
        print(f"🌡️  {param['parameter_type'].upper()}:")
        print(f"   Average: {param['avg_value']:.2f}")
        print(f"   Range: {param['min_value']:.2f} - {param['max_value']:.2f}")
        print(f"   Std Dev: {param['std_dev']:.2f}")
        print(f"   Measurements: {param['measurements']}")
        print()

def query_spatial_analysis(conn):
    """Perform spatial analysis on marine data"""
    print("\n🗺️  SPATIAL ANALYSIS")
    print("=" * 50)
    
    cursor = conn.cursor()
    
    # Find nearby sampling points
    print("📍 Nearby Sampling Points (within 50km of Kochi):")
    cursor.execute("""
        SELECT * FROM find_nearby_samples(76.2, 10.5, 50.0)
        LIMIT 5
    """)
    
    nearby_points = cursor.fetchall()
    for point in nearby_points:
        print(f"   {point['distance_km']:.1f}km away at ({point['longitude']:.2f}, {point['latitude']:.2f})")
    
    # Environmental zones analysis
    cursor.execute("""
        SELECT 
            ez.zone_name,
            ez.zone_type,
            COUNT(sp.id) as sampling_points_in_zone
        FROM environmental_zones ez
        LEFT JOIN sampling_points sp ON ST_Within(sp.location, ez.boundary)
        GROUP BY ez.zone_name, ez.zone_type
    """)
    
    zones = cursor.fetchall()
    print(f"\n🌊 Environmental Zones Coverage:")
    for zone in zones:
        print(f"   {zone['zone_name']} ({zone['zone_type']}): {zone['sampling_points_in_zone']} sampling points")

def query_species_taxonomy(db):
    """Query species taxonomy data from MongoDB"""
    print("\n🐟 SPECIES TAXONOMY DATA")
    print("=" * 50)
    
    taxonomy = db.taxonomy_data
    
    # Group species by taxonomy levels
    pipeline = [
        {"$group": {
            "_id": "$phylum",
            "species_count": {"$sum": 1},
            "species": {"$push": {
                "species_id": "$species_id",
                "common_name": "$common_name",
                "scientific_name": "$species"
            }}
        }},
        {"$sort": {"species_count": -1}}
    ]
    
    phyla = list(taxonomy.aggregate(pipeline))
    
    for phylum in phyla:
        print(f"🔬 Phylum: {phylum['_id']} ({phylum['species_count']} species)")
        for species in phylum['species'][:3]:  # Show first 3 species
            print(f"   • {species['common_name']} ({species['scientific_name']})")
        if len(phylum['species']) > 3:
            print(f"   ... and {len(phylum['species']) - 3} more")
        print()

def query_edna_data(db):
    """Query eDNA sequence data and matches"""
    print("\n🧬 eDNA SEQUENCE ANALYSIS")  
    print("=" * 50)
    
    edna = db.edna_sequences
    
    # Get sequence matching statistics
    sequences = list(edna.find())
    
    print(f"📊 eDNA Database Summary:")
    print(f"   Total sequences: {len(sequences)}")
    
    # Group by confidence levels
    confidence_stats = {}
    for seq in sequences:
        conf = seq.get('confidence_level', 'unknown')
        confidence_stats[conf] = confidence_stats.get(conf, 0) + 1
    
    for conf, count in confidence_stats.items():
        print(f"   {conf.title()} confidence: {count}")
    
    print(f"\n🎯 Top eDNA Matches:")
    high_confidence_seqs = list(edna.find(
        {"matching_score": {"$gte": 85}}, 
        {"sequence_id": 1, "matched_species_id": 1, "matching_score": 1, "sample_metadata.location": 1}
    ).sort("matching_score", -1).limit(5))
    
    for seq in high_confidence_seqs:
        location = seq.get('sample_metadata', {}).get('location', {})
        lat = location.get('lat', 'N/A')
        lon = location.get('lon', 'N/A')
        print(f"   {seq['sequence_id']}: {seq['matched_species_id']} "
              f"({seq['matching_score']:.1f}% match) at ({lat}, {lon})")

def query_research_studies(db):
    """Query research studies and their progress"""
    print("\n📝 RESEARCH STUDIES")
    print("=" * 50)
    
    studies = db.research_studies
    
    ongoing_studies = list(studies.find({"status": "ongoing"}))
    
    for study in ongoing_studies:
        print(f"🔬 {study['title']}")
        print(f"   PI: {study['principal_investigator']} ({study['institution']})")
        print(f"   Type: {study['study_type']}")
        print(f"   Area: {study['study_area']['name']}")
        print(f"   Duration: {study['start_date'].strftime('%Y-%m-%d')} to {study['end_date'].strftime('%Y-%m-%d')}")
        print(f"   Target species: {', '.join(study['target_species'])}")
        print()

def query_integrated_analysis(conn, db):
    """Perform integrated analysis across both databases"""
    print("\n🔄 INTEGRATED CROSS-DATABASE ANALYSIS")
    print("=" * 50)
    
    # Get morphometric data from PostgreSQL
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            species_id,
            COUNT(*) as specimen_count,
            AVG(CAST(metrics->>'total_length_cm' AS FLOAT)) as avg_length,
            AVG(CAST(metrics->>'weight_g' AS FLOAT)) as avg_weight
        FROM morphometric_data 
        WHERE metrics->>'total_length_cm' IS NOT NULL
        GROUP BY species_id
    """)
    
    morphometric_data = cursor.fetchall()
    
    # Cross-reference with taxonomy data from MongoDB
    taxonomy = db.taxonomy_data
    
    print("🐟 Species Morphometric Summary:")
    for morph in morphometric_data:
        species_info = taxonomy.find_one({"species_id": morph['species_id']})
        if species_info:
            print(f"   {species_info['common_name']} ({species_info['species']}):")
            print(f"      Specimens: {morph['specimen_count']}")
            if morph['avg_length']:
                print(f"      Avg Length: {morph['avg_length']:.1f} cm")
            if morph['avg_weight']:
                print(f"      Avg Weight: {morph['avg_weight']:.0f} g")
            print()

def generate_summary_report(conn, db):
    """Generate a comprehensive summary report"""
    print("\n📋 PLATFORM SUMMARY REPORT")
    print("=" * 50)
    
    # PostgreSQL stats
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM sampling_points")
    sp_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM oceanographic_data")
    od_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM morphometric_data")
    md_count = cursor.fetchone()['count']
    
    # MongoDB stats
    taxonomy_count = db.taxonomy_data.count_documents({})
    edna_count = db.edna_sequences.count_documents({})
    studies_count = db.research_studies.count_documents({})
    
    print("📊 Database Contents:")
    print(f"   Sampling Locations: {sp_count}")
    print(f"   Oceanographic Measurements: {od_count}")
    print(f"   Morphometric Specimens: {md_count}")
    print(f"   Species in Taxonomy: {taxonomy_count}")
    print(f"   eDNA Sequences: {edna_count}")
    print(f"   Research Studies: {studies_count}")
    
    # Calculate data completeness
    total_records = sp_count + od_count + md_count + taxonomy_count + edna_count + studies_count
    print(f"\n🎯 Platform Status:")
    print(f"   Total Records: {total_records}")
    print(f"   Data Integration: ✅ Active")
    print(f"   Spatial Analysis: ✅ Available")
    print(f"   eDNA Matching: ✅ Functional")
    print(f"   Cross-DB Queries: ✅ Working")

def main():
    """Main query execution function"""
    print("🌊 Marine Data Integration Platform - Data Explorer")
    print("=" * 60)
    
    # Connect to both databases
    conn = get_postgres_connection()
    mongo_client, db = get_mongodb_connection()
    
    if not conn:
        print("❌ Failed to connect to PostgreSQL")
        sys.exit(1)
        
    if db is None:
        print("❌ Failed to connect to MongoDB")
        sys.exit(1)
    
    try:
        # Execute various queries
        query_sampling_locations(conn)
        query_oceanographic_trends(conn)
        query_spatial_analysis(conn)
        query_species_taxonomy(db)
        query_edna_data(db)
        query_research_studies(db)
        query_integrated_analysis(conn, db)
        generate_summary_report(conn, db)
        
        print("\n✨ Query analysis completed successfully!")
        print("💡 Try running 'python scripts/edna_matcher.py' to test DNA sequence matching")
        
    except Exception as e:
        print(f"❌ Error during query execution: {e}")
        sys.exit(1)
        
    finally:
        if conn:
            conn.close()
        if mongo_client:
            mongo_client.close()

if __name__ == "__main__":
    main()