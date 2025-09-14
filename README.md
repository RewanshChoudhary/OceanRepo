# Marine Data Integration Platform 🌊

A scalable, AI-powered platform for integrating and analyzing marine data including oceanographic measurements, morphometric data, and eDNA sequences.

## Features

- **PostgreSQL + PostGIS**: Spatial oceanographic and morphometric data storage
- **MongoDB**: Flexible taxonomy and eDNA sequence storage
- **Python Scripts**: Data ingestion, querying, and analysis tools
- **K-mer eDNA Matching**: Simple AI-powered species identification
- **Docker Ready**: Portable setup with environment variables

## Quick Start

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   pip install -r requirements.txt
   ```

2. **Start Services**:
   ```bash
   docker-compose up -d
   ```

3. **Initialize Database**:
   ```bash
   python scripts/setup_database.py
   ```

4. **Insert Sample Data**:
   ```bash
   python scripts/ingest_data.py
   ```

5. **Query Data**:
   ```bash
   python scripts/query_data.py
   ```

6. **Test eDNA Matching**:
   ```bash
   python scripts/edna_matcher.py
   ```

## Project Structure

```
marine-data-platform/
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── database/
│   ├── postgres_schema.sql
│   └── mongodb_collections.py
├── scripts/
│   ├── setup_database.py
│   ├── ingest_data.py
│   ├── query_data.py
│   └── edna_matcher.py
└── data/
    └── sample_sequences.json
```

## Environment Variables

- `POSTGRES_HOST`: PostgreSQL host (default: localhost)
- `POSTGRES_PORT`: PostgreSQL port (default: 5432)
- `POSTGRES_DB`: Database name (default: marine_db)
- `POSTGRES_USER`: Database user (default: marineuser)
- `POSTGRES_PASSWORD`: Database password
- `MONGODB_HOST`: MongoDB host (default: localhost)
- `MONGODB_PORT`: MongoDB port (default: 27017)
- `MONGODB_DB`: MongoDB database name (default: marine_db)

## API Endpoints (Future Enhancement)

The platform is designed to be easily extended with REST API endpoints for web applications.

## Contributing

This is a hackathon prototype. Contributions welcome for production enhancements!