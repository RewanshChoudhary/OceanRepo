# Marine Data Integration Platform 🌊

A comprehensive, AI-powered platform for integrating and analyzing marine research data including oceanographic measurements, species taxonomy, eDNA sequences, and ecosystem monitoring. Built for hackathons, research institutions, and marine conservation efforts.

## 🚀 Key Features

### 🗄️ **Dual Database Architecture**
- **PostgreSQL + PostGIS**: Spatial oceanographic data, sampling points, and measurements
- **MongoDB**: Flexible taxonomy data, eDNA sequences, and file metadata

### 🧬 **AI-Powered eDNA Analysis**
- K-mer based sequence matching for species identification
- Batch processing of multiple DNA sequences
- Confidence scoring and taxonomic classification
- Interactive and programmatic analysis modes

### 📁 **Smart File Processing**
- Automatic schema detection and field mapping
- Support for CSV, JSON, Excel, and FASTA formats
- Intelligent data validation and error handling
- Real-time processing with confidence scoring

### 🌐 **REST API & Web Interface**
- RESTful API for all platform functionality
- React-based frontend with interactive dashboards
- Real-time data visualization and mapping
- File upload interface with progress tracking

### 🧪 **Production Ready**
- Comprehensive test coverage (unit, integration, API)
- Docker containerization for easy deployment
- Configurable environments and scaling
- Error logging and monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker and Docker Compose
- Node.js 16+ (for frontend)
- 4GB RAM minimum

### 1. **Clone and Setup Environment**
```bash
# Clone repository
git clone <repository-url>
cd marine-data-platform

# Setup environment
cp .env.example .env
# Edit .env file with your configurations
```

### 2. **Install Dependencies**
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd marine-frontend
npm install
cd ..
```

### 3. **Start Services** 
```bash
# Start databases
docker-compose up -d

# Wait for services to be ready (30 seconds)
sleep 30
```

### 4. **Initialize Platform**
```bash
# Initialize databases
python scripts/setup_database.py

# Load sample data
python scripts/ingest_data.py

# Verify eDNA matching
python scripts/edna_matcher.py --mode test
```

### 5. **Start Application**
```bash
# Start API server (Terminal 1)
python api/app.py

# Start frontend (Terminal 2)
cd marine-frontend
npm run dev
```

### 6. **Access Platform**
- **Web Interface**: http://localhost:5173
- **API Docs**: http://localhost:5000/api/info
- **Health Check**: http://localhost:5000/api/health
- **pgAdmin**: http://localhost:8080 (admin@marine.com / admin123)
- **MongoDB Express**: http://localhost:8081 (admin / admin123)

## 📁 Project Structure

```
marine-data-platform/
├── 🐳 docker-compose.yml           # Container orchestration
├── 📋 requirements.txt             # Python dependencies
├── ⚙️ .env.example                 # Environment template
├── 🧪 run_tests.py                 # Comprehensive test runner
│
├── 🔌 api/                         # REST API Server
│   ├── app.py                      # Main Flask application
│   ├── routes/                     # API endpoints
│   │   ├── data_ingestion.py       # File upload & processing
│   │   ├── species_identification.py # eDNA analysis API
│   │   ├── oceanographic.py        # Ocean data endpoints
│   │   └── ...                     # Other API routes
│   ├── utils/                      # Shared utilities
│   │   ├── database.py             # Database connections
│   │   └── response.py             # API response formatting
│   └── middleware/                 # Authentication & middleware
│
├── 🌐 marine-frontend/             # React Web Interface
│   ├── src/
│   │   ├── components/             # UI components
│   │   │   ├── Upload/FileUpload.tsx # File upload interface
│   │   │   ├── Dashboard/          # Data visualization
│   │   │   └── Identification/     # eDNA analysis UI
│   │   ├── services/api.ts         # API client
│   │   └── context/AppContext.tsx  # Global state management
│   ├── package.json
│   └── vite.config.ts
│
├── 🗄️ database/                    # Database Schemas
│   ├── postgresql/                 # PostgreSQL setup
│   │   ├── schema.sql              # Table definitions
│   │   └── sample_data.sql         # Sample data
│   └── mongodb/                    # MongoDB setup
│       ├── schema.js               # Collection schemas
│       └── sample_data.js          # Sample documents
│
├── 🔬 scripts/                     # Analysis & Processing
│   ├── setup_database.py          # Database initialization
│   ├── ingest_data.py              # Data loading utilities
│   ├── edna_matcher.py             # eDNA sequence analysis
│   └── schema_matcher.py           # Smart file processing
│
├── ⚙️ config/                      # Configuration Files
│   └── schemas.yaml                # Data schema definitions
│
├── 🧪 tests/                       # Test Suite
│   ├── test_file_upload.py         # File processing tests
│   ├── test_edna_analysis.py       # eDNA matching tests
│   └── test_api_integration.py     # API endpoint tests
│
├── 📊 data/                        # Sample Data
│   ├── sample_sequences.json       # Test eDNA sequences
│   ├── test_oceanographic_data.csv # Ocean measurements
│   └── test_species_data.csv       # Taxonomy data
│
└── 📚 docs/                        # Documentation
    ├── API.md                      # API reference
    ├── DEPLOYMENT.md               # Deployment guide
    └── DEVELOPMENT.md              # Development setup
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=marine_db
POSTGRES_USER=marineuser
POSTGRES_PASSWORD=marinepass123

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=marine_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=True
SECRET_KEY=marine-platform-secret-key-2024

# Frontend Configuration
VITE_API_URL=http://localhost:5000/api

# File Upload Limits
MAX_FILE_SIZE=50MB
UPLOAD_FOLDER=./uploads
```

### Data Schema Configuration (config/schemas.yaml)

The platform uses intelligent schema matching to automatically detect and process different data types:

- **Oceanographic Data**: Temperature, salinity, depth measurements
- **Species Data**: Taxonomy, classification, descriptions
- **eDNA Sequences**: DNA sequences with species matching
- **Sampling Points**: Geographic locations and metadata

## 🔌 API Endpoints

### File Upload & Processing
- `POST /api/ingestion/upload` - Upload and process data files
- `GET /api/ingestion/files` - List uploaded files with pagination
- `GET /api/ingestion/files/{id}` - Get file details and processing results
- `POST /api/ingestion/process/{id}` - Manually process uploaded file
- `GET /api/ingestion/schemas` - Get supported data schemas

### eDNA Analysis & Species Identification
- `POST /api/species/identify` - Identify species from single eDNA sequence
- `POST /api/species/batch-identify` - Batch process multiple sequences
- `GET /api/species/taxonomy` - Browse species taxonomy with filtering
- `GET /api/species/taxonomy/{id}` - Get detailed species information
- `GET /api/species/statistics` - Get database statistics

### Data Access & Search
- `GET /api/oceanographic` - Access oceanographic measurements
- `GET /api/spatial` - Spatial queries and geographic data
- `GET /api/search` - Full-text search across all data
- `GET /api/analytics` - Data analytics and insights

### System & Monitoring
- `GET /api/health` - System health check
- `GET /api/info` - API information and version

### Example Usage

```bash
# Upload a CSV file
curl -X POST http://localhost:5000/api/ingestion/upload \
  -F "file=@oceanographic_data.csv" \
  -F "description=Monthly temperature measurements" \
  -F "auto_process=true"

# Identify species from eDNA sequence
curl -X POST http://localhost:5000/api/species/identify \
  -H "Content-Type: application/json" \
  -d '{"sequence": "ATGCGATCGATCGATCG", "min_score": 70}'

# Get system health
curl http://localhost:5000/api/health
```

## 🧪 Testing

Comprehensive test suite with unit, integration, and API tests:

```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type database

# Run with different verbosity
python run_tests.py --verbosity 1

# Skip test report generation
python run_tests.py --no-report
```

### Test Coverage
- **File Upload & Processing**: Schema detection, validation, ingestion
- **eDNA Analysis**: K-mer generation, sequence matching, confidence scoring
- **API Integration**: All endpoints, error handling, data validation
- **Database Operations**: CRUD operations, spatial queries, aggregations

## 🚀 Deployment

### Docker Production Deployment

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# Scale API services
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# View logs
docker-compose logs -f api
```

### Environment-Specific Deployment

```bash
# Development
export NODE_ENV=development
docker-compose up -d

# Production
export NODE_ENV=production
docker-compose -f docker-compose.prod.yml up -d

# Testing
export NODE_ENV=test
python run_tests.py --type integration
```

## 📊 Performance & Monitoring

### System Requirements
- **Minimum**: 4GB RAM, 2 CPU cores, 10GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB SSD storage
- **Production**: 16GB RAM, 8 CPU cores, 100GB SSD storage

### Monitoring Endpoints
- Health Check: `/api/health`
- System Metrics: `/api/analytics/system`
- Database Stats: `/api/species/statistics`

### Performance Benchmarks
- **File Processing**: ~1000 CSV rows/second
- **eDNA Matching**: ~100 sequences/second
- **API Response Time**: <200ms for most endpoints
- **Database Queries**: <100ms for typical operations

## 🤝 Contributing

We welcome contributions! This platform was built for hackathons and research collaboration.

### Development Workflow

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Install development dependencies**: `pip install -r requirements.txt`
4. **Make changes and add tests**
5. **Run test suite**: `python run_tests.py`
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open Pull Request**

### Code Standards
- Follow PEP 8 for Python code
- Use TypeScript for frontend components
- Write tests for new functionality
- Document API changes
- Maintain backwards compatibility

### Priority Areas for Contribution
- 🧬 Advanced eDNA analysis algorithms
- 🗺️ Enhanced geospatial visualization
- 📱 Mobile-responsive interface improvements
- 🔍 Machine learning for data classification
- 📊 Advanced analytics and reporting
- 🔒 Enhanced security and authentication

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for marine research and conservation
- Inspired by open science principles
- Designed for hackathon rapid prototyping
- Optimized for educational and research use

## 📞 Support

For questions, issues, or contributions:
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 📧 **Email**: support@marine-platform.org
- 💬 **Discord**: [Marine Platform Community](https://discord.gg/marine-platform)
- 📚 **Documentation**: [Full Documentation](https://docs.marine-platform.org)

---

**🌊 Built with ❤️ for marine science and ocean conservation**
