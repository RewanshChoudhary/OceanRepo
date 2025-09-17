#!/usr/bin/env python3
"""
Integration Tests for API Endpoints
Tests the complete API workflow including file upload, data processing, and eDNA analysis
"""

import os
import sys
import unittest
import tempfile
import json
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import io

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from api.app import create_app
from api.utils.response import APIResponse


class TestAPIEndpoints(unittest.TestCase):
    """Test API endpoint functionality"""
    
    def setUp(self):
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_health_check_endpoint(self):
        """Test the health check endpoint"""
        response = self.client.get('/api/health')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('status', data['data'])
        self.assertIn('timestamp', data['data'])
        self.assertIn('services', data['data'])
    
    def test_api_info_endpoint(self):
        """Test the API info endpoint"""
        response = self.client.get('/api/info')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('name', data['data'])
        self.assertIn('endpoints', data['data'])
        self.assertIn('version', data['data'])
    
    @patch('api.routes.data_ingestion.MongoDB')
    @patch('api.routes.data_ingestion.process_uploaded_file')
    def test_file_upload_success(self, mock_process, mock_mongodb):
        """Test successful file upload"""
        mock_process.return_value = {
            'success': True,
            'schema_detected': 'oceanographic_data',
            'confidence': 85.0,
            'ingestion_results': [{'success': True, 'records_inserted': 5}]
        }
        
        mock_db = Mock()
        mock_mongodb.return_value.__enter__.return_value = mock_db
        mock_db.uploaded_files.insert_one.return_value = Mock(inserted_id='test_id')
        mock_db.uploaded_files.update_one.return_value = Mock()
        
        # Create test CSV data
        csv_data = "latitude,longitude,temperature\n44.6,-63.5,12.5\n45.2,-62.8,14.2\n"
        
        response = self.client.post('/api/ingestion/upload', 
                                  data={
                                      'file': (io.BytesIO(csv_data.encode()), 'test.csv'),
                                      'description': 'Test upload',
                                      'auto_process': 'true'
                                  },
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('file_id', data['data'])
        self.assertIn('processing_results', data['data'])
    
    def test_file_upload_no_file(self):
        """Test file upload with no file provided"""
        response = self.client.post('/api/ingestion/upload', data={})
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('validation_errors', data)
    
    def test_file_upload_invalid_extension(self):
        """Test file upload with invalid file extension"""
        response = self.client.post('/api/ingestion/upload',
                                  data={
                                      'file': (io.BytesIO(b'invalid content'), 'test.xyz')
                                  },
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('validation_errors', data)
    
    @patch('api.routes.data_ingestion.MongoDB')
    def test_get_uploaded_files(self, mock_mongodb):
        """Test retrieving uploaded files list"""
        mock_db = Mock()
        mock_mongodb.return_value.__enter__.return_value = mock_db
        
        # Mock file documents
        mock_files = [
            {
                'file_id': 'test_001',
                'original_filename': 'test.csv',
                'status': 'processed',
                'upload_timestamp': '2024-01-01T00:00:00Z'
            }
        ]
        
        mock_db.uploaded_files.count_documents.return_value = 1
        mock_db.uploaded_files.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_files
        
        response = self.client.get('/api/ingestion/files')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('metadata', data)
        self.assertIn('pagination', data['metadata'])
    
    @patch('api.routes.data_ingestion.MongoDB')
    def test_get_file_details(self, mock_mongodb):
        """Test retrieving specific file details"""
        mock_db = Mock()
        mock_mongodb.return_value.__enter__.return_value = mock_db
        
        mock_file = {
            'file_id': 'test_001',
            'original_filename': 'test.csv',
            'status': 'processed',
            'processing_results': {'success': True},
            'file_path': '/tmp/test.csv'
        }
        
        mock_db.uploaded_files.find_one.return_value = mock_file
        
        response = self.client.get('/api/ingestion/files/test_001')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['file_id'], 'test_001')
    
    def test_get_supported_schemas(self):
        """Test retrieving supported schemas"""
        response = self.client.get('/api/ingestion/schemas')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('oceanographic_data', data['data'])
        self.assertIn('species_data', data['data'])
        self.assertIn('edna_sequences', data['data'])
    
    @patch('api.routes.species_identification.MongoDB')
    @patch('api.routes.species_identification.eDNAMatcher')
    def test_species_identification(self, mock_edna_matcher, mock_mongodb):
        """Test eDNA species identification endpoint"""
        # Mock database
        mock_db = Mock()
        mock_mongodb.return_value.__enter__.return_value = mock_db
        
        # Mock eDNA matcher
        mock_matcher_instance = Mock()
        mock_edna_matcher.return_value = mock_matcher_instance
        
        # Mock matcher attributes to be JSON serializable
        mock_matcher_instance.k = 8  # Return integer instead of Mock
        mock_matcher_instance.min_score = 50.0
        
        mock_matches = [
            {
                'species_id': 'sp_001',
                'scientific_name': 'Test species',
                'common_name': 'Test fish',
                'matching_score': 85.5,
                'confidence_level': 'high',
                'phylum': 'Chordata',
                'query_length': 100,
                'query_kmers': 96
            }
        ]
        
        mock_matcher_instance.match_sequence.return_value = mock_matches
        mock_db.taxonomy_data.find_one.return_value = {
            'kingdom': 'Animalia',
            'class': 'Actinopterygii'
        }
        
        test_sequence = "ATGCGATCGATCGATCGATCGATCG"
        
        response = self.client.post('/api/species/identify',
                                  data=json.dumps({
                                      'sequence': test_sequence,
                                      'min_score': 50.0,
                                      'top_matches': 5
                                  }),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('matches', data['data'])
        self.assertEqual(len(data['data']['matches']), 1)
        self.assertEqual(data['data']['matches'][0]['species_id'], 'sp_001')
    
    def test_species_identification_invalid_sequence(self):
        """Test species identification with invalid sequence"""
        response = self.client.post('/api/species/identify',
                                  data=json.dumps({
                                      'sequence': 'ATGCXYZ123',  # Invalid bases
                                      'min_score': 50.0
                                  }),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('validation_errors', data)
    
    def test_species_identification_no_sequence(self):
        """Test species identification with no sequence provided"""
        response = self.client.post('/api/species/identify',
                                  data=json.dumps({
                                      'min_score': 50.0
                                  }),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('validation_errors', data)
    
    @patch('api.routes.species_identification.MongoDB')
    @patch('api.routes.species_identification.eDNAMatcher')
    def test_batch_species_identification(self, mock_edna_matcher, mock_mongodb):
        """Test batch eDNA species identification"""
        # Mock database
        mock_db = Mock()
        mock_mongodb.return_value.__enter__.return_value = mock_db
        
        # Mock eDNA matcher
        mock_matcher_instance = Mock()
        mock_edna_matcher.return_value = mock_matcher_instance
        
        def mock_match_sequence(sequence, top_n=3):
            if 'ATGC' in sequence:
                return [{'species_id': 'sp_001', 'matching_score': 80.0}]
            else:
                return []
        
        mock_matcher_instance.match_sequence.side_effect = mock_match_sequence
        
        test_sequences = [
            {
                'id': 'seq_001',
                'sequence': 'ATGCGATCGATCG',
                'metadata': {'sample_location': 'Test location'}
            },
            {
                'id': 'seq_002',
                'sequence': 'AAAAAAAAAAAAAA',
                'metadata': {'sample_location': 'Test location 2'}
            }
        ]
        
        response = self.client.post('/api/species/batch-identify',
                                  data=json.dumps({
                                      'sequences': test_sequences,
                                      'min_score': 50.0,
                                      'top_matches': 3
                                  }),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('results', data['data'])
        self.assertIn('summary', data['data'])
        self.assertEqual(len(data['data']['results']), 2)
    
    @patch('api.routes.species_identification.MongoDB')
    def test_get_taxonomy_data(self, mock_mongodb):
        """Test retrieving taxonomy data"""
        mock_db = Mock()
        mock_mongodb.return_value.__enter__.return_value = mock_db
        
        mock_species = [
            {
                'species_id': 'sp_001',
                'species': 'Test species',
                'common_name': 'Test fish',
                'kingdom': 'Animalia',
                'phylum': 'Chordata'
            }
        ]
        
        mock_db.taxonomy_data.count_documents.return_value = 1
        mock_db.taxonomy_data.find.return_value.skip.return_value.limit.return_value = mock_species
        
        response = self.client.get('/api/species/taxonomy')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('metadata', data)
        self.assertIn('pagination', data['metadata'])
    
    @patch('api.routes.species_identification.MongoDB')
    def test_get_species_details(self, mock_mongodb):
        """Test retrieving specific species details"""
        mock_db = Mock()
        mock_mongodb.return_value.__enter__.return_value = mock_db
        
        mock_species = {
            'species_id': 'sp_001',
            'species': 'Test species',
            'common_name': 'Test fish',
            'kingdom': 'Animalia'
        }
        
        mock_edna_sequences = [
            {
                'sequence_id': 'seq_001',
                'matching_score': 90.0,
                'confidence_level': 'high'
            }
        ]
        
        mock_db.taxonomy_data.find_one.return_value = mock_species
        mock_db.edna_sequences.find.return_value.limit.return_value = mock_edna_sequences
        
        response = self.client.get('/api/species/taxonomy/sp_001')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['species_id'], 'sp_001')
        self.assertIn('edna_sequences', data['data'])
    
    @patch('api.routes.species_identification.MongoDB')
    def test_get_species_statistics(self, mock_mongodb):
        """Test retrieving species database statistics"""
        mock_db = Mock()
        mock_mongodb.return_value.__enter__.return_value = mock_db
        
        # Mock multiple aggregation results using side_effect
        def mock_aggregate(pipeline):
            # First aggregation (taxonomy statistics)
            if pipeline and pipeline[0].get('$group', {}).get('_id') is None:
                return [
                    {
                        '_id': None,
                        'total_species': 100,
                        'kingdoms': ['Animalia', 'Plantae'],
                        'phylums': ['Chordata', 'Tracheophyta'],
                        'classes': ['Actinopterygii'],
                        'families': ['Gadidae']
                    }
                ]
            # Phylum distribution
            elif pipeline and pipeline[0].get('$group', {}).get('_id') == '$phylum':
                return [
                    {'_id': 'Chordata', 'count': 50},
                    {'_id': 'Tracheophyta', 'count': 30}
                ]
            # Source distribution
            elif pipeline and pipeline[0].get('$group', {}).get('_id') == '$data_source':
                return [
                    {'_id': 'NCBI', 'count': 60},
                    {'_id': 'BOLD', 'count': 40}
                ]
            else:
                return []
        
        mock_db.taxonomy_data.aggregate.side_effect = mock_aggregate
        
        # Mock eDNA sequence aggregation
        def mock_edna_aggregate(pipeline):
            if pipeline and pipeline[0].get('$group', {}).get('_id') == '$confidence_level':
                return [
                    {'_id': 'high', 'count': 120},
                    {'_id': 'medium', 'count': 60},
                    {'_id': 'low', 'count': 20}
                ]
            return []
        
        mock_db.edna_sequences.aggregate.side_effect = mock_edna_aggregate
        mock_db.edna_sequences.count_documents.return_value = 200
        
        response = self.client.get('/api/species/statistics')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('taxonomy', data['data'])
        self.assertIn('edna_sequences', data['data'])


class TestAPIResponseUtil(unittest.TestCase):
    """Test API response utility functions"""
    
    def setUp(self):
        self.app = create_app({'TESTING': True})
    
    def test_success_response(self):
        """Test successful API response creation"""
        data = {'test': 'data'}
        message = 'Test success'
        
        with self.app.app_context():
            response = APIResponse.success(data, message)
        
        self.assertEqual(response[1], 200)  # Status code
        response_data = json.loads(response[0].data)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data'], data)
        self.assertEqual(response_data['message'], message)
        self.assertIn('timestamp', response_data)
    
    def test_error_response(self):
        """Test error API response creation"""
        message = 'Test error'
        
        with self.app.app_context():
            response = APIResponse.error(message, status_code=400)
        
        self.assertEqual(response[1], 400)  # Status code
        response_data = json.loads(response[0].data)
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], message)
        self.assertIn('timestamp', response_data)
    
    def test_validation_error_response(self):
        """Test validation error API response creation"""
        errors = {
            'field1': ['Error 1', 'Error 2'],
            'field2': ['Error 3']
        }
        
        with self.app.app_context():
            response = APIResponse.validation_error(errors)
        
        self.assertEqual(response[1], 400)  # Status code
        response_data = json.loads(response[0].data)
        self.assertFalse(response_data['success'])
        self.assertIn('validation_errors', response_data)
        self.assertEqual(response_data['validation_errors'], errors)
    
    def test_paginated_response(self):
        """Test paginated API response creation"""
        data = [{'item': 1}, {'item': 2}]
        page = 1
        per_page = 10
        total = 25
        message = 'Test pagination'
        
        with self.app.app_context():
            response = APIResponse.paginated(data, page, per_page, total, message)
        
        self.assertEqual(response[1], 200)  # Status code
        response_data = json.loads(response[0].data)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['data'], data)
        self.assertIn('metadata', response_data)
        self.assertIn('pagination', response_data['metadata'])
        
        pagination = response_data['metadata']['pagination']
        self.assertEqual(pagination['page'], page)
        self.assertEqual(pagination['per_page'], per_page)
        self.assertEqual(pagination['total'], total)
        self.assertEqual(pagination['pages'], 3)  # ceil(25/10)


if __name__ == '__main__':
    unittest.main(verbosity=2)