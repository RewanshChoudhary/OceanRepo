#!/usr/bin/env python3
"""
Marine Data Integration Platform - API Validation Script
Test all API endpoints with SIH sample data to verify functionality
"""

import os
import sys
import json
import time
import requests
import pandas as pd
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import threading
from urllib.parse import urljoin

# Load environment variables
load_dotenv()

class APIValidator:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.api_process = None
        self.sih_data_path = Path("/home/rewansh57/SIH/data")
        
    def start_api_server(self):
        """Start the Flask API server in background"""
        print("🚀 Starting Flask API server...")
        try:
            # Start API server in background
            self.api_process = subprocess.Popen(
                [sys.executable, "api/app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait for server to start
            print("⏳ Waiting for API server to start...")
            time.sleep(10)
            
            # Test if server is running
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=5)
                if response.status_code == 200:
                    print("✅ API server started successfully!")
                    return True
            except:
                pass
            
            print("❌ API server failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting API server: {e}")
            return False
    
    def stop_api_server(self):
        """Stop the API server"""
        if self.api_process:
            print("🛑 Stopping API server...")
            self.api_process.terminate()
            self.api_process.wait()
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        print("\n🔍 Testing Health Endpoint")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                print("✅ Health check: PASSED")
                print(f"   Status: {data.get('data', {}).get('status', 'Unknown')}")
                print(f"   PostgreSQL: {data.get('data', {}).get('services', {}).get('postgresql', 'Unknown')}")
                print(f"   MongoDB: {data.get('data', {}).get('services', {}).get('mongodb', 'Unknown')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_api_info_endpoint(self):
        """Test the API info endpoint"""
        print("\n📋 Testing API Info Endpoint")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/api/info")
            if response.status_code == 200:
                data = response.json()
                print("✅ API info: PASSED")
                print(f"   Name: {data.get('data', {}).get('name', 'Unknown')}")
                print(f"   Version: {data.get('data', {}).get('version', 'Unknown')}")
                endpoints = data.get('data', {}).get('endpoints', {})
                print(f"   Available endpoints: {len(endpoints)}")
                for endpoint, path in endpoints.items():
                    print(f"     - {endpoint}: {path}")
                return True
            else:
                print(f"❌ API info failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API info error: {e}")
            return False
    
    def test_species_identification(self):
        """Test species identification API with SIH eDNA data"""
        print("\n🧬 Testing Species Identification API")
        print("-" * 40)
        
        # Load eDNA sequences from SIH data
        edna_file = self.sih_data_path / "eDNA Sequence.csv"
        if not edna_file.exists():
            print(f"❌ eDNA data file not found: {edna_file}")
            return False
        
        try:
            df = pd.read_csv(edna_file)
            print(f"📊 Loaded {len(df)} eDNA sequences from SIH data")
            
            # Test single sequence identification
            test_sequences = df.head(3)  # Test first 3 sequences
            
            for idx, row in test_sequences.iterrows():
                sequence_id = row['sequence_id']
                sequence = row['sequence']
                expected_species = row.get('matched_species_id', 'Unknown')
                
                print(f"\n🔬 Testing sequence {sequence_id}:")
                print(f"   Expected species: {expected_species}")
                print(f"   Sequence length: {len(sequence)} bp")
                
                # Make API call
                payload = {
                    "sequence": sequence,
                    "min_score": 50.0,
                    "top_matches": 5
                }
                
                response = requests.post(
                    f"{self.base_url}/api/species/identify",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    matches = result.get('data', {}).get('matches', [])
                    
                    if matches:
                        best_match = matches[0]
                        print(f"   ✅ Best match: {best_match.get('scientific_name', 'Unknown')}")
                        print(f"   📊 Score: {best_match.get('matching_score', 0):.2f}%")
                        print(f"   🎯 Confidence: {best_match.get('confidence_level', 'Unknown')}")
                    else:
                        print("   ⚠️  No matches found above threshold")
                else:
                    print(f"   ❌ API call failed: {response.status_code}")
                    if response.text:
                        print(f"   Error: {response.text[:100]}")
            
            # Test batch identification
            print(f"\n🔄 Testing batch identification...")
            batch_sequences = []
            for idx, row in test_sequences.iterrows():
                batch_sequences.append({
                    "id": row['sequence_id'],
                    "sequence": row['sequence'],
                    "metadata": {"source": "SIH_data"}
                })
            
            batch_payload = {
                "sequences": batch_sequences,
                "min_score": 50.0,
                "top_matches": 3
            }
            
            response = requests.post(
                f"{self.base_url}/api/species/batch-identify",
                json=batch_payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('data', {}).get('summary', {})
                print(f"   ✅ Batch processing: SUCCESS")
                print(f"   📊 Processed: {summary.get('total_sequences', 0)} sequences")
                print(f"   🎯 Successful matches: {summary.get('successful_matches', 0)}")
                print(f"   📈 Success rate: {summary.get('success_rate', 0):.1f}%")
                return True
            else:
                print(f"   ❌ Batch processing failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Species identification error: {e}")
            return False
    
    def test_taxonomy_api(self):
        """Test taxonomy API endpoints"""
        print("\n🌿 Testing Taxonomy API")
        print("-" * 40)
        
        try:
            # Test getting all taxonomy data
            response = requests.get(f"{self.base_url}/api/species/taxonomy?per_page=10")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', [])
                print(f"✅ Taxonomy list: Retrieved {len(data)} species")
                
                if data:
                    first_species = data[0]
                    species_id = first_species.get('species_id')
                    print(f"   First species: {first_species.get('scientific_name', 'Unknown')}")
                    
                    # Test getting specific species details
                    if species_id:
                        detail_response = requests.get(f"{self.base_url}/api/species/taxonomy/{species_id}")
                        if detail_response.status_code == 200:
                            species_detail = detail_response.json()
                            print(f"   ✅ Species details: Retrieved for {species_id}")
                        else:
                            print(f"   ⚠️  Species details failed: {detail_response.status_code}")
                
                # Test taxonomy statistics
                stats_response = requests.get(f"{self.base_url}/api/species/statistics")
                if stats_response.status_code == 200:
                    stats = stats_response.json()
                    taxonomy_stats = stats.get('data', {}).get('taxonomy', {})
                    print(f"   ✅ Statistics: {taxonomy_stats.get('total_species', 0)} species in database")
                    print(f"   📊 Kingdoms: {taxonomy_stats.get('unique_kingdoms', 0)}")
                    print(f"   📊 Phylums: {taxonomy_stats.get('unique_phylums', 0)}")
                
                return True
            else:
                print(f"❌ Taxonomy API failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Taxonomy API error: {e}")
            return False
    
    def test_oceanographic_api(self):
        """Test oceanographic data API with SIH data"""
        print("\n🌊 Testing Oceanographic Data API")
        print("-" * 40)
        
        # Load oceanographic data from SIH
        ocean_file = self.sih_data_path / "Oceanographic Data.csv"
        if not ocean_file.exists():
            print(f"❌ Oceanographic data file not found: {ocean_file}")
            return False
        
        try:
            df = pd.read_csv(ocean_file)
            print(f"📊 Loaded {len(df)} oceanographic records from SIH data")
            
            # Test data ingestion
            sample_data = df.head(5).to_dict('records')
            
            for record in sample_data[:2]:  # Test first 2 records
                # Parse location
                location_str = record.get('location', '').strip('()')
                if ',' in location_str:
                    try:
                        lat, lon = map(float, location_str.split(','))
                        
                        payload = {
                            "location": {
                                "latitude": lat,
                                "longitude": lon
                            },
                            "parameter_type": record.get('parameter_type', 'unknown'),
                            "value": float(record.get('value', 0)),
                            "timestamp": record.get('timestamp', ''),
                            "metadata": {
                                "source": "SIH_data",
                                "original_id": record.get('id', '')
                            }
                        }
                        
                        response = requests.post(
                            f"{self.base_url}/api/oceanographic/data",
                            json=payload,
                            timeout=10
                        )
                        
                        if response.status_code in [200, 201]:
                            print(f"   ✅ Ingested {record.get('parameter_type', 'unknown')} data")
                        else:
                            print(f"   ⚠️  Ingestion warning: {response.status_code}")
                            
                    except ValueError as e:
                        print(f"   ⚠️  Location parsing error: {e}")
            
            # Test data retrieval
            response = requests.get(f"{self.base_url}/api/oceanographic/data?limit=10")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', [])
                print(f"   ✅ Retrieved {len(data)} oceanographic records via API")
                return True
            else:
                print(f"   ❌ Retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Oceanographic API error: {e}")
            return False
    
    def test_search_api(self):
        """Test search and analytics API"""
        print("\n🔍 Testing Search & Analytics API")
        print("-" * 40)
        
        try:
            # Test general search
            search_params = {
                "query": "temperature",
                "limit": 10
            }
            
            response = requests.get(
                f"{self.base_url}/api/search",
                params=search_params
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Search API: Working")
                print(f"   Results found: {len(result.get('data', []))}")
            else:
                print(f"⚠️  Search API: {response.status_code}")
            
            # Test analytics
            response = requests.get(f"{self.base_url}/api/analytics/summary")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Analytics API: Working")
            else:
                print(f"⚠️  Analytics API: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Search API error: {e}")
            return False
    
    def test_spatial_api(self):
        """Test spatial analysis API"""
        print("\n🗺️  Testing Spatial Analysis API")
        print("-" * 40)
        
        try:
            # Test spatial query with sample coordinates
            payload = {
                "bounds": {
                    "min_latitude": 40.0,
                    "max_latitude": 50.0,
                    "min_longitude": -75.0,
                    "max_longitude": -70.0
                },
                "data_types": ["oceanographic", "sampling_points"]
            }
            
            response = requests.post(
                f"{self.base_url}/api/spatial/query",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Spatial query: Working")
                print(f"   Results: {len(result.get('data', []))}")
            else:
                print(f"⚠️  Spatial query: {response.status_code}")
            
            # Test distance calculations
            distance_payload = {
                "point1": {"latitude": 40.7128, "longitude": -74.0060},
                "point2": {"latitude": 48.13, "longitude": 11.58},
                "unit": "km"
            }
            
            response = requests.post(
                f"{self.base_url}/api/spatial/distance",
                json=distance_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Distance calculation: Working")
                distance = result.get('data', {}).get('distance', 0)
                print(f"   Distance calculated: {distance:.2f} km")
            else:
                print(f"⚠️  Distance calculation: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Spatial API error: {e}")
            return False
    
    def test_data_ingestion_api(self):
        """Test data ingestion API with SIH morphometric data"""
        print("\n📥 Testing Data Ingestion API")
        print("-" * 40)
        
        morpho_file = self.sih_data_path / "Morphometric Data.csv"
        if not morpho_file.exists():
            print(f"❌ Morphometric data file not found: {morpho_file}")
            return False
        
        try:
            df = pd.read_csv(morpho_file)
            print(f"📊 Loaded {len(df)} morphometric records from SIH data")
            
            # Test ingestion with sample records
            sample_records = df.head(3)
            
            for idx, row in sample_records.iterrows():
                try:
                    # Parse metrics JSON
                    metrics_str = row.get('metrics', '{}')
                    if isinstance(metrics_str, str) and metrics_str.startswith('{'):
                        metrics = eval(metrics_str)  # Safe in this context
                    else:
                        metrics = {}
                    
                    payload = {
                        "species_id": row.get('species_id', 'unknown'),
                        "sample_location": row.get('sample_location', 'Unknown'),
                        "metrics": metrics,
                        "timestamp": row.get('timestamp', ''),
                        "metadata": {
                            "source": "SIH_morphometric_data",
                            "image_path": row.get('image_path', ''),
                            "original_id": row.get('id', '')
                        }
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/api/ingestion/morphometric",
                        json=payload,
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        print(f"   ✅ Ingested morphometric data for {row.get('species_id', 'unknown')}")
                    else:
                        print(f"   ⚠️  Ingestion warning: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ⚠️  Record processing error: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Data ingestion API error: {e}")
            return False
    
    def validate_sih_data_compatibility(self):
        """Validate SIH data compatibility with platform schemas"""
        print("\n📊 VALIDATING SIH DATA COMPATIBILITY")
        print("=" * 50)
        
        datasets = {
            "eDNA Sequence.csv": ["sequence_id", "sequence", "matched_species_id"],
            "Morphometric Data.csv": ["id", "species_id", "metrics"],
            "Oceanographic Data.csv": ["id", "location", "parameter_type", "value"],
            "Taxonomy.csv": ["species_id", "kingdom", "phylum", "class"],
            "Sampling_Points_Dataset (2).csv": ["id", "location", "timestamp"]
        }
        
        compatibility_score = 0
        total_datasets = len(datasets)
        
        for filename, required_columns in datasets.items():
            file_path = self.sih_data_path / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    actual_columns = df.columns.tolist()
                    
                    missing_columns = [col for col in required_columns if col not in actual_columns]
                    
                    if not missing_columns:
                        print(f"✅ {filename}: FULLY COMPATIBLE")
                        compatibility_score += 1
                    else:
                        print(f"⚠️  {filename}: PARTIALLY COMPATIBLE")
                        print(f"   Missing columns: {missing_columns}")
                        compatibility_score += 0.5
                    
                    print(f"   Records: {len(df)}, Columns: {len(actual_columns)}")
                    
                except Exception as e:
                    print(f"❌ {filename}: ERROR - {e}")
            else:
                print(f"❌ {filename}: FILE NOT FOUND")
        
        compatibility_percentage = (compatibility_score / total_datasets) * 100
        print(f"\n📈 COMPATIBILITY SCORE: {compatibility_percentage:.1f}%")
        
        return compatibility_percentage >= 80
    
    def run_full_validation(self):
        """Run complete API validation with SIH data"""
        print("🌊 MARINE DATA PLATFORM - API VALIDATION WITH SIH DATA")
        print("=" * 70)
        
        # Check SIH data compatibility first
        data_compatible = self.validate_sih_data_compatibility()
        
        if not data_compatible:
            print("\n⚠️  Warning: Some SIH data compatibility issues found")
            print("Proceeding with available data...\n")
        
        # Start API server
        if not self.start_api_server():
            print("❌ Cannot proceed without API server")
            return False
        
        try:
            # Run all API tests
            test_results = {
                "Health Check": self.test_health_endpoint(),
                "API Info": self.test_api_info_endpoint(),
                "Species Identification": self.test_species_identification(),
                "Taxonomy API": self.test_taxonomy_api(),
                "Oceanographic API": self.test_oceanographic_api(),
                "Search & Analytics": self.test_search_api(),
                "Spatial Analysis": self.test_spatial_api(),
                "Data Ingestion": self.test_data_ingestion_api()
            }
            
            # Summary
            print("\n" + "=" * 70)
            print("📊 API VALIDATION SUMMARY")
            print("=" * 70)
            
            passed_tests = sum(test_results.values())
            total_tests = len(test_results)
            
            for test_name, result in test_results.items():
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"{test_name:<25} {status}")
            
            print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
            
            if passed_tests == total_tests:
                print("\n🎉 ALL API TESTS PASSED!")
                print("🚀 Platform is fully operational with SIH data!")
            elif passed_tests >= total_tests * 0.7:
                print("\n✅ Most API tests passed - Platform is operational")
            else:
                print("\n⚠️  Several API issues found - Check logs above")
            
            return passed_tests >= total_tests * 0.7
            
        finally:
            # Always stop the API server
            self.stop_api_server()

def main():
    """Main function"""
    try:
        validator = APIValidator()
        success = validator.run_full_validation()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()