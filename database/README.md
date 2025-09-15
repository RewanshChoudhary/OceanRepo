# Marine Data Integration Platform - Database Documentation

This directory contains the complete database infrastructure for the Marine Data Integration Platform, including schemas, initialization scripts, sample data, and testing utilities for both PostgreSQL and MongoDB databases.

## 📁 Directory Structure

```
database/
├── postgresql/
│   ├── schema.sql              # Complete PostgreSQL schema with tables, constraints, and indexes
│   ├── init_database.sql       # Database initialization script
│   └── sample_data.sql         # Sample data for testing and development
├── mongodb/
│   ├── schema.js              # MongoDB collections, validation, and indexes
│   ├── init_database.js       # Database initialization script
│   └── sample_data.js         # Sample documents for testing
├── test_schemas.py            # Comprehensive testing script
└── README.md                  # This documentation file
```

## 🗄️ Database Overview

### PostgreSQL - Relational Data
- **Oceanographic measurements** - Physical and chemical water properties
- **Sampling events and points** - Research cruise and station data
- **Species metadata** - Taxonomic and ecological information
- **Biological observations** - Species abundance and distribution
- **Research projects and vessels** - Metadata about data collection

### MongoDB - Document Data
- **Taxonomy data** - Comprehensive species classification with flexible metadata
- **eDNA sequences** - Environmental DNA sequences with analysis results
- **Uploaded files** - File processing and ingestion tracking
- **Analysis results** - Computational analysis outputs and results

## 🚀 Quick Start

### Prerequisites
- PostgreSQL 14+ with PostGIS extension
- MongoDB 5.0+
- Python 3.9+ with psycopg2 and pymongo

### 1. PostgreSQL Setup

```bash
# Start PostgreSQL (adjust port as needed)
sudo systemctl start postgresql

# Run the initialization script as superuser
sudo -u postgres psql -p 5433 -f postgresql/init_database.sql

# Load sample data
sudo -u postgres psql -p 5433 -d marine_platform -f postgresql/sample_data.sql
```

### 2. MongoDB Setup

```bash
# Start MongoDB (adjust port as needed)
sudo systemctl start mongod --port 27018

# Run the initialization script
mongosh --port 27018 mongodb/init_database.js

# Load sample data
mongosh --port 27018 marine_platform mongodb/sample_data.js
```

### 3. Test the Setup

```bash
# Install required Python packages
pip install psycopg2 pymongo

# Run comprehensive tests
python database/test_schemas.py
```

## 📋 Database Schemas

### PostgreSQL Tables

#### Core Research Infrastructure
- **`research_projects`** - Research projects and expeditions
- **`research_vessels`** - Research vessels and their capabilities
- **`sampling_events`** - Discrete sampling events or stations
- **`sampling_points`** - Individual sampling points within events

#### Scientific Data
- **`oceanographic_data`** - Physical/chemical oceanographic measurements
- **`species_metadata`** - Species taxonomy and ecological metadata  
- **`biological_observations`** - Species observations and abundance data
- **`data_processing_log`** - Processing and quality control tracking

#### Key Features
- **PostGIS spatial data types** for geographic coordinates
- **JSONB metadata fields** for flexible data storage  
- **Comprehensive constraints** for data quality
- **Performance indexes** on frequently queried fields
- **Custom functions** for validation and calculations
- **Materialized views** for complex analytical queries

### MongoDB Collections

#### Primary Collections
- **`taxonomy_data`** - Species classification with rich metadata
- **`edna_sequences`** - Environmental DNA sequences and analysis
- **`uploaded_files`** - File upload and processing tracking
- **`analysis_results`** - Computational analysis outputs

#### Key Features
- **JSON Schema validation** for document structure
- **Geospatial indexes** for location-based queries
- **Text indexes** for full-text search
- **Compound indexes** for complex query patterns
- **TTL indexes** for automatic data expiration

## 🔧 Configuration

### Environment Variables

```bash
# PostgreSQL Configuration
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_DB=marine_platform
export POSTGRES_USER=marine_app_user
export POSTGRES_PASSWORD=marine_platform_2024!

# MongoDB Configuration  
export MONGODB_HOST=localhost
export MONGODB_PORT=27018
export MONGODB_DB=marine_platform
export MONGODB_USER=marine_app_user
export MONGODB_PASSWORD=marine_platform_2024!
```

### Database Users

#### PostgreSQL Users
- **`postgres`** - Superuser for administration
- **`marine_app_user`** - Application user with read/write access

#### MongoDB Users
- **`marine_admin`** - Database administrator
- **`marine_app_user`** - Application user with read/write access
- **`marine_read_user`** - Read-only user for analytics

## 📊 Sample Data

The sample data includes realistic marine research data:

### PostgreSQL Sample Data
- **3 research projects** (AMBS2024, CEMP2024, DSEI2023)
- **3 research vessels** (CCGS Hudson, RV Oceanus, CCGS Amundsen)
- **3 sampling events** with real coordinates
- **4 sampling points** at different depths
- **4 oceanographic measurements** with typical marine values
- **4 species metadata records** for common marine species
- **3 biological observations** with abundance data

### MongoDB Sample Data
- **5 comprehensive taxonomy records** with full hierarchical classification
- **4 eDNA sequences** with quality control and taxonomic assignments
- **3 uploaded file records** with processing metadata
- **3 analysis results** showing different analytical approaches

## 🧪 Testing

The testing script (`test_schemas.py`) performs comprehensive validation:

### PostgreSQL Tests
- ✅ Table structure and relationships
- ✅ Constraints and data types
- ✅ Indexes and performance optimizations
- ✅ CRUD operations
- ✅ Custom functions and views
- ✅ PostGIS spatial functionality

### MongoDB Tests  
- ✅ Collection existence and structure
- ✅ Document validation rules
- ✅ Index performance and coverage
- ✅ CRUD operations
- ✅ Geospatial queries
- ✅ Aggregation pipelines

### Running Tests

```bash
# Basic test run
python database/test_schemas.py

# View detailed logs
tail -f database_test.log

# Check test report
cat database_test_report.json
```

## 🚀 Production Deployment

### PostgreSQL Production Setup
1. **Enable connection pooling** with pgbouncer
2. **Configure backup strategy** with pg_dump/pg_basebackup
3. **Set up monitoring** with pg_stat_statements
4. **Tune performance** parameters for your workload
5. **Configure SSL** for secure connections

### MongoDB Production Setup
1. **Enable authentication** and role-based access
2. **Configure replica sets** for high availability
3. **Set up backup strategy** with mongodump or MongoDB Atlas
4. **Configure monitoring** with MongoDB Compass or ops tools
5. **Enable SSL/TLS** for secure connections

### Performance Optimization

#### PostgreSQL
```sql
-- Recommended configuration adjustments
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET work_mem = '64MB';
SELECT pg_reload_conf();

-- Analyze statistics for query planning
ANALYZE;

-- Reindex for maintenance
REINDEX DATABASE marine_platform;
```

#### MongoDB
```javascript
// Enable profiler for slow queries
db.setProfilingLevel(1, { slowms: 100 });

// Compact collections periodically
db.runCommand({ compact: 'taxonomy_data' });

// Update collection statistics
db.taxonomy_data.reIndex();
```

## 📈 Monitoring and Maintenance

### Health Checks
```bash
# PostgreSQL health check
psql -h localhost -p 5433 -U marine_app_user -d marine_platform -c "SELECT version();"

# MongoDB health check
mongosh --port 27018 -u marine_app_user -p marine_platform_2024! --eval "db.runCommand('ping')"
```

### Regular Maintenance
- **Weekly**: Update table/collection statistics
- **Monthly**: Check and rebuild indexes if needed
- **Quarterly**: Review and archive old data
- **Annually**: Perform major version upgrades

### Backup Strategy
```bash
# PostgreSQL backup
pg_dump -h localhost -p 5433 -U postgres marine_platform > backup_$(date +%Y%m%d).sql

# MongoDB backup  
mongodump --port 27018 --db marine_platform --out backup_$(date +%Y%m%d)
```

## 🔍 Troubleshooting

### Common Issues

#### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check port availability
netstat -tlnp | grep 5433

# Test connection
psql -h localhost -p 5433 -U postgres -c "SELECT 1;"
```

#### MongoDB Connection Issues
```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Check port availability  
netstat -tlnp | grep 27018

# Test connection
mongosh --port 27018 --eval "db.runCommand('ping')"
```

#### Performance Issues
- Check slow query logs
- Analyze query execution plans
- Review index usage statistics
- Monitor resource utilization

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Marine Data Standards](https://ioos.noaa.gov/data-management/)

## 🤝 Contributing

When modifying the database schema:

1. **Update schema files** in both `postgresql/` and `mongodb/` directories
2. **Add migration scripts** for existing deployments
3. **Update sample data** to reflect schema changes
4. **Run comprehensive tests** to ensure compatibility
5. **Update documentation** to reflect changes

## 📞 Support

For issues with the database setup:
1. Check the troubleshooting section above
2. Review test results and logs
3. Consult the detailed error messages
4. Check system resources and dependencies

---

*This database infrastructure supports the Marine Data Integration Platform's mission to enable comprehensive marine research data management and analysis.*