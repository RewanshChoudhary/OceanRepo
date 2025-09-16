#!/usr/bin/env python3
"""
Simple standalone API server for testing species identification
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

# Add project root to path
sys.path.append('.')
from scripts.edna_matcher import eDNAMatcher

load_dotenv()

app = Flask(__name__)
CORS(app)

# Global matcher instance
matcher = None
db = None

def init_matcher():
    """Initialize the eDNA matcher with database"""
    global matcher, db
    try:
        client = MongoClient(
            host=os.getenv('MONGODB_HOST', 'localhost'),
            port=int(os.getenv('MONGODB_PORT', '27017'))
        )
        db = client[os.getenv('MONGODB_DB', 'marine_db')]
        
        matcher = eDNAMatcher(min_score=30.0)  # Lower threshold for testing
        matcher.build_reference_database(db)
        
        print(f"✅ eDNA matcher initialized with {len(matcher.reference_db)} species")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize matcher: {e}")
        return False

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'matcher_ready': matcher is not None
    })

@app.route('/api/species/identify', methods=['POST'])
def identify_species():
    """Identify species from eDNA sequence"""
    try:
        if not matcher:
            return jsonify({
                'success': False,
                'message': 'eDNA matcher not initialized'
            }), 500
        
        data = request.get_json()
        if not data or 'sequence' not in data:
            return jsonify({
                'success': False,
                'message': 'No sequence provided'
            }), 400
        
        sequence = data['sequence'].strip().upper()
        min_score = data.get('min_score', 30.0)  # Lower default threshold
        top_matches = min(data.get('top_matches', 5), 20)
        
        # Validate sequence
        if not sequence:
            return jsonify({
                'success': False,
                'message': 'Empty sequence'
            }), 400
        
        valid_bases = set('ATGCN')
        if not all(base in valid_bases for base in sequence):
            return jsonify({
                'success': False,
                'message': 'Invalid DNA bases. Only A, T, G, C, N allowed'
            }), 400
        
        # Perform matching
        matches = matcher.match_sequence(sequence, top_n=top_matches)
        
        # Enhance matches with taxonomy info
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
                    'class': species_info.get('class', 'Unknown') if species_info else 'Unknown'
                }
            }
            enhanced_matches.append(enhanced_match)
        
        result = {
            'matches': enhanced_matches,
            'query_info': {
                'sequence_length': len(sequence),
                'min_score_threshold': min_score,
                'total_matches_found': len(matches)
            }
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Found {len(matches)} matches'
        })
        
    except Exception as e:
        print(f"Error in species identification: {e}")
        return jsonify({
            'success': False,
            'message': f'Species identification failed: {str(e)}'
        }), 500

@app.route('/api/species/sample-sequences')
def get_sample_sequences():
    """Get sample sequences for testing"""
    try:
        # Get 3 sample sequences from database
        samples = list(db.edna_sequences.find().limit(3))
        result = []
        
        for sample in samples:
            species_info = db.taxonomy_data.find_one({
                'species_id': sample['matched_species_id']
            })
            
            result.append({
                'sequence_id': sample['sequence_id'],
                'sequence': sample['sequence'],
                'species_id': sample['matched_species_id'],
                'species_name': species_info.get('species', 'Unknown') if species_info else 'Unknown',
                'common_name': species_info.get('common_name', 'Unknown') if species_info else 'Unknown'
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Retrieved {len(result)} sample sequences'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get sample sequences: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🌊 Starting Test API Server for Species Identification")
    print("=" * 60)
    
    if init_matcher():
        print("🚀 Server starting on http://localhost:5000")
        print("🔗 Test endpoints:")
        print("   - Health: http://localhost:5000/api/health")
        print("   - Identify: POST http://localhost:5000/api/species/identify")
        print("   - Samples: http://localhost:5000/api/species/sample-sequences")
        print()
        
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("❌ Failed to initialize server")
        sys.exit(1)