"""
Database connection utilities for Marine Data Platform API
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
from flask import g
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration settings"""
    
    POSTGRES_CONFIG = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'marine_db'),
        'user': os.getenv('POSTGRES_USER', 'marineuser'),
        'password': os.getenv('POSTGRES_PASSWORD', 'marinepass123')
    }
    
    MONGODB_CONFIG = {
        'host': os.getenv('MONGODB_HOST', 'localhost'),
        'port': int(os.getenv('MONGODB_PORT', '27017')),
        'database': os.getenv('MONGODB_DB', 'marine_db')
    }

def get_postgres_connection():
    """Get PostgreSQL connection with connection pooling"""
    try:
        if 'postgres_conn' not in g or g.postgres_conn.closed:
            g.postgres_conn = psycopg2.connect(
                **DatabaseConfig.POSTGRES_CONFIG,
                cursor_factory=RealDictCursor
            )
        return g.postgres_conn
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return None

def get_mongodb_connection():
    """Get MongoDB connection"""
    try:
        if 'mongo_client' not in g:
            g.mongo_client = MongoClient(
                host=DatabaseConfig.MONGODB_CONFIG['host'],
                port=DatabaseConfig.MONGODB_CONFIG['port'],
                serverSelectionTimeoutMS=5000
            )
            g.mongo_db = g.mongo_client[DatabaseConfig.MONGODB_CONFIG['database']]
        return g.mongo_client, g.mongo_db
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        return None, None

def init_databases():
    """Initialize database connections and create necessary collections/tables"""
    logger = logging.getLogger(__name__)
    
    try:
        # Test PostgreSQL connection
        with PostgreSQLCursor() as cursor:
            if cursor is not None:
                logger.info("PostgreSQL connection initialized successfully")
            else:
                logger.warning("PostgreSQL connection failed during initialization")
        
        # Test MongoDB connection
        with MongoDB() as db:
            if db is not None:
                logger.info("MongoDB connection initialized successfully")
                
                # Create indexes for better performance
                try:
                    db.taxonomy_data.create_index([('species_id', 1)], unique=True)
                    db.edna_sequences.create_index([('sequence_id', 1)], unique=True)
                    db.uploaded_files.create_index([('file_id', 1)], unique=True)
                    logger.info("MongoDB indexes created successfully")
                except Exception as e:
                    logger.warning(f"Failed to create MongoDB indexes: {e}")
            else:
                logger.warning("MongoDB connection failed during initialization")
                
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

def test_connections():
    """Test database connections and return status"""
    status = {
        'postgresql': False,
        'mongodb': False
    }
    
    try:
        # Test PostgreSQL
        with PostgreSQLCursor() as cursor:
            if cursor is not None:
                cursor.execute("SELECT 1")
                cursor.fetchone()
                status['postgresql'] = True
    except Exception:
        pass
    
    try:
        # Test MongoDB
        with MongoDB() as db:
            if db is not None:
                db.list_collection_names()
                status['mongodb'] = True
    except Exception:
        pass
    
    return status

def close_db_connections():
    """Close database connections"""
    if 'postgres_conn' in g:
        g.postgres_conn.close()
    if 'mongo_client' in g:
        g.mongo_client.close()

# Remove duplicate function - using the one above

# Context managers for database operations
class PostgreSQLCursor:
    """Context manager for PostgreSQL operations"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def __enter__(self):
        self.conn = get_postgres_connection()
        if self.conn:
            self.cursor = self.conn.cursor()
            return self.cursor
        return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if exc_type is None and self.conn:
            self.conn.commit()
        elif self.conn:
            self.conn.rollback()

class MongoDB:
    """Context manager for MongoDB operations"""
    
    def __init__(self):
        self.client = None
        self.db = None
    
    def __enter__(self):
        self.client, self.db = get_mongodb_connection()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # MongoDB connections are handled by connection pooling
        pass