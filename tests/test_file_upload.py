#!/usr/bin/env python3
"""
Unit Tests for File Upload and Processing
Tests the file upload, parsing, schema detection, and database ingestion functionality
"""

import os
import sys
import unittest
import tempfile
import json
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.schema_matcher import SchemaMatcher, FileStructureAnalyzer
from api.routes.data_ingestion import detect_schema_basic, process_uploaded_file


class TestFileStructureAnalyzer(unittest.TestCase):
    """Test file structure analysis functionality"""
    
    def setUp(self):
        self.analyzer = FileStructureAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_analyze_csv_file_oceanographic(self):
        """Test CSV analysis with oceanographic data"""
        # Create test CSV
        test_data = {
            'latitude': [44.6, 45.2, 46.1],
            'longitude': [-63.5, -62.8, -61.9],
            'temperature': [12.5, 14.2, 13.8],
            'salinity': [35.1, 34.8, 35.3],
            'depth': [10, 15, 20],
            'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03']
        }
        
        df = pd.DataFrame(test_data)
        csv_path = Path(self.temp_dir) / 'oceanographic_test.csv'
        df.to_csv(csv_path, index=False)
        
        # Analyze file
        result = self.analyzer.analyze_csv_file(csv_path)
        
        # Assertions
        self.assertEqual(result['file_type'], 'csv')
        self.assertEqual(len(result['columns']), 6)
        self.assertIn('latitude', result['columns'])
        self.assertIn('temperature', result['columns'])
        self.assertEqual(result['total_rows'], 3)
    
    def test_analyze_json_file_species(self):
        """Test JSON analysis with species data"""
        # Create test JSON
        test_data = [
            {
                'species_id': 'sp_001',
                'scientific_name': 'Gadus morhua',
                'common_name': 'Atlantic cod',
                'kingdom': 'Animalia',
                'phylum': 'Chordata'
            },
            {
                'species_id': 'sp_002',
                'scientific_name': 'Homarus americanus',
                'common_name': 'American lobster',
                'kingdom': 'Animalia',
                'phylum': 'Arthropoda'
            }
        ]
        
        json_path = Path(self.temp_dir) / 'species_test.json'
        with open(json_path, 'w') as f:
            json.dump(test_data, f)
        
        # Analyze file
        result = self.analyzer.analyze_json_file(json_path)
        
        # Assertions
        self.assertEqual(result['file_type'], 'json')
        self.assertIn('species_id', result['fields'])
        self.assertIn('scientific_name', result['fields'])
        self.assertEqual(result.get('array_length'), 2)
    
    def test_analyze_invalid_file(self):
        """Test analysis of invalid/corrupt file"""
        # Create invalid CSV
        csv_path = Path(self.temp_dir) / 'invalid.csv'
        with open(csv_path, 'w') as f:
            f.write('invalid,csv,content\nwith"broken"quotes\n')
        
        # This should not crash
        result = self.analyzer.analyze_csv_file(csv_path)
        
        # Should either succeed or return error gracefully
        self.assertTrue('error' in result or 'columns' in result)


class TestSchemaMatcher(unittest.TestCase):
    """Test schema matching functionality"""
    
    def setUp(self):
        self.matcher = SchemaMatcher()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test schema config
        self.test_config = {
            'schemas': {
                'test_oceanographic': {
                    'name': 'Test Oceanographic',
                    'target_database': 'postgresql',
                    'required_fields': ['latitude', 'longitude', 'temperature'],
                    'optional_fields': ['salinity', 'depth'],
                    'field_patterns': [
                        'lat|latitude',
                        'lon|longitude', 
                        'temp|temperature',
                        'sal|salinity'
                    ],
                    'confidence_threshold': 70.0
                },
                'test_species': {
                    'name': 'Test Species',
                    'target_database': 'mongodb',
                    'required_fields': ['species_id', 'scientific_name'],
                    'optional_fields': ['common_name', 'kingdom'],
                    'field_patterns': [
                        'species.*id',
                        'scientific.*name',
                        'common.*name'
                    ],
                    'confidence_threshold': 65.0
                }
            },
            'field_mappings': {
                'coordinates': [
                    ['latitude', 'lat', 'coord_lat'],
                    ['longitude', 'lon', 'coord_lon']
                ]
            },
            'validation_rules': {
                'coordinates': {
                    'latitude': {'min': -90.0, 'max': 90.0},
                    'longitude': {'min': -180.0, 'max': 180.0}
                }
            }
        }
        
        # Mock the config loading
        self.matcher.schemas = self.test_config['schemas']
        self.matcher.field_mappings = self.test_config['field_mappings']
        self.matcher.validation_rules = self.test_config['validation_rules']
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_calculate_schema_confidence_exact_match(self):
        """Test confidence calculation with exact field matches"""
        file_fields = ['latitude', 'longitude', 'temperature', 'salinity']
        schema_config = self.test_config['schemas']['test_oceanographic']
        
        confidence = self.matcher._calculate_schema_confidence(file_fields, schema_config)
        
        # Should be high confidence due to exact matches
        self.assertGreater(confidence, 80.0)
    
    def test_calculate_schema_confidence_pattern_match(self):
        """Test confidence calculation with pattern matches"""
        file_fields = ['lat', 'lon', 'temp', 'sal']
        schema_config = self.test_config['schemas']['test_oceanographic']
        
        confidence = self.matcher._calculate_schema_confidence(file_fields, schema_config)
        
        # Should have reasonable confidence from pattern matches
        self.assertGreater(confidence, 50.0)
    
    def test_map_fields_direct(self):
        """Test direct field mapping"""
        file_fields = ['latitude', 'longitude', 'temperature']
        schema_config = self.test_config['schemas']['test_oceanographic']
        
        mappings = self.matcher._map_fields(file_fields, schema_config)
        
        self.assertEqual(mappings['latitude'], 'latitude')
        self.assertEqual(mappings['longitude'], 'longitude')
        self.assertEqual(mappings['temperature'], 'temperature')
    
    def test_map_fields_with_mappings(self):
        """Test field mapping using global mappings"""
        file_fields = ['lat', 'lon', 'temp']
        schema_config = self.test_config['schemas']['test_oceanographic']
        
        mappings = self.matcher._map_fields(file_fields, schema_config)
        
        # Should map through global field mappings
        self.assertEqual(mappings['lat'], 'latitude')
        self.assertEqual(mappings['lon'], 'longitude')
    
    def test_check_required_fields(self):
        """Test required field checking"""
        field_mappings = {
            'latitude': 'latitude',
            'longitude': 'longitude',
            'temperature': 'temperature'
        }
        schema_config = self.test_config['schemas']['test_oceanographic']
        
        required_check = self.matcher._check_required_fields(field_mappings, schema_config)
        
        # All required fields should be satisfied
        self.assertTrue(required_check['latitude'])
        self.assertTrue(required_check['longitude'])
        self.assertTrue(required_check['temperature'])
    
    def test_validate_data_valid(self):
        """Test data validation with valid data"""
        valid_data = {
            'latitude': 44.6,
            'longitude': -63.5,
            'temperature': 12.5
        }
        
        is_valid, errors = self.matcher.validate_data(valid_data, 'test_oceanographic')
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_data_invalid_coordinates(self):
        """Test data validation with invalid coordinates"""
        invalid_data = {
            'latitude': 95.0,  # Invalid latitude
            'longitude': -63.5,
            'temperature': 12.5
        }
        
        is_valid, errors = self.matcher.validate_data(invalid_data, 'test_oceanographic')
        
        self.assertFalse(is_valid)
        self.assertTrue(any('above maximum' in error for error in errors))
    
    def test_match_file_schema_csv(self):
        """Test complete schema matching workflow for CSV"""
        # Create test CSV
        test_data = {
            'lat': [44.6, 45.2],
            'lon': [-63.5, -62.8],
            'temp': [12.5, 14.2]
        }
        
        df = pd.DataFrame(test_data)
        csv_path = Path(self.temp_dir) / 'test.csv'
        df.to_csv(csv_path, index=False)
        
        with patch('scripts.schema_matcher.FileStructureAnalyzer') as mock_analyzer:
            mock_instance = Mock()
            mock_instance.analyze_csv_file.return_value = {
                'file_type': 'csv',
                'columns': ['lat', 'lon', 'temp'],
                'fields': {},
                'total_rows': 2
            }
            mock_analyzer.return_value = mock_instance
            
            matches = self.matcher.match_file_schema(str(csv_path))
            
            self.assertGreater(len(matches), 0)
            self.assertGreater(matches[0]['confidence'], 50.0)


class TestBasicSchemaDetection(unittest.TestCase):
    """Test fallback schema detection when config is unavailable"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('api.routes.data_ingestion.ingest_to_mongodb')
    def test_detect_edna_schema(self, mock_ingest):
        """Test detection of eDNA sequences"""
        mock_ingest.return_value = {'success': True, 'inserted_count': 1}
        
        # Create eDNA CSV
        test_data = {
            'sequence_id': ['seq_001'],
            'sequence': ['ATGCGATCGATCG'],
            'species_id': ['sp_001']
        }
        
        df = pd.DataFrame(test_data)
        csv_path = Path(self.temp_dir) / 'edna_test.csv'
        df.to_csv(csv_path, index=False)
        
        result = detect_schema_basic(str(csv_path), Mock())
        
        self.assertTrue(result['success'])
        self.assertEqual(result['schema_detected'], 'edna_sequences')
        self.assertEqual(result['confidence'], 75.0)
    
    @patch('api.routes.data_ingestion.ingest_to_postgresql')
    def test_detect_oceanographic_schema(self, mock_ingest):
        """Test detection of oceanographic data"""
        mock_ingest.return_value = {'success': True, 'records_inserted': 1}
        
        # Create oceanographic CSV
        test_data = {
            'temperature': [12.5],
            'salinity': [35.1],
            'depth': [10]
        }
        
        df = pd.DataFrame(test_data)
        csv_path = Path(self.temp_dir) / 'ocean_test.csv'
        df.to_csv(csv_path, index=False)
        
        result = detect_schema_basic(str(csv_path), Mock())
        
        self.assertTrue(result['success'])
        self.assertEqual(result['schema_detected'], 'oceanographic_data')
        self.assertEqual(result['confidence'], 75.0)


class TestFileUploadIntegration(unittest.TestCase):
    """Integration tests for file upload workflow"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('api.routes.data_ingestion.SchemaMatcher')
    @patch('api.routes.data_ingestion.ingest_to_postgresql')
    def test_process_uploaded_file_success(self, mock_ingest, mock_matcher_class):
        """Test successful file processing workflow"""
        # Setup mocks
        mock_matcher = Mock()
        mock_matcher.load_schemas.return_value = True
        mock_matcher.match_file_schema.return_value = [{
            'schema': 'oceanographic_data',
            'confidence': 85.0,
            'target_database': 'postgresql'
        }]
        mock_matcher_class.return_value = mock_matcher
        
        mock_ingest.return_value = {
            'success': True,
            'records_inserted': 5
        }
        
        # Create test file
        test_data = {
            'latitude': [44.6, 45.2],
            'longitude': [-63.5, -62.8],
            'temperature': [12.5, 14.2]
        }
        
        df = pd.DataFrame(test_data)
        csv_path = Path(self.temp_dir) / 'test_upload.csv'
        df.to_csv(csv_path, index=False)
        
        # Test processing
        result = process_uploaded_file('test_file_001', str(csv_path), Mock())
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['schema_detected'], 'oceanographic_data')
        self.assertEqual(result['confidence'], 85.0)
        self.assertIn('ingestion_results', result)
    
    @patch('api.routes.data_ingestion.detect_schema_basic')
    def test_process_uploaded_file_fallback(self, mock_fallback):
        """Test file processing with config file missing (fallback)"""
        mock_fallback.return_value = {
            'success': True,
            'schema_detected': 'species_data',
            'confidence': 70.0
        }
        
        # Create test file
        csv_path = Path(self.temp_dir) / 'test_fallback.csv'
        with open(csv_path, 'w') as f:
            f.write('species_id,scientific_name\nsp_001,Test species\n')
        
        # Test processing (config file won't exist)
        result = process_uploaded_file('test_file_002', str(csv_path), Mock())
        
        # Should use fallback
        mock_fallback.assert_called_once()
        self.assertTrue(result['success'])


if __name__ == '__main__':
    unittest.main(verbosity=2)