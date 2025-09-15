#!/usr/bin/env python3
"""
Simple Database Validation Script
Check PostgreSQL tables, data, and basic MongoDB connectivity
"""

import os
import sys
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_postgresql():
    """Check PostgreSQL database"""
    print("🐘 POSTGRESQL DATABASE CHECK")
    print("=" * 50)
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5433'),
            database=os.getenv('POSTGRES_DB', 'marine_platform'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', '')
        )
        
        cursor = conn.cursor()
        
        print("✅ PostgreSQL Connection: SUCCESS")
        
        # Check PostgreSQL version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"📍 Version: {version.split(',')[0]}")
        
        # Check PostGIS
        try:
            cursor.execute("SELECT PostGIS_Version()")
            postgis_version = cursor.fetchone()[0]
            print(f"📍 PostGIS: {postgis_version}")
        except:
            print("⚠️  PostGIS: Not available")
        
        # List all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"\n📊 DATABASE TABLES ({len(tables)} total):")
        print("-" * 30)
        
        table_stats = []
        for (table_name,) in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                table_stats.append((table_name, count))
                status = "✅" if count > 0 else "📝"
                print(f"{status} {table_name:<25} {count:>8} rows")
            except Exception as e:
                print(f"❌ {table_name:<25} ERROR: {str(e)[:40]}")
        
        # Check for important tables
        important_tables = [
            'research_projects', 'research_vessels', 'sampling_events', 
            'sampling_points', 'oceanographic_data', 'species_metadata',
            'biological_observations', 'data_processing_log'
        ]
        
        print(f"\n🎯 IMPORTANT TABLES STATUS:")
        print("-" * 30)
        found_tables = [name for name, _ in table_stats]
        
        for table in important_tables:
            if table in found_tables:
                count = next((count for name, count in table_stats if name == table), 0)
                status = "✅ EXISTS" if count > 0 else "📝 EMPTY"
                print(f"{status:<12} {table}")
            else:
                print(f"❌ MISSING   {table}")
        
        # Sample some data
        print(f"\n🔍 SAMPLE DATA:")
        print("-" * 30)
        
        sample_tables = ['research_projects', 'sampling_events', 'oceanographic_data']
        for table in sample_tables:
            if table in found_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                        sample_row = cursor.fetchone()
                        
                        # Get column names
                        cursor.execute(f"""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = '{table}' 
                            ORDER BY ordinal_position LIMIT 5
                        """)
                        columns = [col[0] for col in cursor.fetchall()]
                        
                        print(f"\n📋 {table.upper()} (1/{count} rows):")
                        for i, col_name in enumerate(columns):
                            if i < len(sample_row):
                                value = str(sample_row[i])[:50]
                                if len(str(sample_row[i])) > 50:
                                    value += "..."
                                print(f"   {col_name}: {value}")
                    else:
                        print(f"\n📋 {table.upper()}: No data")
                        
                except Exception as e:
                    print(f"\n❌ Error sampling {table}: {e}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False

def check_mongodb():
    """Check MongoDB database"""
    print("\n🍃 MONGODB DATABASE CHECK")
    print("=" * 50)
    
    try:
        # Connect to MongoDB
        client = MongoClient(
            host=os.getenv('MONGODB_HOST', 'localhost'),
            port=int(os.getenv('MONGODB_PORT', '27018'))
        )
        
        # Test connection
        server_info = client.server_info()
        print("✅ MongoDB Connection: SUCCESS")
        print(f"📍 Version: {server_info.get('version', 'Unknown')}")
        
        # Get database
        db_name = os.getenv('MONGODB_DB', 'marine_platform')
        db = client[db_name]
        print(f"📊 Database: {db_name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"\n📊 COLLECTIONS ({len(collections)} total):")
        print("-" * 30)
        
        if collections:
            for collection_name in collections:
                try:
                    count = db[collection_name].count_documents({})
                    status = "✅" if count > 0 else "📝"
                    print(f"{status} {collection_name:<25} {count:>8} docs")
                except Exception as e:
                    print(f"❌ {collection_name:<25} ERROR: {str(e)[:40]}")
        else:
            print("📝 No collections found")
        
        # Check important collections
        important_collections = ['taxonomy_data', 'edna_sequences', 'uploaded_files', 'analysis_results']
        
        print(f"\n🎯 IMPORTANT COLLECTIONS STATUS:")
        print("-" * 30)
        
        for collection in important_collections:
            if collection in collections:
                count = db[collection].count_documents({})
                status = "✅ EXISTS" if count > 0 else "📝 EMPTY"
                print(f"{status:<12} {collection}")
            else:
                print(f"❌ MISSING   {collection}")
        
        # Sample data from collections with data
        print(f"\n🔍 SAMPLE DATA:")
        print("-" * 30)
        
        for collection_name in collections[:3]:  # Check first 3 collections
            try:
                count = db[collection_name].count_documents({})
                if count > 0:
                    sample = db[collection_name].find_one()
                    print(f"\n📋 {collection_name.upper()} (1/{count} documents):")
                    if sample:
                        for key, value in list(sample.items())[:5]:  # Show first 5 fields
                            value_str = str(value)[:50]
                            if len(str(value)) > 50:
                                value_str += "..."
                            print(f"   {key}: {value_str}")
                else:
                    print(f"\n📋 {collection_name.upper()}: No data")
            except Exception as e:
                print(f"\n❌ Error sampling {collection_name}: {e}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB Error: {e}")
        return False

def main():
    """Main validation function"""
    print("🌊 MARINE DATA PLATFORM - DATABASE CHECK")
    print("=" * 60)
    
    # Check PostgreSQL
    pg_success = check_postgresql()
    
    # Check MongoDB  
    mongo_success = check_mongodb()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    pg_status = "✅ OPERATIONAL" if pg_success else "❌ ISSUES"
    mongo_status = "✅ OPERATIONAL" if mongo_success else "❌ ISSUES"
    
    print(f"PostgreSQL: {pg_status}")
    print(f"MongoDB:    {mongo_status}")
    
    if pg_success and mongo_success:
        print("\n🎉 Both databases are operational!")
        print("🚀 Platform is ready for data operations!")
    elif pg_success:
        print("\n⚠️  PostgreSQL is working but MongoDB has issues")
    elif mongo_success:
        print("\n⚠️  MongoDB is working but PostgreSQL has issues")
    else:
        print("\n❌ Both databases have issues - check configurations")
    
    return pg_success and mongo_success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)