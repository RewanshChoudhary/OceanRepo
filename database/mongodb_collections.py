"""
MongoDB Collections Setup for Marine Data Integration Platform
This script initializes MongoDB collections and inserts sample data
"""

import os
from pymongo import MongoClient
from datetime import datetime, timezone
import json


def setup_mongodb_collections(connection_string=None, db_name=None):
    if connection_string is None:
        connection_string = os.getenv('MONGO_CONNECTION', 'mongodb://localhost:27017/')
    if db_name is None:
        db_name = os.getenv('MONGO_DB', 'marine_db')
    """
    Initialize MongoDB collections with indexes and sample data
    """
    client = MongoClient(connection_string)
    db = client[db_name]
    
    # ===== Taxonomy Data Collection =====
    taxonomy_collection = db.taxonomy_data
    
    # Create indexes for efficient querying
    taxonomy_collection.create_index("species_id", unique=True)
    taxonomy_collection.create_index("kingdom")
    taxonomy_collection.create_index("phylum")
    taxonomy_collection.create_index("class")
    taxonomy_collection.create_index("family")
    taxonomy_collection.create_index("genus")
    taxonomy_collection.create_index("species")
    taxonomy_collection.create_index([("genus", 1), ("species", 1)])
    
    # Sample taxonomy data
    taxonomy_samples = [
        {
            "species_id": "sp_001",
            "kingdom": "Animalia",
            "phylum": "Chordata",
            "class": "Actinopterygii",
            "order": "Perciformes",
            "family": "Serranidae", 
            "genus": "Epinephelus",
            "species": "Epinephelus coioides",
            "common_name": "Orange-spotted grouper",
            "description": "Marine fish species found in Indian waters",
            "habitat": "Coral reefs and rocky areas",
            "conservation_status": "Near Threatened",
            "max_length_cm": 120,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "species_id": "sp_002",
            "kingdom": "Animalia", 
            "phylum": "Cnidaria",
            "class": "Anthozoa",
            "order": "Scleractinia",
            "family": "Acroporidae",
            "genus": "Acropora",
            "species": "Acropora digitifera",
            "common_name": "Finger coral",
            "description": "Branching hard coral species",
            "habitat": "Shallow tropical coral reefs",
            "conservation_status": "Vulnerable",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "species_id": "sp_003",
            "kingdom": "Animalia",
            "phylum": "Mollusca", 
            "class": "Cephalopoda",
            "order": "Sepiida",
            "family": "Sepiidae",
            "genus": "Sepia",
            "species": "Sepia pharaonis",
            "common_name": "Pharaoh cuttlefish",
            "description": "Large cuttlefish species in Indo-Pacific waters",
            "habitat": "Sandy and muddy bottoms",
            "max_length_cm": 42,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "species_id": "sp_004",
            "kingdom": "Plantae",
            "phylum": "Ochrophyta",
            "class": "Phaeophyceae", 
            "order": "Laminariales",
            "family": "Sargassaceae",
            "genus": "Sargassum",
            "species": "Sargassum wightii",
            "common_name": "Wight's sargassum",
            "description": "Brown seaweed species",
            "habitat": "Intertidal and subtidal rocky shores",
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    # Insert taxonomy data (avoid duplicates)
    for species in taxonomy_samples:
        taxonomy_collection.update_one(
            {"species_id": species["species_id"]},
            {"$set": species},
            upsert=True
        )
    
    # ===== eDNA Sequences Collection =====
    edna_collection = db.edna_sequences
    
    # Create indexes
    edna_collection.create_index("sequence_id", unique=True)
    edna_collection.create_index("matched_species_id")
    edna_collection.create_index("matching_score")
    edna_collection.create_index("sample_metadata.sample_date")
    edna_collection.create_index([("sample_metadata.location.lat", 1), ("sample_metadata.location.lon", 1)])
    
    # Sample eDNA sequences (simplified for demonstration)
    edna_samples = [
        {
            "sequence_id": "seq_001",
            "sequence": "AGTCGATCGTAGCTACGTAGCTAGCTACGTAGCTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGC",
            "matched_species_id": "sp_001", 
            "matching_score": 95.7,
            "sequence_length": 76,
            "sample_metadata": {
                "location": {"lat": 10.5, "lon": 76.2},
                "sample_date": datetime(2024, 9, 10),
                "depth_m": 15,
                "water_temperature": 29.5
            },
            "method": "k-mer matching",
            "confidence_level": "high",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "sequence_id": "seq_002", 
            "sequence": "TCGATCGAGTCGATCGAGTCGATCGAGTCGATCGAGTCGATCGAGTCGATCGAGTCGATCGAGTCGATCGAGTCG",
            "matched_species_id": "sp_002",
            "matching_score": 88.3,
            "sequence_length": 72,
            "sample_metadata": {
                "location": {"lat": 11.2, "lon": 75.8},
                "sample_date": datetime(2024, 9, 12),
                "depth_m": 8,
                "water_temperature": 28.9
            },
            "method": "k-mer matching",
            "confidence_level": "medium",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "sequence_id": "seq_003",
            "sequence": "GCTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACGT",
            "matched_species_id": "sp_003",
            "matching_score": 92.1,
            "sequence_length": 72,
            "sample_metadata": {
                "location": {"lat": 9.8, "lon": 76.5},
                "sample_date": datetime(2024, 9, 11),
                "depth_m": 25,
                "water_temperature": 27.8
            },
            "method": "k-mer matching", 
            "confidence_level": "high",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "sequence_id": "seq_004",
            "sequence": "CGATCGTAGCTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACGTAGCTACG",
            "matched_species_id": "sp_004",
            "matching_score": 79.5,
            "sequence_length": 70,
            "sample_metadata": {
                "location": {"lat": 12.1, "lon": 74.9},
                "sample_date": datetime(2024, 9, 13),
                "depth_m": 3,
                "water_temperature": 30.2
            },
            "method": "k-mer matching",
            "confidence_level": "low",
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    # Insert eDNA data
    for seq in edna_samples:
        edna_collection.update_one(
            {"sequence_id": seq["sequence_id"]},
            {"$set": seq},
            upsert=True
        )
    
    # ===== Research Studies Collection =====
    studies_collection = db.research_studies
    
    # Create indexes
    studies_collection.create_index("study_id", unique=True)
    studies_collection.create_index("principal_investigator")
    studies_collection.create_index("study_area.coordinates")
    studies_collection.create_index("start_date")
    studies_collection.create_index("study_type")
    
    # Sample research studies
    research_studies = [
        {
            "study_id": "study_001",
            "title": "Marine Biodiversity Assessment in Kerala Waters",
            "principal_investigator": "Dr. Marine Researcher",
            "institution": "Indian Institute of Marine Sciences",
            "study_type": "biodiversity_survey",
            "description": "Comprehensive assessment of marine species diversity along Kerala coast",
            "study_area": {
                "name": "Kerala Coast",
                "coordinates": [[75.5, 8.5], [77.0, 12.5]]
            },
            "start_date": datetime(2024, 6, 1),
            "end_date": datetime(2024, 12, 31),
            "funding_agency": "Ministry of Earth Sciences",
            "target_species": ["sp_001", "sp_002", "sp_003"],
            "sampling_methods": ["net_trawl", "scuba_diving", "edna_sampling"],
            "status": "ongoing",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "study_id": "study_002", 
            "title": "Climate Change Impact on Coral Reefs",
            "principal_investigator": "Dr. Coral Expert",
            "institution": "National Institute of Oceanography",
            "study_type": "climate_impact",
            "description": "Long-term monitoring of coral reef health under changing climate conditions",
            "study_area": {
                "name": "Lakshadweep Islands",
                "coordinates": [[71.0, 8.0], [74.0, 12.5]]
            },
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2026, 12, 31),
            "funding_agency": "Department of Science and Technology",
            "target_species": ["sp_002"],
            "sampling_methods": ["underwater_photography", "water_quality_monitoring"],
            "status": "ongoing",
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    # Insert research studies
    for study in research_studies:
        studies_collection.update_one(
            {"study_id": study["study_id"]},
            {"$set": study},
            upsert=True
        )
    
    print(f"✅ MongoDB collections initialized successfully!")
    print(f"📊 Taxonomy records: {taxonomy_collection.count_documents({})}")
    print(f"🧬 eDNA sequences: {edna_collection.count_documents({})}")
    print(f"📝 Research studies: {studies_collection.count_documents({})}")
    
    client.close()
    return True


if __name__ == "__main__":
    setup_mongodb_collections()