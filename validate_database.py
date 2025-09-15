#!/usr/bin/env python3
"""
Marine Data Integration Platform - Database Validation Script
Check database tables, data integrity, and column matching
"""

import os
import sys
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv
from tabulate import tabulate
import pandas as pd

# Load environment variables
load_dotenv()

def get_postgres_connection():
    """Create PostgreSQL connection with current environment settings"""
    try:
        # Use the actual port from docker-compose (5433)
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5433'),  # Docker port
            database=os.getenv('POSTGRES_DB', 'marine_platform'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', '')
        )
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {e}")
        return None

def get_mongodb_connection():
    """Create MongoDB connection with current environment settings"""
    try:
        # Use the actual port from docker-compose (27018)
        client = MongoClient(
            host=os.getenv('MONGODB_HOST', 'localhost'),
            port=int(os.getenv('MONGODB_PORT', '27018'))  # Docker port
        )
        db = client[os.getenv('MONGODB_DB', 'marine_platform')]
        return client, db
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return None, None

def validate_postgresql():
    """Validate PostgreSQL database structure and data"""
    print("🐘 POSTGRESQL VALIDATION")
    print("=" * 50)
    
    conn = get_postgres_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check PostGIS extension
        print("\n📍 PostGIS Extension:")
        try:
            cursor.execute("SELECT PostGIS_Version();")
            postgis_version = cursor.fetchone()[0]
            print(f"   ✅ PostGIS Version: {postgis_version}")
        except Exception as e:
            print(f"   ❌ PostGIS not available: {e}")
        
        # List all tables
        print("\n📊 Database Tables:")
        cursor.execute("""
            SELECT table_name, 
                   (SELECT count(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        table_data = []
        
        for table_name, column_count in tables:
            try:
                # Count rows in each table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                table_data.append([table_name, column_count, row_count])
            except Exception as e:
                table_data.append([table_name, column_count, f"Error: {e}"])
        
        if table_data:
            print(tabulate(table_data, headers=['Table Name', 'Columns', 'Row Count'], tablefmt='grid'))
        else:
            print("   ⚠️  No tables found")
        
        # Check specific important tables
        important_tables = [
            'research_projects', 'research_vessels', 'sampling_events', 
            'sampling_points', 'oceanographic_data', 'species_metadata',
            'biological_observations'
        ]
        
        print("\n🔍 Important Tables Detail:")
        for table in important_tables:
            try:
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                print(f"\n   📋 {table.upper()} ({row_count} rows):")
                if columns:
                    col_data = [[col[0], col[1], col[2], str(col[3])[:30] + "..." if col[3] and len(str(col[3])) > 30 else col[3]] for col in columns[:5]]  # Show first 5 columns
                    print(tabulate(col_data, headers=['Column', 'Type', 'Nullable', 'Default'], tablefmt='simple'))
                    if len(columns) > 5:
                        print(f"      ... and {len(columns) - 5} more columns")
                else:
                    print("      ❌ Table not found or no columns")
                    
            except Exception as e:
                print(f"      ❌ Error checking {table}: {e}")
        
        # Sample data from key tables
        print("\n📋 SAMPLE DATA:")
        sample_tables = ['research_projects', 'sampling_events', 'oceanographic_data']
        
        for table in sample_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 2")
                    rows = cursor.fetchall()
                    
                    # Get column names
                    cursor.execute(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table}' AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """)
                    columns = [col[0] for col in cursor.fetchall()]
                    
                    print(f"\n   🔸 {table.upper()} (showing 2/{count} rows):")
                    if rows:
                        # Show only first few columns to avoid wide output
                        display_columns = columns[:4]
                        display_data = [[str(row[i])[:30] + "..." if len(str(row[i])) > 30 else row[i] for i in range(min(4, len(row)))] for row in rows]
                        print(tabulate(display_data, headers=display_columns, tablefmt='simple'))
                else:
                    print(f"\n   🔸 {table.upper()}: No data")
                    
            except Exception as e:
                print(f"\n   ❌ Error sampling {table}: {e}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL validation error: {e}")
        return False

def validate_mongodb():
    """Validate MongoDB database structure and data"""
    print("\n🍃 MONGODB VALIDATION")
    print("=" * 50)
    
    client, db = get_mongodb_connection()
    if not client or not db:
        return False
    
    try:
        # List all collections
        print("\n📊 MongoDB Collections:")
        collections = db.list_collection_names()
        
        collection_data = []
        for collection_name in collections:
            try:
                count = db[collection_name].count_documents({})
                # Get a sample document to check structure
                sample = db[collection_name].find_one()
                field_count = len(sample.keys()) if sample else 0
                collection_data.append([collection_name, count, field_count])
            except Exception as e:
                collection_data.append([collection_name, f"Error: {e}", 0])
        
        if collection_data:
            print(tabulate(collection_data, headers=['Collection', 'Document Count', 'Field Count'], tablefmt='grid'))
        else:
            print("   ⚠️  No collections found")
        
        # Check important collections
        important_collections = ['taxonomy_data', 'edna_sequences', 'uploaded_files', 'analysis_results']
        
        print("\n🔍 Important Collections Detail:")
        for collection_name in important_collections:
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                
                print(f"\n   📋 {collection_name.upper()} ({count} documents):")
                
                if count > 0:
                    # Get sample document
                    sample = collection.find_one()
                    if sample:
                        print(f"      Sample document fields: {list(sample.keys())[:10]}...")  # Show first 10 fields
                        
                        # Show some sample documents
                        samples = list(collection.find().limit(2))
                        print(f"      Sample data (showing 2/{count} documents):")
                        for i, doc in enumerate(samples, 1):
                            print(f"        Document {i}:")
                            for key, value in list(doc.items())[:5]:  # Show first 5 fields
                                value_str = str(value)[:50] + "..." if len(str(value)) > 50 else value
                                print(f"          {key}: {value_str}")
                else:
                    print("      ℹ️  Empty collection")
                    
            except Exception as e:
                print(f"      ❌ Error checking {collection_name}: {e}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB validation error: {e}")
        return False

def test_database_connections():
    """Test database connections"""
    print("🔌 DATABASE CONNECTION TEST")
    print("=" * 50)
    
    # Test PostgreSQL
    print("\n🐘 PostgreSQL Connection:")
    pg_conn = get_postgres_connection()
    if pg_conn:
        try:
            cursor = pg_conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"   ✅ Connected successfully")
            print(f"   📍 Version: {version[:50]}...")
            cursor.close()
            pg_conn.close()
        except Exception as e:
            print(f"   ❌ Connection test failed: {e}")
    
    # Test MongoDB  
    print("\n🍃 MongoDB Connection:")
    mongo_client, mongo_db = get_mongodb_connection()
    if mongo_client and mongo_db:
        try:
            server_info = mongo_client.server_info()
            print(f"   ✅ Connected successfully")
            print(f"   📍 Version: {server_info.get('version', 'Unknown')}")
            print(f"   📊 Database: {mongo_db.name}")
            mongo_client.close()
        except Exception as e:
            print(f"   ❌ Connection test failed: {e}")

def check_data_integrity():
    """Check data integrity and relationships"""
    print("\n🔍 DATA INTEGRITY CHECKS")
    print("=" * 50)
    
    pg_conn = get_postgres_connection()
    if not pg_conn:
        print("❌ Cannot perform integrity checks - PostgreSQL not available")
        return
    
    try:
        cursor = pg_conn.cursor()
        
        # Check foreign key relationships
        print("\n🔗 Foreign Key Relationships:")
        cursor.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name;
        """)
        
        fk_relationships = cursor.fetchall()
        if fk_relationships:
            fk_data = [[rel[0], rel[1], f"{rel[2]}.{rel[3]}"] for rel in fk_relationships]
            print(tabulate(fk_data, headers=['Table', 'Column', 'References'], tablefmt='simple'))
        else:
            print("   ℹ️  No foreign key relationships found")
        
        # Check for orphaned records
        print("\n🔍 Data Consistency Checks:")
        
        # Example: Check if sampling_points have corresponding events
        consistency_checks = [
            ("Sampling Points without Events", """
                SELECT COUNT(*) FROM sampling_points sp 
                LEFT JOIN sampling_events se ON sp.sampling_event_id = se.id 
                WHERE se.id IS NULL
            """),
            ("Oceanographic Data without Sampling Points", """
                SELECT COUNT(*) FROM oceanographic_data od 
                LEFT JOIN sampling_points sp ON od.sampling_point_id = sp.id 
                WHERE sp.id IS NULL
            """),
            ("Species Observations without Metadata", """
                SELECT COUNT(*) FROM biological_observations bo 
                LEFT JOIN species_metadata sm ON bo.species_id = sm.species_id 
                WHERE sm.species_id IS NULL
            """)
        ]
        
        for check_name, query in consistency_checks:
            try:
                cursor.execute(query)
                result = cursor.fetchone()[0]
                status = "✅ OK" if result == 0 else f"⚠️  {result} issues"
                print(f"   {check_name}: {status}")
            except Exception as e:
                print(f"   {check_name}: ❌ Error - {e}")
        
        cursor.close()
        pg_conn.close()
        
    except Exception as e:
        print(f"❌ Data integrity check error: {e}")

def main():
    """Main validation function"""
    print("🌊 MARINE DATA PLATFORM - DATABASE VALIDATION")
    print("=" * 60)
    print(f"🕐 Validation Time: {pd.Timestamp.now()}")
    print("\n")
    
    # Test connections first
    test_database_connections()
    
    # Validate PostgreSQL
    pg_success = validate_postgresql()
    
    # Validate MongoDB
    mongo_success = validate_mongodb()
    
    # Check data integrity
    if pg_success:
        check_data_integrity()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    pg_status = "✅ PASSED" if pg_success else "❌ FAILED"
    mongo_status = "✅ PASSED" if mongo_success else "❌ FAILED"
    
    print(f"PostgreSQL: {pg_status}")
    print(f"MongoDB: {mongo_status}")
    
    if pg_success and mongo_success:
        print("\n🎉 All database validations PASSED!")
        print("🚀 Platform is ready for use!")
    else:
        print("\n⚠️  Some database issues found.")
        print("💡 Please check the logs above for details.")
        
    return pg_success and mongo_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)