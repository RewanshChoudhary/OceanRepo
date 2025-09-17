#!/usr/bin/env python3
"""
Script to process uploaded files using the enhanced schema matcher.
This replaces directory scanning with database-driven file processing.
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from scripts.schema_matcher import SchemaMatchingOrchestrator
from api.utils.database import MongoDB

def setup_logging(log_level='INFO'):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Process uploaded marine data files')
    parser.add_argument('--status-filter', 
                       help='Filter files by status (uploaded, processed, etc.)')
    parser.add_argument('--upload-type-filter', 
                       choices=['edna', 'oceanographic', 'species', 'taxonomy'],
                       help='Filter files by upload type')
    parser.add_argument('--dry-run', action='store_true',
                       help='Analyze files without processing them')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    parser.add_argument('--show-details', action='store_true',
                       help='Show detailed processing results')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Configuration
    config = {
        'similarity_threshold': 0.6,
        'log_level': args.log_level,
        'console_logging': True
    }
    
    try:
        logger.info("Starting Marine Data Upload Processor")
        logger.info(f"Status filter: {args.status_filter}")
        logger.info(f"Upload type filter: {args.upload_type_filter}")
        logger.info(f"Dry run: {args.dry_run}")
        
        # Initialize schema matcher
        matcher = SchemaMatchingOrchestrator(config)
        
        # Run processing
        results = matcher.run_matching_on_uploads(
            status_filter=args.status_filter,
            upload_type_filter=args.upload_type_filter,
            process_matches=not args.dry_run
        )
        
        if 'error' in results:
            logger.error(f"Processing failed: {results['error']}")
            return 1
        
        # Display summary
        print("\n" + "="*60)
        print("UPLOAD PROCESSING SUMMARY")
        print("="*60)
        print(f"Processing timestamp: {results['timestamp']}")
        print(f"Files analyzed: {results['files_analyzed']}")
        print(f"Database schemas found: {results['schemas_found']}")
        
        if args.dry_run:
            print("\n🔍 DRY RUN - Files analyzed but not processed")
        else:
            processing_results = results.get('processing_results', [])
            successful = len([r for r in processing_results if r.get('success')])
            failed = len([r for r in processing_results if not r.get('success')])
            
            print(f"\n📊 PROCESSING RESULTS:")
            print(f"  ✅ Successfully processed: {successful}")
            print(f"  ❌ Failed processing: {failed}")
        
        # Show file matches
        matches = results.get('matches', {})
        if matches:
            print(f"\n📁 FILE MATCHES:")
            for file_id, match_info in matches.items():
                upload_info = match_info.get('upload_info', {})
                file_name = upload_info.get('original_filename', file_id)
                upload_type = upload_info.get('upload_type', 'unknown')
                
                print(f"\n  📄 {file_name} ({upload_type})")
                
                potential_matches = match_info.get('potential_matches', [])
                if potential_matches:
                    best_match = potential_matches[0]
                    print(f"    🎯 Best match: {best_match['schema_name']} "
                          f"(score: {best_match['match_score']:.1f})")
                    
                    if args.show_details and len(potential_matches) > 1:
                        print("    📝 Other matches:")
                        for match in potential_matches[1:3]:  # Show top 2 alternatives
                            print(f"      - {match['schema_name']} "
                                  f"(score: {match['match_score']:.1f})")
                else:
                    print("    ❌ No suitable matches found")
        
        # Show processing details if requested
        if args.show_details and not args.dry_run:
            processing_results = results.get('processing_results', [])
            if processing_results:
                print(f"\n🔄 DETAILED PROCESSING RESULTS:")
                for result in processing_results:
                    file_name = result.get('file_name', result.get('file_id', 'unknown'))
                    success = result.get('success', False)
                    
                    if success:
                        schema = result.get('schema_matched', 'unknown')
                        confidence = result.get('confidence', 0)
                        processing_result = result.get('processing_result', {})
                        
                        print(f"\n  ✅ {file_name}")
                        print(f"    Schema: {schema} ({confidence:.1f}% confidence)")
                        
                        if 'inserted_count' in processing_result:
                            print(f"    MongoDB records inserted: {processing_result['inserted_count']}")
                        elif 'records_inserted' in processing_result:
                            print(f"    PostgreSQL records inserted: {processing_result['records_inserted']}")
                    else:
                        error = result.get('error', 'Unknown error')
                        print(f"\n  ❌ {file_name}")
                        print(f"    Error: {error}")
        
        print(f"\n{'='*60}")
        logger.info("Processing completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)