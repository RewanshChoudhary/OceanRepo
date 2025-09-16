#!/usr/bin/env python3
"""
Unit Tests for eDNA Analysis
Tests the eDNA sequence matching, k-mer generation, and species identification
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from collections import Counter

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.edna_matcher import eDNAMatcher


class TesteDNAMatcher(unittest.TestCase):
    """Test eDNA sequence matching functionality"""
    
    def setUp(self):
        self.matcher = eDNAMatcher(k=5, min_score=50.0)
        
        # Mock reference database with test species
        self.matcher.reference_db = {
            'sp_001': Counter({
                'ATGCG': 3,
                'TGCGA': 2,
                'GCGAT': 2,
                'CGATC': 1,
                'GATCG': 1
            }),
            'sp_002': Counter({
                'CGATC': 4,
                'GATCG': 3,
                'ATCGA': 2,
                'TCGAT': 2,
                'CGATT': 1
            })
        }
        
        # Mock species information
        self.matcher.species_info = {
            'sp_001': {
                'scientific_name': 'Testicus species',
                'common_name': 'Test species 1',
                'phylum': 'Chordata'
            },
            'sp_002': {
                'scientific_name': 'Mockicus species',
                'common_name': 'Test species 2',
                'phylum': 'Arthropoda'
            }
        }
    
    def test_generate_kmers_valid_sequence(self):
        """Test k-mer generation with valid DNA sequence"""
        sequence = "ATGCGATCG"
        kmers = self.matcher.generate_kmers(sequence)
        
        expected_kmers = ['ATGCG', 'TGCGA', 'GCGAT', 'CGATC', 'GATCG']
        self.assertEqual(kmers, expected_kmers)
    
    def test_generate_kmers_invalid_bases(self):
        """Test k-mer generation with invalid DNA bases"""
        sequence = "ATGCXGATCG"  # X is invalid
        kmers = self.matcher.generate_kmers(sequence)
        
        # Should only return k-mers without invalid bases
        self.assertNotIn('TGCXG', kmers)
        self.assertNotIn('GCXGA', kmers)
        self.assertNotIn('CXGAT', kmers)
        self.assertNotIn('XGATC', kmers)
    
    def test_generate_kmers_short_sequence(self):
        """Test k-mer generation with sequence shorter than k"""
        sequence = "ATGC"  # Length 4, k=5
        kmers = self.matcher.generate_kmers(sequence)
        
        self.assertEqual(kmers, [])
    
    def test_generate_kmers_empty_sequence(self):
        """Test k-mer generation with empty sequence"""
        sequence = ""
        kmers = self.matcher.generate_kmers(sequence)
        
        self.assertEqual(kmers, [])
    
    def test_calculate_match_score_identical(self):
        """Test match score calculation with identical k-mer profiles"""
        query_kmers = Counter(['ATGCG', 'TGCGA', 'GCGAT'])
        reference_kmers = Counter(['ATGCG', 'TGCGA', 'GCGAT'])
        
        score = self.matcher.calculate_match_score(query_kmers, reference_kmers)
        
        # Should be 100% match
        self.assertEqual(score, 100.0)
    
    def test_calculate_match_score_partial_overlap(self):
        """Test match score calculation with partial overlap"""
        query_kmers = Counter(['ATGCG', 'TGCGA', 'GCGAT', 'CGATC'])
        reference_kmers = Counter(['ATGCG', 'TGCGA', 'XXXXX', 'YYYYY'])
        
        score = self.matcher.calculate_match_score(query_kmers, reference_kmers)
        
        # Should have moderate score due to partial overlap
        self.assertGreater(score, 0.0)
        self.assertLess(score, 100.0)
    
    def test_calculate_match_score_no_overlap(self):
        """Test match score calculation with no overlap"""
        query_kmers = Counter(['ATGCG', 'TGCGA', 'GCGAT'])
        reference_kmers = Counter(['XXXXX', 'YYYYY', 'ZZZZZ'])
        
        score = self.matcher.calculate_match_score(query_kmers, reference_kmers)
        
        # Should be 0% match
        self.assertEqual(score, 0.0)
    
    def test_calculate_match_score_empty_kmers(self):
        """Test match score calculation with empty k-mer sets"""
        query_kmers = Counter([])
        reference_kmers = Counter(['ATGCG', 'TGCGA'])
        
        score = self.matcher.calculate_match_score(query_kmers, reference_kmers)
        
        self.assertEqual(score, 0.0)
    
    def test_match_sequence_good_match(self):
        """Test sequence matching with good match"""
        # Sequence that should match sp_001 well
        sequence = "ATGCGATCG"  # Contains k-mers from sp_001
        
        matches = self.matcher.match_sequence(sequence, top_n=2)
        
        self.assertGreater(len(matches), 0)
        self.assertGreater(matches[0]['matching_score'], 50.0)
        self.assertEqual(matches[0]['species_id'], 'sp_001')
        self.assertIn('confidence_level', matches[0])
        self.assertIn('query_length', matches[0])
    
    def test_match_sequence_no_match(self):
        """Test sequence matching with no good matches"""
        # Sequence with k-mers not in reference database
        sequence = "AAAAAAAAAAA"
        
        matches = self.matcher.match_sequence(sequence, top_n=5)
        
        # Should return empty list due to low scores
        self.assertEqual(len(matches), 0)
    
    def test_match_sequence_top_n_limit(self):
        """Test sequence matching respects top_n parameter"""
        sequence = "ATGCGATCG"
        
        matches = self.matcher.match_sequence(sequence, top_n=1)
        
        # Should return at most 1 match
        self.assertLessEqual(len(matches), 1)
    
    def test_get_confidence_level(self):
        """Test confidence level categorization"""
        # Test high confidence
        self.assertEqual(self.matcher.get_confidence_level(90.0), "high")
        
        # Test medium confidence  
        self.assertEqual(self.matcher.get_confidence_level(75.0), "medium")
        
        # Test low confidence
        self.assertEqual(self.matcher.get_confidence_level(60.0), "low")
        
        # Test very low confidence
        self.assertEqual(self.matcher.get_confidence_level(40.0), "very_low")
    
    def test_batch_match_sequences_list_of_strings(self):
        """Test batch matching with list of sequence strings"""
        sequences = [
            "ATGCGATCG",
            "CGATCGATCG",
            "AAAAAAAAAAA"
        ]
        
        results = self.matcher.batch_match_sequences(sequences)
        
        self.assertEqual(len(results), 3)
        self.assertIn('seq_1', results)
        self.assertIn('seq_2', results)
        self.assertIn('seq_3', results)
    
    def test_batch_match_sequences_list_of_dicts(self):
        """Test batch matching with list of sequence dictionaries"""
        sequences = [
            {
                'test_id': 'test_seq_001',
                'sequence': 'ATGCGATCG',
                'description': 'Test sequence 1'
            },
            {
                'test_id': 'test_seq_002', 
                'sequence': 'CGATCGATCG',
                'description': 'Test sequence 2'
            }
        ]
        
        results = self.matcher.batch_match_sequences(sequences)
        
        self.assertEqual(len(results), 2)
        self.assertIn('test_seq_001', results)
        self.assertIn('test_seq_002', results)
    
    def test_batch_match_sequences_empty_list(self):
        """Test batch matching with empty sequence list"""
        sequences = []
        
        results = self.matcher.batch_match_sequences(sequences)
        
        self.assertEqual(len(results), 0)
    
    @patch('scripts.edna_matcher.MongoClient')
    def test_build_reference_database(self, mock_mongo_client):
        """Test building reference database from MongoDB"""
        # Mock MongoDB collections
        mock_db = Mock()
        mock_edna_collection = Mock()
        mock_taxonomy_collection = Mock()
        
        mock_db.edna_sequences = mock_edna_collection
        mock_db.taxonomy_data = mock_taxonomy_collection
        
        # Mock sequence data
        mock_sequences = [
            {
                'matched_species_id': 'test_sp_001',
                'sequence': 'ATGCGATCGATCG'
            },
            {
                'matched_species_id': 'test_sp_002',
                'sequence': 'CGATCGATCGATT'
            }
        ]
        mock_edna_collection.find.return_value = mock_sequences
        
        # Mock taxonomy data
        def mock_find_one(query):
            species_id = query['species_id']
            if species_id == 'test_sp_001':
                return {
                    'species_id': 'test_sp_001',
                    'species': 'Test species 1',
                    'common_name': 'Common test 1',
                    'phylum': 'Test phylum 1'
                }
            elif species_id == 'test_sp_002':
                return {
                    'species_id': 'test_sp_002',
                    'species': 'Test species 2',
                    'common_name': 'Common test 2',
                    'phylum': 'Test phylum 2'
                }
            return None
        
        mock_taxonomy_collection.find_one.side_effect = mock_find_one
        
        # Test building reference database
        fresh_matcher = eDNAMatcher()
        fresh_matcher.build_reference_database(mock_db)
        
        # Verify reference database was built
        self.assertIn('test_sp_001', fresh_matcher.reference_db)
        self.assertIn('test_sp_002', fresh_matcher.reference_db)
        self.assertIn('test_sp_001', fresh_matcher.species_info)
        self.assertIn('test_sp_002', fresh_matcher.species_info)
    
    def test_sequence_preprocessing(self):
        """Test sequence preprocessing (uppercasing, stripping)"""
        # Test lowercase sequence
        sequence = "atgcgatcg"
        kmers = self.matcher.generate_kmers(sequence)
        expected_kmers = ['ATGCG', 'TGCGA', 'GCGAT', 'CGATC', 'GATCG']
        self.assertEqual(kmers, expected_kmers)
        
        # Test sequence with whitespace
        sequence = "  ATGCGATCG  "
        kmers = self.matcher.generate_kmers(sequence)
        expected_kmers = ['ATGCG', 'TGCGA', 'GCGAT', 'CGATC', 'GATCG']
        self.assertEqual(kmers, expected_kmers)
    
    def test_min_score_filtering(self):
        """Test that results below min_score are filtered out"""
        # Create matcher with high minimum score
        high_threshold_matcher = eDNAMatcher(k=5, min_score=95.0)
        high_threshold_matcher.reference_db = self.matcher.reference_db
        high_threshold_matcher.species_info = self.matcher.species_info
        
        # Test with sequence that would normally match but below threshold
        sequence = "CGATCGATCG"  # Partial match
        
        matches = high_threshold_matcher.match_sequence(sequence, top_n=5)
        
        # Should return fewer or no matches due to high threshold
        self.assertLessEqual(len(matches), len(self.matcher.match_sequence(sequence, top_n=5)))


class TesteDNAIntegration(unittest.TestCase):
    """Integration tests for eDNA analysis workflow"""
    
    @patch('scripts.edna_matcher.MongoClient')
    def test_full_workflow_with_mock_db(self, mock_mongo_client):
        """Test complete eDNA analysis workflow with mocked database"""
        # Setup mock database
        mock_client = Mock()
        mock_db = Mock()
        mock_mongo_client.return_value = mock_client
        
        mock_edna_collection = Mock()
        mock_taxonomy_collection = Mock()
        mock_db.edna_sequences = mock_edna_collection
        mock_db.taxonomy_data = mock_taxonomy_collection
        
        # Mock data
        mock_sequences = [
            {
                'matched_species_id': 'integration_sp_001',
                'sequence': 'ATGCGATCGATCGATCGATCGATCG'
            }
        ]
        mock_edna_collection.find.return_value = mock_sequences
        
        mock_taxonomy_collection.find_one.return_value = {
            'species_id': 'integration_sp_001',
            'species': 'Integration testicus',
            'common_name': 'Integration test species',
            'phylum': 'Chordata'
        }
        
        # Initialize and test matcher
        matcher = eDNAMatcher()
        matcher.build_reference_database(mock_db)
        
        # Test sequence matching
        test_sequence = "ATGCGATCGATCGATCGATCGATCG"
        matches = matcher.match_sequence(test_sequence)
        
        # Verify workflow completed
        self.assertIsInstance(matches, list)
        if matches:  # If there are matches
            self.assertIn('species_id', matches[0])
            self.assertIn('scientific_name', matches[0])
            self.assertIn('matching_score', matches[0])
            self.assertIn('confidence_level', matches[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)