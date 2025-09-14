#!/usr/bin/env python3
"""
Marine Data Integration Platform - eDNA Sequence Matcher
K-mer based sequence matching algorithm for species identification
"""

import os
import sys
import json
from pymongo import MongoClient
from collections import defaultdict, Counter
from datetime import datetime, timezone
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class eDNAMatcher:
    def __init__(self, k=5, min_score=50.0):
        """
        Initialize eDNA matcher with k-mer parameters
        
        Args:
            k (int): K-mer length for sequence analysis
            min_score (float): Minimum matching score threshold
        """
        self.k = k
        self.min_score = min_score
        self.reference_db = {}
        self.species_info = {}
        
    def generate_kmers(self, sequence):
        """
        Generate k-mers from a DNA sequence
        
        Args:
            sequence (str): DNA sequence
            
        Returns:
            list: List of k-mers
        """
        sequence = sequence.upper().strip()
        kmers = []
        
        for i in range(len(sequence) - self.k + 1):
            kmer = sequence[i:i + self.k]
            # Only include k-mers with valid DNA bases
            if all(base in 'ATGC' for base in kmer):
                kmers.append(kmer)
                
        return kmers
    
    def build_reference_database(self, db):
        """
        Build k-mer reference database from MongoDB eDNA sequences
        
        Args:
            db: MongoDB database connection
        """
        print("🔬 Building k-mer reference database...")
        
        # Get reference sequences from MongoDB
        edna_collection = db.edna_sequences
        taxonomy_collection = db.taxonomy_data
        
        sequences = list(edna_collection.find())
        
        for seq_record in sequences:
            species_id = seq_record['matched_species_id']
            sequence = seq_record['sequence']
            
            # Generate k-mers for this sequence
            kmers = self.generate_kmers(sequence)
            
            if species_id not in self.reference_db:
                self.reference_db[species_id] = Counter()
                
            # Add k-mers to reference database
            for kmer in kmers:
                self.reference_db[species_id][kmer] += 1
            
            # Store species information
            if species_id not in self.species_info:
                species_data = taxonomy_collection.find_one({"species_id": species_id})
                if species_data:
                    self.species_info[species_id] = {
                        'scientific_name': species_data.get('species', 'Unknown'),
                        'common_name': species_data.get('common_name', 'Unknown'),
                        'phylum': species_data.get('phylum', 'Unknown')
                    }
        
        print(f"✅ Reference database built with {len(self.reference_db)} species")
        print(f"📊 Total k-mer profiles: {sum(len(kmers) for kmers in self.reference_db.values())}")
    
    def calculate_match_score(self, query_kmers, reference_kmers):
        """
        Calculate matching score between query and reference k-mers
        
        Args:
            query_kmers (Counter): Query k-mers
            reference_kmers (Counter): Reference k-mers
            
        Returns:
            float: Matching score (0-100)
        """
        if not query_kmers or not reference_kmers:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(set(query_kmers.keys()) & set(reference_kmers.keys()))
        union = len(set(query_kmers.keys()) | set(reference_kmers.keys()))
        
        if union == 0:
            return 0.0
            
        jaccard_score = (intersection / union) * 100
        
        # Weight by k-mer frequency similarity
        common_kmers = set(query_kmers.keys()) & set(reference_kmers.keys())
        frequency_score = 0.0
        
        if common_kmers:
            for kmer in common_kmers:
                q_freq = query_kmers[kmer]
                r_freq = reference_kmers[kmer]
                frequency_score += min(q_freq, r_freq) / max(q_freq, r_freq)
            
            frequency_score = (frequency_score / len(common_kmers)) * 100
            
            # Combine scores (weighted average)
            final_score = (jaccard_score * 0.7) + (frequency_score * 0.3)
        else:
            final_score = jaccard_score
            
        return final_score
    
    def match_sequence(self, query_sequence, top_n=5):
        """
        Match a query sequence against the reference database
        
        Args:
            query_sequence (str): DNA sequence to match
            top_n (int): Number of top matches to return
            
        Returns:
            list: List of match results
        """
        query_kmers = Counter(self.generate_kmers(query_sequence))
        
        if not query_kmers:
            return []
        
        matches = []
        
        for species_id, reference_kmers in self.reference_db.items():
            score = self.calculate_match_score(query_kmers, reference_kmers)
            
            if score >= self.min_score:
                species_info = self.species_info.get(species_id, {})
                
                match_result = {
                    'species_id': species_id,
                    'scientific_name': species_info.get('scientific_name', 'Unknown'),
                    'common_name': species_info.get('common_name', 'Unknown'),
                    'phylum': species_info.get('phylum', 'Unknown'),
                    'matching_score': round(score, 2),
                    'confidence_level': self.get_confidence_level(score),
                    'query_length': len(query_sequence),
                    'query_kmers': len(query_kmers)
                }
                
                matches.append(match_result)
        
        # Sort by matching score (descending)
        matches.sort(key=lambda x: x['matching_score'], reverse=True)
        
        return matches[:top_n]
    
    def get_confidence_level(self, score):
        """
        Determine confidence level based on matching score
        
        Args:
            score (float): Matching score
            
        Returns:
            str: Confidence level
        """
        if score >= 85:
            return "high"
        elif score >= 70:
            return "medium"
        elif score >= 50:
            return "low"
        else:
            return "very_low"
    
    def batch_match_sequences(self, sequences):
        """
        Match multiple sequences at once
        
        Args:
            sequences (list): List of sequences to match
            
        Returns:
            dict: Results for each sequence
        """
        results = {}
        
        for i, seq in enumerate(sequences):
            seq_id = f"seq_{i+1}"
            if isinstance(seq, dict) and 'sequence' in seq:
                sequence = seq['sequence']
                seq_id = seq.get('test_id', seq_id)
            else:
                sequence = seq
            
            matches = self.match_sequence(sequence)
            results[seq_id] = matches
            
        return results

def get_mongodb_connection():
    """Create MongoDB connection"""
    try:
        client = MongoClient(
            host=os.getenv('MONGODB_HOST', 'localhost'),
            port=int(os.getenv('MONGODB_PORT', '27017'))
        )
        db = client[os.getenv('MONGODB_DB', 'marine_db')]
        return client, db
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        return None, None

def load_test_sequences():
    """Load test sequences from JSON file"""
    try:
        with open('data/sample_sequences.json', 'r') as f:
            data = json.load(f)
            return data.get('test_sequences', [])
    except Exception as e:
        print(f"⚠️  Could not load test sequences: {e}")
        return []

def run_interactive_mode(matcher):
    """Run interactive sequence matching mode"""
    print("\n🧬 Interactive eDNA Sequence Matcher")
    print("=" * 50)
    print("Enter DNA sequences to match (or 'quit' to exit)")
    
    while True:
        try:
            sequence = input("\n🔬 Enter DNA sequence: ").strip()
            
            if sequence.lower() in ['quit', 'exit', 'q']:
                break
                
            if not sequence:
                continue
                
            if not all(base.upper() in 'ATGCN' for base in sequence):
                print("⚠️  Invalid sequence. Please use only A, T, G, C, N characters.")
                continue
            
            matches = matcher.match_sequence(sequence)
            
            print(f"\n🎯 Matching Results for sequence (length: {len(sequence)}):")
            print("-" * 40)
            
            if matches:
                for i, match in enumerate(matches, 1):
                    confidence_emoji = {
                        'high': '🟢', 'medium': '🟡', 'low': '🟠', 'very_low': '🔴'
                    }.get(match['confidence_level'], '⚪')
                    
                    print(f"{i}. {match['common_name']} ({match['scientific_name']})")
                    print(f"   Score: {match['matching_score']}% {confidence_emoji} {match['confidence_level'].upper()}")
                    print(f"   Phylum: {match['phylum']}")
                    print()
            else:
                print("❌ No matches found above threshold")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error processing sequence: {e}")
    
    print("\n👋 Exiting interactive mode")

def run_batch_test_mode(matcher):
    """Run batch testing with sample sequences"""
    print("\n🧪 Batch Testing Mode")
    print("=" * 50)
    
    test_sequences = load_test_sequences()
    
    if not test_sequences:
        print("❌ No test sequences found")
        return
    
    results = matcher.batch_match_sequences(test_sequences)
    
    print(f"📊 Testing {len(test_sequences)} sequences:")
    print("-" * 40)
    
    correct_predictions = 0
    total_predictions = 0
    
    for seq_id, matches in results.items():
        # Find corresponding test sequence info
        test_seq = next((s for s in test_sequences if s.get('test_id') == seq_id), {})
        expected_match = test_seq.get('expected_match')
        description = test_seq.get('description', 'Test sequence')
        
        print(f"\n🔬 {seq_id}: {description}")
        
        if matches:
            best_match = matches[0]
            print(f"   Best match: {best_match['common_name']} ({best_match['species_id']})")
            print(f"   Score: {best_match['matching_score']}% - {best_match['confidence_level'].upper()}")
            
            # Check accuracy if expected match is provided
            if expected_match:
                total_predictions += 1
                if best_match['species_id'] == expected_match:
                    print("   ✅ CORRECT prediction")
                    correct_predictions += 1
                else:
                    print(f"   ❌ INCORRECT - expected {expected_match}")
        else:
            print("   ❌ No matches found")
            if expected_match:
                total_predictions += 1
                print(f"   Expected: {expected_match}")
    
    # Calculate accuracy
    if total_predictions > 0:
        accuracy = (correct_predictions / total_predictions) * 100
        print(f"\n📈 Testing Results:")
        print(f"   Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")
        print(f"   Algorithm Performance: {'Good' if accuracy >= 80 else 'Needs Improvement'}")

def save_match_results(matches, output_file="edna_matches.json"):
    """Save matching results to JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(matches, f, indent=2, default=str)
        print(f"💾 Results saved to {output_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def main():
    """Main eDNA matcher function"""
    parser = argparse.ArgumentParser(description="eDNA Sequence Matcher")
    parser.add_argument('--mode', choices=['interactive', 'batch', 'test'], 
                       default='interactive', help='Matching mode')
    parser.add_argument('--k', type=int, default=5, help='K-mer size')
    parser.add_argument('--min-score', type=float, default=50.0, 
                       help='Minimum matching score')
    parser.add_argument('--sequence', type=str, help='Single sequence to match')
    parser.add_argument('--save', action='store_true', help='Save results to file')
    
    args = parser.parse_args()
    
    print("🌊 Marine Data Integration Platform - eDNA Matcher")
    print("=" * 60)
    
    # Connect to MongoDB
    mongo_client, db = get_mongodb_connection()
    if db is None:
        print("❌ Failed to connect to MongoDB")
        sys.exit(1)
    
    # Initialize matcher
    matcher = eDNAMatcher(k=args.k, min_score=args.min_score)
    
    try:
        # Build reference database
        matcher.build_reference_database(db)
        
        if args.sequence:
            # Single sequence mode
            matches = matcher.match_sequence(args.sequence)
            print(f"\n🎯 Results for input sequence:")
            for match in matches:
                print(f"   {match['common_name']}: {match['matching_score']}%")
            
            if args.save:
                save_match_results(matches)
                
        elif args.mode == 'interactive':
            run_interactive_mode(matcher)
            
        elif args.mode == 'batch' or args.mode == 'test':
            run_batch_test_mode(matcher)
            
        print("\n✨ eDNA matching completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during eDNA matching: {e}")
        sys.exit(1)
        
    finally:
        if mongo_client:
            mongo_client.close()

if __name__ == "__main__":
    main()