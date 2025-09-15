"""
Species Identification API Routes
Provides AI-powered species identification from eDNA sequences and taxonomy management
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from api.utils.database import PostgreSQLCursor, MongoDB
from api.utils.response import APIResponse
from scripts.edna_matcher import eDNAMatcher

species_bp = Blueprint('species', __name__)
logger = logging.getLogger(__name__)

@species_bp.route('/identify', methods=['POST'])
def identify_species():
    """
    Identify species from eDNA sequence using AI-powered k-mer matching
    
    POST /api/species/identify
    
    Request body:
    {
        "sequence": "ATGCGATCGATCG...",
        "min_score": 50.0,
        "top_matches": 5
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'sequence' not in data:
            return APIResponse.validation_error({
                'sequence': ['eDNA sequence is required']
            })
        
        sequence = data['sequence'].strip().upper()
        min_score = data.get('min_score', 50.0)
        top_matches = min(data.get('top_matches', 5), 20)  # Limit to max 20 results
        
        # Validate sequence format
        if not sequence:
            return APIResponse.validation_error({
                'sequence': ['Sequence cannot be empty']
            })
        
        # Check for valid DNA bases
        valid_bases = set('ATGCN')
        if not all(base in valid_bases for base in sequence):
            return APIResponse.validation_error({
                'sequence': ['Sequence contains invalid DNA bases. Only A, T, G, C, N are allowed']
            })
        
        # Initialize eDNA matcher
        with MongoDB() as db:
            if db is None:
                return APIResponse.server_error("Database connection failed")
            
            matcher = eDNAMatcher(min_score=min_score)
            matcher.build_reference_database(db)
            
            # Perform matching
            matches = matcher.match_sequence(sequence, top_n=top_matches)
            
            # Enhance results with additional species information
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
            
            result_data = {
                'matches': enhanced_matches,
                'query_info': {
                    'sequence_length': len(sequence),
                    'processed_sequence': sequence[:50] + '...' if len(sequence) > 50 else sequence,
                    'k_mer_size': matcher.k,
                    'min_score_threshold': min_score,
                    'total_matches_found': len(matches)
                },
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            if not matches:
                message = f"No species matches found above {min_score}% similarity threshold"
                return APIResponse.success(result_data, message)
            
            return APIResponse.success(result_data, f"Found {len(matches)} species matches")
            
    except Exception as e:
        logger.error(f"Species identification error: {e}")
        return APIResponse.server_error(f"Species identification failed: {str(e)}")

@species_bp.route('/batch-identify', methods=['POST'])
def batch_identify_species():
    """
    Batch identify multiple eDNA sequences
    
    POST /api/species/batch-identify
    
    Request body:
    {
        "sequences": [
            {
                "id": "seq1",
                "sequence": "ATGCGATC...",
                "metadata": {"sample_location": "Location A"}
            },
            {
                "id": "seq2", 
                "sequence": "CGATCGAT...",
                "metadata": {"sample_location": "Location B"}
            }
        ],
        "min_score": 50.0,
        "top_matches": 3
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'sequences' not in data:
            return APIResponse.validation_error({
                'sequences': ['Array of sequences is required']
            })
        
        sequences = data['sequences']
        min_score = data.get('min_score', 50.0)
        top_matches = min(data.get('top_matches', 3), 10)
        
        if not sequences or len(sequences) == 0:
            return APIResponse.validation_error({
                'sequences': ['At least one sequence is required']
            })
        
        if len(sequences) > 50:  # Limit batch size
            return APIResponse.validation_error({
                'sequences': ['Maximum 50 sequences allowed per batch']
            })
        
        # Initialize eDNA matcher
        with MongoDB() as db:
            if db is None:
                return APIResponse.server_error("Database connection failed")
            
            matcher = eDNAMatcher(min_score=min_score)
            matcher.build_reference_database(db)
            
            results = []
            
            for seq_data in sequences:
                seq_id = seq_data.get('id', f"seq_{len(results) + 1}")
                sequence = seq_data.get('sequence', '').strip().upper()
                metadata = seq_data.get('metadata', {})
                
                if not sequence:
                    results.append({
                        'id': seq_id,
                        'error': 'Empty sequence',
                        'matches': [],
                        'metadata': metadata
                    })
                    continue
                
                try:
                    matches = matcher.match_sequence(sequence, top_n=top_matches)
                    
                    results.append({
                        'id': seq_id,
                        'matches': matches,
                        'sequence_length': len(sequence),
                        'total_matches': len(matches),
                        'metadata': metadata,
                        'best_match': matches[0] if matches else None
                    })
                    
                except Exception as e:
                    results.append({
                        'id': seq_id,
                        'error': f'Processing failed: {str(e)}',
                        'matches': [],
                        'metadata': metadata
                    })
            
            # Calculate summary statistics
            successful_matches = sum(1 for r in results if 'error' not in r and r.get('total_matches', 0) > 0)
            total_sequences = len(results)
            
            summary = {
                'total_sequences': total_sequences,
                'successful_matches': successful_matches,
                'failed_sequences': total_sequences - successful_matches,
                'success_rate': (successful_matches / total_sequences * 100) if total_sequences > 0 else 0,
                'processing_timestamp': datetime.utcnow().isoformat()
            }
            
            return APIResponse.success({
                'results': results,
                'summary': summary
            }, f"Processed {total_sequences} sequences with {successful_matches} successful matches")
            
    except Exception as e:
        logger.error(f"Batch species identification error: {e}")
        return APIResponse.server_error(f"Batch identification failed: {str(e)}")

@species_bp.route('/taxonomy', methods=['GET'])
def get_taxonomy():
    """
    Get species taxonomy data with filtering and pagination
    
    GET /api/species/taxonomy?page=1&per_page=20&kingdom=Animalia&phylum=Chordata
    """
    try:
        # Get query parameters
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
        
        # Build filter query
        filter_query = {}
        
        # Taxonomic filters
        taxonomic_levels = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']
        for level in taxonomic_levels:
            value = request.args.get(level)
            if value:
                filter_query[level] = {'$regex': value, '$options': 'i'}
        
        # Search by common name
        common_name = request.args.get('common_name')
        if common_name:
            filter_query['common_name'] = {'$regex': common_name, '$options': 'i'}
        
        # Data source filter
        data_source = request.args.get('data_source')
        if data_source:
            filter_query['data_source'] = data_source
        
        with MongoDB() as db:
            if db is None:
                return APIResponse.server_error("Database connection failed")
            
            collection = db.taxonomy_data
            
            # Get total count for pagination
            total = collection.count_documents(filter_query)
            
            # Calculate skip value
            skip = (page - 1) * per_page
            
            # Get data with pagination
            cursor = collection.find(filter_query).skip(skip).limit(per_page)
            
            species_list = []
            for doc in cursor:
                species_data = {
                    'species_id': doc.get('species_id'),
                    'scientific_name': doc.get('species'),
                    'common_name': doc.get('common_name'),
                    'taxonomy': {
                        'kingdom': doc.get('kingdom'),
                        'phylum': doc.get('phylum'),
                        'class': doc.get('class'),
                        'order': doc.get('order'),
                        'family': doc.get('family'),
                        'genus': doc.get('genus')
                    },
                    'description': doc.get('description'),
                    'reference_link': doc.get('reference_link'),
                    'data_source': doc.get('data_source'),
                    'import_date': doc.get('import_date')
                }
                species_list.append(species_data)
            
            return APIResponse.paginated(
                data=species_list,
                page=page,
                per_page=per_page,
                total=total,
                message=f"Retrieved {len(species_list)} species records"
            )
            
    except Exception as e:
        logger.error(f"Taxonomy retrieval error: {e}")
        return APIResponse.server_error(f"Failed to retrieve taxonomy data: {str(e)}")

@species_bp.route('/taxonomy/<species_id>', methods=['GET'])
def get_species_details(species_id):
    """
    Get detailed information about a specific species
    
    GET /api/species/taxonomy/{species_id}
    """
    try:
        with MongoDB() as db:
            if db is None:
                return APIResponse.server_error("Database connection failed")
            
            # Get species taxonomy information
            species_doc = db.taxonomy_data.find_one({'species_id': species_id})
            
            if not species_doc:
                return APIResponse.not_found("Species")
            
            # Get related eDNA sequences
            edna_sequences = list(db.edna_sequences.find({
                'matched_species_id': species_id
            }).limit(10))
            
            # Build detailed response
            species_details = {
                'species_id': species_doc.get('species_id'),
                'scientific_name': species_doc.get('species'),
                'common_name': species_doc.get('common_name'),
                'taxonomy': {
                    'kingdom': species_doc.get('kingdom'),
                    'phylum': species_doc.get('phylum'),
                    'class': species_doc.get('class'),
                    'order': species_doc.get('order'),
                    'family': species_doc.get('family'),
                    'genus': species_doc.get('genus')
                },
                'description': species_doc.get('description'),
                'reference_link': species_doc.get('reference_link'),
                'data_source': species_doc.get('data_source'),
                'import_date': species_doc.get('import_date'),
                'edna_sequences': {
                    'count': len(edna_sequences),
                    'sequences': [{
                        'sequence_id': seq.get('sequence_id'),
                        'matching_score': seq.get('matching_score'),
                        'confidence_level': seq.get('confidence_level'),
                        'sample_location': seq.get('sample_location'),
                        'sequencing_method': seq.get('sequencing_method')
                    } for seq in edna_sequences]
                }
            }
            
            return APIResponse.success(
                species_details,
                f"Retrieved details for {species_details['common_name']}"
            )
            
    except Exception as e:
        logger.error(f"Species details retrieval error: {e}")
        return APIResponse.server_error(f"Failed to retrieve species details: {str(e)}")

@species_bp.route('/statistics', methods=['GET'])
def get_species_statistics():
    """
    Get statistics about the species database
    
    GET /api/species/statistics
    """
    try:
        with MongoDB() as db:
            if db is None:
                return APIResponse.server_error("Database connection failed")
            
            # Aggregate taxonomy statistics
            taxonomy_pipeline = [
                {
                    '$group': {
                        '_id': None,
                        'total_species': {'$sum': 1},
                        'kingdoms': {'$addToSet': '$kingdom'},
                        'phylums': {'$addToSet': '$phylum'},
                        'classes': {'$addToSet': '$class'},
                        'families': {'$addToSet': '$family'}
                    }
                }
            ]
            
            taxonomy_stats = list(db.taxonomy_data.aggregate(taxonomy_pipeline))
            
            # Get phylum distribution
            phylum_pipeline = [
                {
                    '$group': {
                        '_id': '$phylum',
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'count': -1}}
            ]
            
            phylum_distribution = list(db.taxonomy_data.aggregate(phylum_pipeline))
            
            # eDNA sequence statistics
            edna_stats = db.edna_sequences.count_documents({})
            
            # Confidence level distribution
            confidence_pipeline = [
                {
                    '$group': {
                        '_id': '$confidence_level',
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            confidence_distribution = list(db.edna_sequences.aggregate(confidence_pipeline))
            
            # Data source distribution
            source_pipeline = [
                {
                    '$group': {
                        '_id': '$data_source',
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            source_distribution = list(db.taxonomy_data.aggregate(source_pipeline))
            
            stats = {
                'taxonomy': {
                    'total_species': taxonomy_stats[0]['total_species'] if taxonomy_stats else 0,
                    'unique_kingdoms': len(taxonomy_stats[0]['kingdoms']) if taxonomy_stats else 0,
                    'unique_phylums': len(taxonomy_stats[0]['phylums']) if taxonomy_stats else 0,
                    'unique_classes': len(taxonomy_stats[0]['classes']) if taxonomy_stats else 0,
                    'unique_families': len(taxonomy_stats[0]['families']) if taxonomy_stats else 0,
                    'phylum_distribution': [
                        {'phylum': item['_id'], 'count': item['count']}
                        for item in phylum_distribution[:10]  # Top 10
                    ]
                },
                'edna_sequences': {
                    'total_sequences': edna_stats,
                    'confidence_distribution': [
                        {'confidence_level': item['_id'], 'count': item['count']}
                        for item in confidence_distribution
                    ]
                },
                'data_sources': [
                    {'source': item['_id'], 'count': item['count']}
                    for item in source_distribution
                ],
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return APIResponse.success(
                stats,
                "Retrieved species database statistics"
            )
            
    except Exception as e:
        logger.error(f"Statistics retrieval error: {e}")
        return APIResponse.server_error(f"Failed to retrieve statistics: {str(e)}")