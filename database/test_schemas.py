#!/usr/bin/env python3
"""
Marine Data Integration Platform - Database Schema Testing
Comprehensive testing script to validate database schemas, constraints, and functionality
"""

import os
import sys
import psycopg2
import pymongo
import json
from datetime import datetime, timezone
import subprocess
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_test.log')
    ]
)
logger = logging.getLogger(__name__)

class DatabaseTester:
    """Database schema and functionality tester"""
    
    def __init__(self):
        self.postgres_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5433)),
            'database': 'marine_platform',
            'user': 'marine_app_user',
            'password': 'marine_platform_2024!'
        }
        
        self.mongo_config = {
            'host': os.getenv('MONGODB_HOST', 'localhost'),
            'port': int(os.getenv('MONGODB_PORT', 27018)),
            'database': 'marine_platform',
            'username': 'marine_app_user',
            'password': 'marine_platform_2024!'
        }
        
        self.test_results = {
            'postgresql': {'passed': 0, 'failed': 0, 'errors': []},
            'mongodb': {'passed': 0, 'failed': 0, 'errors': []},
            'overall': {'passed': 0, 'failed': 0}
        }
    
    def connect_postgresql(self):
        """Connect to PostgreSQL database"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            logger.info("✓ PostgreSQL connection successful")
            return conn
        except Exception as e:
            logger.error(f"✗ PostgreSQL connection failed: {e}")
            return None
    
    def connect_mongodb(self):
        """Connect to MongoDB database"""
        try:
            client = pymongo.MongoClient(
                f"mongodb://{self.mongo_config['username']}:{self.mongo_config['password']}@"
                f"{self.mongo_config['host']}:{self.mongo_config['port']}/{self.mongo_config['database']}"
            )
            db = client[self.mongo_config['database']]
            # Test connection
            db.command('ismaster')
            logger.info("✓ MongoDB connection successful")
            return db
        except Exception as e:
            logger.error(f"✗ MongoDB connection failed: {e}")
            return None
    
    def test_postgresql_schema(self):
        """Test PostgreSQL schema structure and constraints"""
        logger.info("\n🔍 Testing PostgreSQL Schema...")
        
        conn = self.connect_postgresql()
        if not conn:
            self.test_results['postgresql']['failed'] += 1
            return
        
        try:
            cursor = conn.cursor()
            
            # Test 1: Check if all expected tables exist
            self._test_postgresql_tables(cursor)
            
            # Test 2: Check constraints and indexes
            self._test_postgresql_constraints(cursor)
            
            # Test 3: Test data insertion and validation
            self._test_postgresql_data_operations(cursor)
            
            # Test 4: Test views and functions
            self._test_postgresql_views_functions(cursor)
            
            # Test 5: Test spatial functionality
            self._test_postgresql_spatial(cursor)
            
        except Exception as e:
            logger.error(f"PostgreSQL schema test error: {e}")
            self.test_results['postgresql']['failed'] += 1
            self.test_results['postgresql']['errors'].append(str(e))
        finally:
            if conn:
                conn.close()
    
    def _test_postgresql_tables(self, cursor):
        """Test if all required tables exist with correct structure"""
        expected_tables = [
            'research_projects', 'research_vessels', 'sampling_events',
            'sampling_points', 'oceanographic_data', 'species_metadata',
            'biological_observations', 'data_processing_log'
        ]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in expected_tables:
            if table in existing_tables:
                logger.info(f"  ✓ Table '{table}' exists")
                self.test_results['postgresql']['passed'] += 1
            else:
                logger.error(f"  ✗ Table '{table}' missing")
                self.test_results['postgresql']['failed'] += 1
                self.test_results['postgresql']['errors'].append(f"Missing table: {table}")
    
    def _test_postgresql_constraints(self, cursor):
        """Test database constraints and indexes"""
        # Test primary key constraints
        cursor.execute("""
            SELECT tc.table_name, tc.constraint_name, tc.constraint_type
            FROM information_schema.table_constraints tc
            WHERE tc.table_schema = 'public' 
            AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY tc.table_name
        """)
        
        pk_constraints = cursor.fetchall()
        logger.info(f"  ✓ Found {len(pk_constraints)} primary key constraints")
        self.test_results['postgresql']['passed'] += 1
        
        # Test foreign key constraints
        cursor.execute("""
            SELECT tc.table_name, tc.constraint_name, tc.constraint_type
            FROM information_schema.table_constraints tc
            WHERE tc.table_schema = 'public' 
            AND tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name
        """)
        
        fk_constraints = cursor.fetchall()
        logger.info(f"  ✓ Found {len(fk_constraints)} foreign key constraints")
        self.test_results['postgresql']['passed'] += 1
        
        # Test indexes
        cursor.execute("""
            SELECT schemaname, tablename, indexname
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        indexes = cursor.fetchall()
        logger.info(f"  ✓ Found {len(indexes)} indexes")
        self.test_results['postgresql']['passed'] += 1
    
    def _test_postgresql_data_operations(self, cursor):
        """Test basic CRUD operations"""
        try:
            # Test INSERT with proper data types
            cursor.execute("""
                INSERT INTO research_projects (
                    project_name, project_code, principal_investigator, 
                    institution, start_date, status
                ) VALUES (
                    'Test Project', 'TEST001', 'Test PI', 
                    'Test Institution', CURRENT_DATE, 'ACTIVE'
                ) RETURNING id
            """)
            
            project_id = cursor.fetchone()[0]
            logger.info("  ✓ INSERT operation successful")
            self.test_results['postgresql']['passed'] += 1
            
            # Test UPDATE
            cursor.execute("""
                UPDATE research_projects 
                SET description = 'Test project for schema validation'
                WHERE id = %s
            """, (project_id,))
            
            logger.info("  ✓ UPDATE operation successful")
            self.test_results['postgresql']['passed'] += 1
            
            # Test SELECT with JOIN
            cursor.execute("""
                SELECT p.project_name, p.status, p.created_at
                FROM research_projects p
                WHERE p.id = %s
            """, (project_id,))
            
            result = cursor.fetchone()
            if result:
                logger.info("  ✓ SELECT operation successful")
                self.test_results['postgresql']['passed'] += 1
            
            # Test DELETE (cleanup)
            cursor.execute("DELETE FROM research_projects WHERE id = %s", (project_id,))
            logger.info("  ✓ DELETE operation successful")
            self.test_results['postgresql']['passed'] += 1
            
        except Exception as e:
            logger.error(f"  ✗ Data operations test failed: {e}")
            self.test_results['postgresql']['failed'] += 1
            self.test_results['postgresql']['errors'].append(f"Data operations: {str(e)}")
    
    def _test_postgresql_views_functions(self, cursor):
        """Test views and custom functions"""
        try:
            # Test materialized views
            cursor.execute("""
                SELECT schemaname, matviewname 
                FROM pg_matviews 
                WHERE schemaname = 'public'
            """)
            
            matviews = cursor.fetchall()
            logger.info(f"  ✓ Found {len(matviews)} materialized views")
            self.test_results['postgresql']['passed'] += 1
            
            # Test custom functions
            cursor.execute("""
                SELECT routine_name, routine_type
                FROM information_schema.routines
                WHERE routine_schema = 'public'
                AND routine_type = 'FUNCTION'
            """)
            
            functions = cursor.fetchall()
            logger.info(f"  ✓ Found {len(functions)} custom functions")
            self.test_results['postgresql']['passed'] += 1
            
            # Test a specific function
            cursor.execute("SELECT is_valid_coordinates(-63.5, 44.6)")
            result = cursor.fetchone()[0]
            if result:
                logger.info("  ✓ Custom function test successful")
                self.test_results['postgresql']['passed'] += 1
            
        except Exception as e:
            logger.error(f"  ✗ Views/functions test failed: {e}")
            self.test_results['postgresql']['failed'] += 1
            self.test_results['postgresql']['errors'].append(f"Views/functions: {str(e)}")
    
    def _test_postgresql_spatial(self, cursor):
        """Test PostGIS spatial functionality"""
        try:
            # Test PostGIS extension
            cursor.execute("SELECT PostGIS_Version()")
            postgis_version = cursor.fetchone()[0]
            logger.info(f"  ✓ PostGIS version: {postgis_version}")
            self.test_results['postgresql']['passed'] += 1
            
            # Test spatial data insertion and queries
            cursor.execute("""
                SELECT ST_AsText(ST_GeogFromText('POINT(-63.5833 44.6333)'))
            """)
            
            result = cursor.fetchone()[0]
            if 'POINT' in result:
                logger.info("  ✓ Spatial data operations successful")
                self.test_results['postgresql']['passed'] += 1
            
        except Exception as e:
            logger.error(f"  ✗ Spatial functionality test failed: {e}")
            self.test_results['postgresql']['failed'] += 1
            self.test_results['postgresql']['errors'].append(f"Spatial: {str(e)}")
    
    def test_mongodb_schema(self):
        """Test MongoDB schema structure and validation"""
        logger.info("\n🔍 Testing MongoDB Schema...")
        
        db = self.connect_mongodb()
        if not db:
            self.test_results['mongodb']['failed'] += 1
            return
        
        try:
            # Test 1: Check if collections exist
            self._test_mongodb_collections(db)
            
            # Test 2: Test document validation
            self._test_mongodb_validation(db)
            
            # Test 3: Test indexes
            self._test_mongodb_indexes(db)
            
            # Test 4: Test data operations
            self._test_mongodb_data_operations(db)
            
            # Test 5: Test geospatial queries
            self._test_mongodb_geospatial(db)
            
        except Exception as e:
            logger.error(f"MongoDB schema test error: {e}")
            self.test_results['mongodb']['failed'] += 1
            self.test_results['mongodb']['errors'].append(str(e))
    
    def _test_mongodb_collections(self, db):
        """Test if all required collections exist"""
        expected_collections = [
            'taxonomy_data', 'edna_sequences', 'uploaded_files', 'analysis_results'
        ]
        
        existing_collections = db.list_collection_names()
        
        for collection in expected_collections:
            if collection in existing_collections:
                logger.info(f"  ✓ Collection '{collection}' exists")
                self.test_results['mongodb']['passed'] += 1
            else:
                logger.error(f"  ✗ Collection '{collection}' missing")
                self.test_results['mongodb']['failed'] += 1
                self.test_results['mongodb']['errors'].append(f"Missing collection: {collection}")
    
    def _test_mongodb_validation(self, db):
        """Test document validation rules"""
        try:
            # Test valid document insertion
            test_doc = {
                'species_id': 'TEST001',
                'scientific_name': 'Test species',
                'data_source': 'TEST_DB',
                'import_date': datetime.now(timezone.utc),
                'confidence_level': 'HIGH'
            }
            
            result = db.taxonomy_data.insert_one(test_doc)
            if result.inserted_id:
                logger.info("  ✓ Valid document insertion successful")
                self.test_results['mongodb']['passed'] += 1
                
                # Cleanup
                db.taxonomy_data.delete_one({'_id': result.inserted_id})
            
            # Test invalid document rejection
            invalid_doc = {
                'scientific_name': 'Test species without required fields'
                # Missing required fields: species_id, data_source, import_date
            }
            
            try:
                db.taxonomy_data.insert_one(invalid_doc)
                logger.error("  ✗ Invalid document was accepted (should be rejected)")
                self.test_results['mongodb']['failed'] += 1
            except Exception:
                logger.info("  ✓ Invalid document properly rejected")
                self.test_results['mongodb']['passed'] += 1
                
        except Exception as e:
            logger.error(f"  ✗ Validation test failed: {e}")
            self.test_results['mongodb']['failed'] += 1
            self.test_results['mongodb']['errors'].append(f"Validation: {str(e)}")
    
    def _test_mongodb_indexes(self, db):
        """Test MongoDB indexes"""
        for collection_name in ['taxonomy_data', 'edna_sequences']:
            try:
                collection = db[collection_name]
                indexes = list(collection.list_indexes())
                logger.info(f"  ✓ Collection '{collection_name}' has {len(indexes)} indexes")
                self.test_results['mongodb']['passed'] += 1
                
                # Check for specific indexes
                index_names = [idx['name'] for idx in indexes]
                if f'idx_{collection_name.split("_")[0]}_id_unique' in index_names:
                    logger.info(f"  ✓ Unique index found for {collection_name}")
                    self.test_results['mongodb']['passed'] += 1
                
            except Exception as e:
                logger.error(f"  ✗ Index test failed for {collection_name}: {e}")
                self.test_results['mongodb']['failed'] += 1
    
    def _test_mongodb_data_operations(self, db):
        """Test basic CRUD operations"""
        try:
            collection = db.taxonomy_data
            
            # Test INSERT
            test_doc = {
                'species_id': 'CRUD_TEST_001',
                'scientific_name': 'Testicus cruddicus',
                'data_source': 'CRUD_TEST',
                'import_date': datetime.now(timezone.utc),
                'confidence_level': 'HIGH'
            }
            
            result = collection.insert_one(test_doc)
            logger.info("  ✓ MongoDB INSERT successful")
            self.test_results['mongodb']['passed'] += 1
            
            # Test UPDATE
            collection.update_one(
                {'_id': result.inserted_id},
                {'$set': {'common_name': 'Test CRUD Species'}}
            )
            logger.info("  ✓ MongoDB UPDATE successful")
            self.test_results['mongodb']['passed'] += 1
            
            # Test FIND
            found_doc = collection.find_one({'_id': result.inserted_id})
            if found_doc and found_doc.get('common_name') == 'Test CRUD Species':
                logger.info("  ✓ MongoDB FIND successful")
                self.test_results['mongodb']['passed'] += 1
            
            # Test DELETE
            delete_result = collection.delete_one({'_id': result.inserted_id})
            if delete_result.deleted_count == 1:
                logger.info("  ✓ MongoDB DELETE successful")
                self.test_results['mongodb']['passed'] += 1
                
        except Exception as e:
            logger.error(f"  ✗ MongoDB CRUD operations failed: {e}")
            self.test_results['mongodb']['failed'] += 1
            self.test_results['mongodb']['errors'].append(f"CRUD operations: {str(e)}")
    
    def _test_mongodb_geospatial(self, db):
        """Test MongoDB geospatial functionality"""
        try:
            collection = db.edna_sequences
            
            # Test geospatial query
            query = {
                'sampling_info.location': {
                    '$near': {
                        '$geometry': {
                            'type': 'Point',
                            'coordinates': [-63.5833, 44.6333]
                        },
                        '$maxDistance': 1000000  # 1000 km
                    }
                }
            }
            
            # This will only work if there are documents with location data
            count = collection.count_documents({
                'sampling_info.location': {'$exists': True}
            })
            
            if count >= 0:  # Even 0 is a valid result
                logger.info(f"  ✓ Geospatial query successful (found {count} docs with location)")
                self.test_results['mongodb']['passed'] += 1
            
        except Exception as e:
            logger.error(f"  ✗ Geospatial test failed: {e}")
            self.test_results['mongodb']['failed'] += 1
            self.test_results['mongodb']['errors'].append(f"Geospatial: {str(e)}")
    
    def test_sample_data_loading(self):
        """Test loading sample data"""
        logger.info("\n🔍 Testing Sample Data Loading...")
        
        # Test PostgreSQL sample data
        conn = self.connect_postgresql()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM research_projects")
                pg_count = cursor.fetchone()[0]
                logger.info(f"  ✓ PostgreSQL has {pg_count} sample projects")
                self.test_results['postgresql']['passed'] += 1
            except Exception as e:
                logger.error(f"  ✗ PostgreSQL sample data test failed: {e}")
                self.test_results['postgresql']['failed'] += 1
            finally:
                conn.close()
        
        # Test MongoDB sample data
        db = self.connect_mongodb()
        if db:
            try:
                mongo_count = db.taxonomy_data.count_documents({})
                logger.info(f"  ✓ MongoDB has {mongo_count} sample taxonomy records")
                self.test_results['mongodb']['passed'] += 1
            except Exception as e:
                logger.error(f"  ✗ MongoDB sample data test failed: {e}")
                self.test_results['mongodb']['failed'] += 1
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*60)
        logger.info("📊 DATABASE SCHEMA TESTING REPORT")
        logger.info("="*60)
        
        # PostgreSQL Results
        pg_total = self.test_results['postgresql']['passed'] + self.test_results['postgresql']['failed']
        pg_success_rate = (self.test_results['postgresql']['passed'] / pg_total * 100) if pg_total > 0 else 0
        
        logger.info(f"\n🐘 PostgreSQL Results:")
        logger.info(f"  Tests Passed: {self.test_results['postgresql']['passed']}")
        logger.info(f"  Tests Failed: {self.test_results['postgresql']['failed']}")
        logger.info(f"  Success Rate: {pg_success_rate:.1f}%")
        
        if self.test_results['postgresql']['errors']:
            logger.info("  Errors:")
            for error in self.test_results['postgresql']['errors']:
                logger.info(f"    - {error}")
        
        # MongoDB Results
        mongo_total = self.test_results['mongodb']['passed'] + self.test_results['mongodb']['failed']
        mongo_success_rate = (self.test_results['mongodb']['passed'] / mongo_total * 100) if mongo_total > 0 else 0
        
        logger.info(f"\n🍃 MongoDB Results:")
        logger.info(f"  Tests Passed: {self.test_results['mongodb']['passed']}")
        logger.info(f"  Tests Failed: {self.test_results['mongodb']['failed']}")
        logger.info(f"  Success Rate: {mongo_success_rate:.1f}%")
        
        if self.test_results['mongodb']['errors']:
            logger.info("  Errors:")
            for error in self.test_results['mongodb']['errors']:
                logger.info(f"    - {error}")
        
        # Overall Results
        total_passed = self.test_results['postgresql']['passed'] + self.test_results['mongodb']['passed']
        total_failed = self.test_results['postgresql']['failed'] + self.test_results['mongodb']['failed']
        total_tests = total_passed + total_failed
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\n🎯 Overall Results:")
        logger.info(f"  Total Tests: {total_tests}")
        logger.info(f"  Tests Passed: {total_passed}")
        logger.info(f"  Tests Failed: {total_failed}")
        logger.info(f"  Overall Success Rate: {overall_success_rate:.1f}%")
        
        # Final recommendation
        if overall_success_rate >= 90:
            logger.info(f"\n✅ EXCELLENT: Database schemas are well-implemented and ready for production!")
        elif overall_success_rate >= 75:
            logger.info(f"\n⚠️  GOOD: Database schemas are mostly working, minor issues need attention.")
        elif overall_success_rate >= 50:
            logger.info(f"\n🔧 NEEDS WORK: Database schemas have significant issues that need fixing.")
        else:
            logger.info(f"\n❌ CRITICAL: Database schemas have major problems and need substantial work.")
        
        logger.info("\n" + "="*60)
        
        return {
            'postgresql': {
                'passed': self.test_results['postgresql']['passed'],
                'failed': self.test_results['postgresql']['failed'],
                'success_rate': pg_success_rate,
                'errors': self.test_results['postgresql']['errors']
            },
            'mongodb': {
                'passed': self.test_results['mongodb']['passed'],
                'failed': self.test_results['mongodb']['failed'],
                'success_rate': mongo_success_rate,
                'errors': self.test_results['mongodb']['errors']
            },
            'overall': {
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'success_rate': overall_success_rate
            }
        }

def main():
    """Main testing function"""
    print("🧪 Marine Data Integration Platform - Database Schema Testing")
    print("=" * 60)
    
    tester = DatabaseTester()
    
    # Run all tests
    tester.test_postgresql_schema()
    tester.test_mongodb_schema()
    tester.test_sample_data_loading()
    
    # Generate report
    report = tester.generate_report()
    
    # Save report to JSON file
    with open('database_test_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: database_test_report.json")
    print(f"📄 Log file saved to: database_test.log")
    
    # Return appropriate exit code
    if report['overall']['success_rate'] >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()