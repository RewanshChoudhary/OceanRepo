# Upload-Based File Processing System

## Overview

The Marine Data Platform has been enhanced to replace directory-based file scanning with an upload-driven processing system. This new approach integrates seamlessly with the frontend upload functionality and provides intelligent schema matching and data ingestion.

## Key Features

### 🔄 Upload-Driven Processing
- Files are processed from the database upload records instead of scanning directories
- Maintains all upload metadata (type, description, timestamps)
- Supports filtering by upload status and data type

### 🧠 Intelligent Schema Matching
- Automatic detection of data schemas based on file structure
- Confidence scoring for schema matches
- Upload type awareness (eDNA, Oceanographic, Species, Taxonomy)
- Fallback to basic schema detection when configuration is unavailable

### 🎯 Enhanced Processing Capabilities
- Bulk processing of uploaded files
- Individual file reprocessing
- Real-time status updates
- Comprehensive error handling and logging

## System Components

### 1. Enhanced SchemaMatcher Class

**Location**: `scripts/schema_matcher.py`

**New Methods**:
- `scan_uploaded_files()` - Scans database for uploaded files instead of directories
- `run_matching_on_uploads()` - Main processing method for uploaded files
- `filter_matches_by_upload_type()` - Filters schema matches by frontend upload type
- `process_matched_file()` - Processes individual files and updates database status

### 2. New API Endpoints

**Location**: `api/routes/data_ingestion.py`

**Endpoints**:
- `POST /api/ingestion/process-uploads` - Bulk process uploaded files
- `POST /api/ingestion/reprocess/{file_id}` - Reprocess specific file

### 3. Enhanced Frontend Interface

**Location**: `marine-frontend/src/components/Upload/FileUpload.tsx`

**New Features**:
- Bulk processing controls
- Upload type filtering
- Real-time processing status
- Individual file reprocessing
- Enhanced processing results display

### 4. Command Line Interface

**Location**: `scripts/process_uploads.py`

**Usage**:
```bash
# Process all uploaded files
python scripts/process_uploads.py

# Process only eDNA files
python scripts/process_uploads.py --upload-type-filter edna

# Dry run (analyze without processing)
python scripts/process_uploads.py --dry-run --show-details

# Filter by status
python scripts/process_uploads.py --status-filter uploaded
```

## Upload Type Mapping

The system maps frontend upload types to database schemas:

| Upload Type | Target Schemas |
|-------------|----------------|
| `edna` | `edna_sequences` |
| `oceanographic` | `oceanographic_data`, `sampling_points` |
| `species` | `species_data`, `taxonomy_data` |
| `taxonomy` | `taxonomy_data`, `species_data` |

## API Usage Examples

### 1. Bulk Processing

```javascript
// Process all uploaded files
const response = await ApiService.processUploads({
  process_matches: true
});

// Process only eDNA files that are uploaded but not processed
const response = await ApiService.processUploads({
  status_filter: 'uploaded',
  upload_type_filter: 'edna',
  process_matches: true
});
```

### 2. Individual File Reprocessing

```javascript
// Reprocess a specific file
const response = await ApiService.reprocessFile(fileId);
```

## Database Integration

### File Status Tracking

Files progress through these status states:
1. `uploaded` - File uploaded but not processed
2. `processing` - Currently being processed
3. `processed` - Successfully processed and ingested
4. `processing_failed` - Processing failed with error

### Metadata Storage

Each uploaded file maintains:
- Upload type (from frontend selection)
- Processing results and confidence scores
- Schema matching information
- Error logs and timestamps
- File path and metadata

## Error Handling

### Graceful Degradation
- Falls back to basic schema detection if configuration is missing
- Continues processing other files if one fails
- Maintains detailed error logs for troubleshooting

### Status Updates
- Real-time status updates in frontend
- Database status tracking
- Comprehensive error messages
- Processing timestamps and metadata

## Benefits

### 1. **Better Integration**
- Seamless connection between upload and processing
- Maintains upload context and metadata
- Respects user-selected data types

### 2. **Enhanced User Experience**
- Real-time processing feedback
- Bulk operations for efficiency
- Individual file reprocessing options
- Clear status indicators

### 3. **Improved Reliability**
- Database-driven state management
- Comprehensive error handling
- Processing history and audit trail
- Configurable confidence thresholds

### 4. **Scalability**
- Processes only uploaded files, not entire directories
- Efficient filtering and querying
- Supports large numbers of uploads
- Async processing capabilities

## Configuration

### Schema Configuration
The system uses YAML configuration files for schema definitions:
- Primary: `config/schemas.yaml`
- Fallback: Built-in schema detection

### Processing Parameters
- Similarity threshold: 0.6 (configurable)
- Confidence scoring for schema matches
- Upload type filtering
- Status-based processing

## Future Enhancements

### Planned Features
1. **Scheduled Processing**: Automatic processing of uploads at intervals
2. **Processing Priorities**: Priority queuing for different data types
3. **Validation Rules**: Enhanced data validation before ingestion
4. **Processing Analytics**: Detailed analytics on processing success rates
5. **Custom Schema Support**: User-defined schema configurations

### Integration Points
- Real-time notifications for processing completion
- Integration with data quality checks
- Connection to data visualization updates
- API webhooks for external system integration

## Migration Guide

### From Directory-Based Processing

1. **Old Method**: `matcher.run_matching(directory_path)`
2. **New Method**: `matcher.run_matching_on_uploads(filters)`

### Code Migration Examples

```python
# Old directory-based approach
results = matcher.run_matching('/path/to/data/files')

# New upload-based approach
results = matcher.run_matching_on_uploads(
    status_filter='uploaded',
    upload_type_filter='edna',
    process_matches=True
)
```

## Conclusion

The upload-based processing system provides a more integrated, user-friendly, and scalable approach to marine data ingestion. By connecting the frontend upload functionality directly with intelligent schema matching and processing, users can now easily manage their data uploads and monitor processing in real-time.

This system maintains backward compatibility while providing enhanced functionality for modern data management workflows.