#!/usr/bin/env python3
"""
Marine Data Integration Platform - Database Setup Script
Initialize PostgreSQL and MongoDB databases with schemas and sample data
"""

import os
import sys
import time
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv

# Import other setup modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.mongodb_collections import setup_mongodb_collections

# Load environment variables
load_dotenv()

def wait_for_postgres(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready"""
    print("⏳ Waiting for PostgreSQL to be ready...")
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DB', 'marine_db'),
                user=os.getenv('POSTGRES_USER', 'marineuser'),
                password=os.getenv('POSTGRES_PASSWORD', 'marinepass123')
            )
            conn.close()
            print("✅ PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError:
            if attempt < max_retries - 1:
                print(f"   Attempt {attempt + 1}/{max_retries} - retrying in {delay}s...")
                time.sleep(delay)
            else:
                print("❌ PostgreSQL connection timeout")
                return False
    return False

def wait_for_mongodb(max_retries=30, delay=2):
    """Wait for MongoDB to be ready"""
    print("⏳ Waiting for MongoDB to be ready...")
    
    for attempt in range(max_retries):
        try:
            client = MongoClient(
                host=os.getenv('MONGODB_HOST', 'localhost'),
                port=int(os.getenv('MONGODB_PORT', '27017')),
                serverSelectionTimeoutMS=1000
            )
            # Test connection
            client.admin.command('ismaster')
            client.close()
            print("✅ MongoDB is ready!")
            return True
        except Exception:
            if attempt < max_retries - 1:
                print(f"   Attempt {attempt + 1}/{max_retries} - retrying in {delay}s...")
                time.sleep(delay)
            else:
                print("❌ MongoDB connection timeout")
                return False
    return False

def setup_postgres_schema():
    """Setup PostgreSQL schema and initial data"""
    print("\n🐘 Setting up PostgreSQL schema...")
    
    try:
        # Read SQL schema file
        schema_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'postgres_schema.sql')
        
        if not os.path.exists(schema_file):
            print(f"❌ Schema file not found: {schema_file}")
            return False
            
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Connect and execute schema
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'marine_db'),
            user=os.getenv('POSTGRES_USER', 'marineuser'),
            password=os.getenv('POSTGRES_PASSWORD', 'marinepass123')
        )
        
        cursor = conn.cursor()
        
        # Execute schema creation
        cursor.execute(schema_sql)
        conn.commit()
        
        # Verify table creation
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"✅ PostgreSQL schema created successfully!")
        print(f"📊 Created tables: {', '.join(table_names)}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error setting up PostgreSQL schema: {e}")
        return False

def setup_mongodb_schema():
    """Setup MongoDB collections and initial data"""
    print("\n🍃 Setting up MongoDB collections...")
    
    try:
        # Use the existing MongoDB setup function
        connection_string = f"mongodb://{os.getenv('MONGODB_HOST', 'localhost')}:{os.getenv('MONGODB_PORT', '27017')}/"
        db_name = os.getenv('MONGODB_DB', 'marine_db')
        
        success = setup_mongodb_collections(connection_string, db_name)
        
        if success:
            print("✅ MongoDB collections setup completed!")
            return True
        else:
            print("❌ MongoDB setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up MongoDB: {e}")
        return False

def verify_database_setup():
    """Verify that both databases are properly set up"""
    print("\n🔍 Verifying database setup...")
    
    # Verify PostgreSQL
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'marine_db'),
            user=os.getenv('POSTGRES_USER', 'marineuser'),
            password=os.getenv('POSTGRES_PASSWORD', 'marinepass123')
        )
        
        cursor = conn.cursor()
        
        # Check PostGIS extension
        cursor.execute("SELECT PostGIS_Version();")
        postgis_version = cursor.fetchone()[0]
        print(f"   PostgreSQL + PostGIS: ✅ (Version: {postgis_version})")
        
        # Check table counts
        cursor.execute("SELECT COUNT(*) FROM environmental_zones")
        ez_count = cursor.fetchone()[0]
        print(f"   Environmental zones: {ez_count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   PostgreSQL verification failed: {e}")
        return False
    
    # Verify MongoDB
    try:
        client = MongoClient(
            host=os.getenv('MONGODB_HOST', 'localhost'),
            port=int(os.getenv('MONGODB_PORT', '27017'))
        )
        db = client[os.getenv('MONGODB_DB', 'marine_db')]
        
        # Check collections
        collections = db.list_collection_names()
        print(f"   MongoDB collections: {', '.join(collections)}")
        
        # Check document counts
        taxonomy_count = db.taxonomy_data.count_documents({})
        edna_count = db.edna_sequences.count_documents({})
        studies_count = db.research_studies.count_documents({})
        
        print(f"   Taxonomy records: {taxonomy_count}")
        print(f"   eDNA sequences: {edna_count}")
        print(f"   Research studies: {studies_count}")
        
        client.close()
        
    except Exception as e:
        print(f"   MongoDB verification failed: {e}")
        return False
    
    print("✅ Database verification completed successfully!")
    return True

def create_env_file():
    """Create .env file from .env.example if it doesn't exist"""
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    env_example = os.path.join(os.path.dirname(__file__), '..', '.env.example')
    
    if not os.path.exists(env_file) and os.path.exists(env_example):
        print("📋 Creating .env file from .env.example...")
        try:
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ .env file created successfully!")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("ℹ️  .env file already exists or .env.example not found")
        return True

def print_connection_info():
    """Print database connection information"""
    print("\n🔗 Database Connection Information:")
    print("=" * 50)
    print(f"PostgreSQL:")
    print(f"  Host: {os.getenv('POSTGRES_HOST', 'localhost')}")
    print(f"  Port: {os.getenv('POSTGRES_PORT', '5432')}")
    print(f"  Database: {os.getenv('POSTGRES_DB', 'marine_db')}")
    print(f"  User: {os.getenv('POSTGRES_USER', 'marineuser')}")
    
    print(f"\nMongoDB:")
    print(f"  Host: {os.getenv('MONGODB_HOST', 'localhost')}")
    print(f"  Port: {os.getenv('MONGODB_PORT', '27017')}")
    print(f"  Database: {os.getenv('MONGODB_DB', 'marine_db')}")
    
    print(f"\nWeb Interfaces (if using Docker):")
    print(f"  pgAdmin: http://localhost:8080")
    print(f"  MongoDB Express: http://localhost:8081")

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎯 Next Steps:")
    print("=" * 50)
    print("1. Insert sample data:")
    print("   python scripts/ingest_data.py")
    print()
    print("2. Explore the data:")
    print("   python scripts/query_data.py")
    print()
    print("3. Test eDNA sequence matching:")
    print("   python scripts/edna_matcher.py")
    print()
    print("4. Interactive eDNA matching:")
    print("   python scripts/edna_matcher.py --mode interactive")
    print()
    print("🚀 Your Marine Data Integration Platform is ready!")

def main():
    """Main setup function"""
    print("🌊 Marine Data Integration Platform - Database Setup")
    print("=" * 60)
    
    # Create .env file if needed
    create_env_file()
    
    # Wait for databases to be ready
    print("\n🔄 Checking database connections...")
    
    postgres_ready = wait_for_postgres()
    mongodb_ready = wait_for_mongodb()
    
    if not postgres_ready:
        print("\n❌ PostgreSQL is not available. Please ensure it's running.")
        print("💡 If using Docker: docker-compose up -d postgres")
        sys.exit(1)
    
    if not mongodb_ready:
        print("\n❌ MongoDB is not available. Please ensure it's running.")
        print("💡 If using Docker: docker-compose up -d mongodb")
        sys.exit(1)
    
    # Setup databases
    print("\n🛠️  Initializing databases...")
    
    postgres_success = setup_postgres_schema()
    mongodb_success = setup_mongodb_schema()
    
    if not postgres_success or not mongodb_success:
        print("\n❌ Database setup failed. Please check the error messages above.")
        sys.exit(1)
    
    # Verify setup
    verification_success = verify_database_setup()
    
    if not verification_success:
        print("\n❌ Database verification failed.")
        sys.exit(1)
    
    # Print connection info and next steps
    print_connection_info()
    print_next_steps()
    
    print(f"\n✨ Database setup completed successfully!")

if __name__ == "__main__":
    main()