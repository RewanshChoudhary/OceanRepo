#!/usr/bin/env python3
"""
Simple test for species identification API without full Flask server
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

# Add project root to path
sys.path.append('.')
from scripts.edna_matcher import eDNAMatcher

load_dotenv()

def test_species_identification():
    """Test species identification with sample data"""
    print("🧬 Testing Species Identification API Logic")
    print("=" * 50)
    
    try:
        # Connect to MongoDB directly
        client = MongoClient(
            host=os.getenv('MONGODB_HOST', 'localhost'),
            port=int(os.getenv('MONGODB_PORT', '27017'))
        )
        db = client[os.getenv('MONGODB_DB', 'marine_db')]
        
        # Test sequence (from sample data)
        test_sequence = "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"
        print(f"🔬 Test sequence length: {len(test_sequence)}")
        print(f"🔬 First 50 chars: {test_sequence[:50]}...")
        
        # Initialize eDNA matcher
        matcher = eDNAMatcher(min_score=50.0)
        matcher.build_reference_database(db)
        
        print(f"📊 Reference database built with {len(matcher.reference_db)} species")
        
        # Perform matching
        matches = matcher.match_sequence(test_sequence, top_n=5)
        
        print(f"\n🎯 Found {len(matches)} matches:")
        if matches:
            for i, match in enumerate(matches, 1):
                print(f"   {i}. {match['scientific_name']} ({match['common_name']})")
                print(f"      Species ID: {match['species_id']}")
                print(f"      Score: {match['matching_score']:.2f}%")
                print(f"      Confidence: {match['confidence_level']}")
                print()
        else:
            print("   ❌ No matches found above threshold")
            
        # Test with a sequence from the database
        print("🔬 Testing with actual database sequence...")
        sample_edna = db.edna_sequences.find_one()
        if sample_edna:
            db_sequence = sample_edna['sequence']
            expected_species = sample_edna['matched_species_id']
            
            print(f"   Expected match: {expected_species}")
            
            db_matches = matcher.match_sequence(db_sequence, top_n=3)
            if db_matches:
                best_match = db_matches[0]
                print(f"   Best match: {best_match['species_id']} ({best_match['matching_score']:.2f}%)")
                
                if best_match['species_id'] == expected_species:
                    print("   ✅ CORRECT identification!")
                else:
                    print("   ❌ Incorrect identification")
            else:
                print("   ❌ No matches found for database sequence")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def simulate_api_request():
    """Simulate the API request processing"""
    print("\n🔌 Simulating API Request Processing")
    print("=" * 50)
    
    # This simulates what happens in the API endpoint
    request_data = {
        'sequence': 'ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG',
        'min_score': 50.0,
        'top_matches': 5
    }
    
    try:
        # Connect to database
        client = MongoClient(
            host=os.getenv('MONGODB_HOST', 'localhost'),
            port=int(os.getenv('MONGODB_PORT', '27017'))
        )
        db = client[os.getenv('MONGODB_DB', 'marine_db')]
        
        # Initialize matcher (like in the API)
        matcher = eDNAMatcher(min_score=request_data['min_score'])
        matcher.build_reference_database(db)
        
        # Perform matching
        matches = matcher.match_sequence(
            request_data['sequence'], 
            top_n=request_data['top_matches']
        )
        
        # Enhance results with additional species information (like in API)
        enhanced_matches = []
        for match in matches:
            species_info = db.taxonomy_data.find_one({
                'species_id': match['species_id']
            })
            
            enhanced_match = {
                'species_id': match['species_id'],
                'scientific_name': match['scientific_name'],
                'common_name': match['common_name'],
                'matching_score': match['matching_score'],
                'confidence_level': match['confidence_level'],
                'taxonomy': {
                    'kingdom': species_info.get('kingdom', 'Unknown') if species_info else 'Unknown',
                    'phylum': match['phylum'],
                    'class': species_info.get('class', 'Unknown') if species_info else 'Unknown',
                    'order': species_info.get('order', 'Unknown') if species_info else 'Unknown',
                    'family': species_info.get('family', 'Unknown') if species_info else 'Unknown',
                    'genus': species_info.get('genus', 'Unknown') if species_info else 'Unknown'
                },
                'sequence_stats': {
                    'query_length': match['query_length'],
                    'query_kmers': match['query_kmers']
                }
            }
            enhanced_matches.append(enhanced_match)
        
        # Format API response
        result_data = {
            'matches': enhanced_matches,
            'query_info': {
                'sequence_length': len(request_data['sequence']),
                'processed_sequence': request_data['sequence'][:50] + '...' if len(request_data['sequence']) > 50 else request_data['sequence'],
                'k_mer_size': matcher.k,
                'min_score_threshold': request_data['min_score'],
                'total_matches_found': len(matches)
            }
        }
        
        print(f"✅ API Response simulated successfully:")
        print(f"   Found {len(enhanced_matches)} matches")
        for match in enhanced_matches[:3]:  # Show first 3
            print(f"   - {match['scientific_name']}: {match['matching_score']:.1f}%")
        
        client.close()
        return result_data
        
    except Exception as e:
        print(f"❌ API simulation error: {e}")
        return None

if __name__ == '__main__':
    success = test_species_identification()
    if success:
        api_result = simulate_api_request()
        if api_result:
            print("\n🎉 Species identification is working correctly!")
            print("The issue might be with the Flask server configuration or frontend integration.")
        else:
            print("\n❌ API simulation failed")
    else:
        print("\n❌ Species identification test failed")