// Marine Data Integration Platform - MongoDB Schema
// Collection definitions and index creation for NoSQL marine data storage

// Use the marine platform database
use('marine_platform');

// =====================================================
// COLLECTION SCHEMA DEFINITIONS
// =====================================================

// Taxonomy Data Collection
// Stores comprehensive species taxonomy and classification information
db.createCollection('taxonomy_data', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["species_id", "scientific_name", "data_source", "import_date"],
            properties: {
                species_id: {
                    bsonType: "string",
                    description: "Unique identifier for the species",
                    maxLength: 50
                },
                scientific_name: {
                    bsonType: "string",
                    description: "Scientific/binomial name of the species",
                    maxLength: 255
                },
                common_name: {
                    bsonType: ["string", "null"],
                    description: "Common name(s) of the species",
                    maxLength: 255
                },
                authority: {
                    bsonType: ["string", "null"],
                    description: "Taxonomic authority who first described the species",
                    maxLength: 255
                },
                taxonomic_status: {
                    bsonType: "string",
                    enum: ["ACCEPTED", "SYNONYM", "UNRESOLVED", "PROVISIONAL"],
                    description: "Current taxonomic status"
                },
                taxonomy: {
                    bsonType: "object",
                    description: "Complete taxonomic hierarchy",
                    properties: {
                        kingdom: { bsonType: ["string", "null"], maxLength: 100 },
                        phylum: { bsonType: ["string", "null"], maxLength: 100 },
                        class: { bsonType: ["string", "null"], maxLength: 100 },
                        order: { bsonType: ["string", "null"], maxLength: 100 },
                        family: { bsonType: ["string", "null"], maxLength: 100 },
                        genus: { bsonType: ["string", "null"], maxLength: 100 },
                        species: { bsonType: ["string", "null"], maxLength: 100 },
                        subspecies: { bsonType: ["string", "null"], maxLength: 100 }
                    }
                },
                conservation_status: {
                    bsonType: ["object", "null"],
                    description: "Conservation and protection status",
                    properties: {
                        iucn_status: { 
                            bsonType: ["string", "null"], 
                            enum: [null, "LC", "NT", "VU", "EN", "CR", "EW", "EX", "DD", "NE"]
                        },
                        cites_status: { bsonType: ["string", "null"], maxLength: 20 },
                        national_status: { bsonType: ["string", "null"], maxLength: 100 },
                        regional_status: { bsonType: ["string", "null"], maxLength: 100 }
                    }
                },
                ecological_info: {
                    bsonType: ["object", "null"],
                    description: "Ecological and environmental information",
                    properties: {
                        habitat_type: { bsonType: ["string", "null"], maxLength: 100 },
                        depth_range: {
                            bsonType: ["object", "null"],
                            properties: {
                                min_meters: { bsonType: ["number", "null"], minimum: 0 },
                                max_meters: { bsonType: ["number", "null"], minimum: 0 }
                            }
                        },
                        temperature_range: {
                            bsonType: ["object", "null"],
                            properties: {
                                min_celsius: { bsonType: ["number", "null"] },
                                max_celsius: { bsonType: ["number", "null"] }
                            }
                        },
                        salinity_range: {
                            bsonType: ["object", "null"],
                            properties: {
                                min_psu: { bsonType: ["number", "null"], minimum: 0 },
                                max_psu: { bsonType: ["number", "null"], minimum: 0 }
                            }
                        },
                        geographic_distribution: { bsonType: ["string", "null"] },
                        feeding_type: { bsonType: ["string", "null"], maxLength: 100 },
                        trophic_level: { bsonType: ["number", "null"], minimum: 1, maximum: 5 },
                        body_size: {
                            bsonType: ["object", "null"],
                            properties: {
                                length_mm: { bsonType: ["number", "null"], minimum: 0 },
                                weight_g: { bsonType: ["number", "null"], minimum: 0 }
                            }
                        }
                    }
                },
                reference_info: {
                    bsonType: ["object", "null"],
                    description: "Reference and source information",
                    properties: {
                        reference_source: { bsonType: ["string", "null"], maxLength: 255 },
                        reference_url: { bsonType: ["string", "null"] },
                        reference_doi: { bsonType: ["string", "null"], maxLength: 255 },
                        authors: { bsonType: ["array", "null"], items: { bsonType: "string" } },
                        publication_year: { bsonType: ["int", "null"], minimum: 1700, maximum: 2030 }
                    }
                },
                data_source: {
                    bsonType: "string",
                    description: "Source database or organization",
                    maxLength: 100
                },
                confidence_level: {
                    bsonType: "string",
                    enum: ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
                    description: "Confidence in the taxonomic information"
                },
                genetic_info: {
                    bsonType: ["object", "null"],
                    description: "Genetic and molecular information",
                    properties: {
                        genome_size_bp: { bsonType: ["long", "null"], minimum: 0 },
                        chromosome_count: { bsonType: ["int", "null"], minimum: 1 },
                        mitochondrial_genes: { bsonType: ["array", "null"] },
                        genetic_markers: { bsonType: ["array", "null"] }
                    }
                },
                images: {
                    bsonType: ["array", "null"],
                    description: "Associated images and media",
                    items: {
                        bsonType: "object",
                        properties: {
                            url: { bsonType: "string" },
                            type: { bsonType: "string", enum: ["photograph", "illustration", "microscopy"] },
                            license: { bsonType: ["string", "null"] },
                            caption: { bsonType: ["string", "null"] }
                        }
                    }
                },
                import_date: {
                    bsonType: "date",
                    description: "Date when the record was imported"
                },
                last_modified: {
                    bsonType: ["date", "null"],
                    description: "Last modification date"
                },
                last_verified: {
                    bsonType: ["date", "null"],
                    description: "Last verification date"
                },
                metadata: {
                    bsonType: ["object", "null"],
                    description: "Additional flexible metadata"
                }
            }
        }
    }
});

// eDNA Sequences Collection
// Stores environmental DNA sequences and analysis results
db.createCollection('edna_sequences', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["sequence_id", "sequence", "import_date"],
            properties: {
                sequence_id: {
                    bsonType: "string",
                    description: "Unique identifier for the DNA sequence",
                    maxLength: 100
                },
                sequence: {
                    bsonType: "string",
                    pattern: "^[ATGCNRYSWKMBDHV-]+$",
                    description: "DNA sequence using IUPAC notation"
                },
                sequence_info: {
                    bsonType: ["object", "null"],
                    description: "Sequence characteristics",
                    properties: {
                        length: { bsonType: "int", minimum: 1 },
                        gc_content: { bsonType: ["number", "null"], minimum: 0, maximum: 1 },
                        quality_scores: { bsonType: ["array", "null"] },
                        primer_info: {
                            bsonType: ["object", "null"],
                            properties: {
                                forward_primer: { bsonType: ["string", "null"] },
                                reverse_primer: { bsonType: ["string", "null"] },
                                target_gene: { bsonType: ["string", "null"] },
                                amplicon_length: { bsonType: ["int", "null"] }
                            }
                        }
                    }
                },
                sampling_info: {
                    bsonType: ["object", "null"],
                    description: "Sampling context information",
                    properties: {
                        sample_id: { bsonType: ["string", "null"], maxLength: 100 },
                        sampling_point_id: { bsonType: ["string", "null"], maxLength: 100 },
                        sampling_event_id: { bsonType: ["string", "null"], maxLength: 100 },
                        location: {
                            bsonType: ["object", "null"],
                            description: "GeoJSON Point",
                            properties: {
                                type: { bsonType: "string", enum: ["Point"] },
                                coordinates: {
                                    bsonType: "array",
                                    items: { bsonType: "number" },
                                    minItems: 2,
                                    maxItems: 3
                                }
                            }
                        },
                        collection_date: { bsonType: ["date", "null"] },
                        depth_meters: { bsonType: ["number", "null"], minimum: 0 },
                        water_type: { 
                            bsonType: ["string", "null"],
                            enum: [null, "freshwater", "brackish", "marine", "hypersaline"]
                        },
                        habitat_description: { bsonType: ["string", "null"] }
                    }
                },
                laboratory_info: {
                    bsonType: ["object", "null"],
                    description: "Laboratory processing information",
                    properties: {
                        extraction_method: { bsonType: ["string", "null"], maxLength: 255 },
                        amplification_method: { bsonType: ["string", "null"], maxLength: 255 },
                        sequencing_platform: { 
                            bsonType: ["string", "null"],
                            enum: [null, "Illumina", "PacBio", "Oxford Nanopore", "454", "Ion Torrent", "Sanger"]
                        },
                        sequencing_date: { bsonType: ["date", "null"] },
                        library_preparation: { bsonType: ["string", "null"] },
                        barcode_sequence: { bsonType: ["string", "null"] },
                        processing_lab: { bsonType: ["string", "null"], maxLength: 255 },
                        technician: { bsonType: ["string", "null"], maxLength: 255 }
                    }
                },
                taxonomic_assignment: {
                    bsonType: ["object", "null"],
                    description: "Taxonomic identification results",
                    properties: {
                        matched_species_id: { bsonType: ["string", "null"], maxLength: 50 },
                        scientific_name: { bsonType: ["string", "null"], maxLength: 255 },
                        common_name: { bsonType: ["string", "null"], maxLength: 255 },
                        taxonomy: {
                            bsonType: ["object", "null"],
                            properties: {
                                kingdom: { bsonType: ["string", "null"] },
                                phylum: { bsonType: ["string", "null"] },
                                class: { bsonType: ["string", "null"] },
                                order: { bsonType: ["string", "null"] },
                                family: { bsonType: ["string", "null"] },
                                genus: { bsonType: ["string", "null"] },
                                species: { bsonType: ["string", "null"] }
                            }
                        },
                        matching_score: { bsonType: ["number", "null"], minimum: 0, maximum: 100 },
                        confidence_level: {
                            bsonType: ["string", "null"],
                            enum: [null, "LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
                        },
                        assignment_method: { bsonType: ["string", "null"], maxLength: 100 },
                        reference_database: { bsonType: ["string", "null"], maxLength: 100 },
                        alternative_matches: {
                            bsonType: ["array", "null"],
                            items: {
                                bsonType: "object",
                                properties: {
                                    species_id: { bsonType: "string" },
                                    scientific_name: { bsonType: "string" },
                                    matching_score: { bsonType: "number" }
                                }
                            }
                        }
                    }
                },
                quality_control: {
                    bsonType: ["object", "null"],
                    description: "Quality control metrics",
                    properties: {
                        contamination_check: { bsonType: ["bool", "null"] },
                        chimera_check: { bsonType: ["bool", "null"] },
                        quality_score: { bsonType: ["number", "null"], minimum: 0, maximum: 100 },
                        length_filter_passed: { bsonType: ["bool", "null"] },
                        abundance_filter_passed: { bsonType: ["bool", "null"] },
                        manual_review_status: {
                            bsonType: ["string", "null"],
                            enum: [null, "PENDING", "APPROVED", "REJECTED", "NEEDS_REVIEW"]
                        },
                        reviewer: { bsonType: ["string", "null"], maxLength: 255 },
                        review_date: { bsonType: ["date", "null"] },
                        qc_flags: {
                            bsonType: ["array", "null"],
                            items: { bsonType: "string" }
                        }
                    }
                },
                analysis_results: {
                    bsonType: ["object", "null"],
                    description: "Additional analysis results",
                    properties: {
                        abundance_count: { bsonType: ["int", "null"], minimum: 0 },
                        relative_abundance: { bsonType: ["number", "null"], minimum: 0, maximum: 1 },
                        diversity_indices: {
                            bsonType: ["object", "null"],
                            properties: {
                                shannon: { bsonType: ["number", "null"] },
                                simpson: { bsonType: ["number", "null"] },
                                chao1: { bsonType: ["number", "null"] }
                            }
                        },
                        blast_results: {
                            bsonType: ["array", "null"],
                            items: {
                                bsonType: "object",
                                properties: {
                                    hit_id: { bsonType: "string" },
                                    e_value: { bsonType: "number" },
                                    bit_score: { bsonType: "number" },
                                    identity_percent: { bsonType: "number" },
                                    coverage_percent: { bsonType: "number" }
                                }
                            }
                        }
                    }
                },
                import_date: {
                    bsonType: "date",
                    description: "Date when the sequence was imported"
                },
                last_modified: {
                    bsonType: ["date", "null"],
                    description: "Last modification date"
                },
                data_source: {
                    bsonType: ["string", "null"],
                    description: "Original source of the sequence data",
                    maxLength: 100
                },
                metadata: {
                    bsonType: ["object", "null"],
                    description: "Additional flexible metadata"
                }
            }
        }
    }
});

// Uploaded Files Collection
// Tracks all uploaded files and their processing status
db.createCollection('uploaded_files', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["file_id", "original_filename", "upload_timestamp", "status"],
            properties: {
                file_id: {
                    bsonType: "string",
                    description: "Unique identifier for the uploaded file",
                    maxLength: 255
                },
                original_filename: {
                    bsonType: "string",
                    description: "Original filename as uploaded",
                    maxLength: 255
                },
                file_info: {
                    bsonType: ["object", "null"],
                    description: "File characteristics",
                    properties: {
                        file_size: { bsonType: "long", minimum: 0 },
                        file_type: { bsonType: ["string", "null"], maxLength: 50 },
                        mime_type: { bsonType: ["string", "null"], maxLength: 100 },
                        encoding: { bsonType: ["string", "null"], maxLength: 50 },
                        checksum_md5: { bsonType: ["string", "null"], maxLength: 32 },
                        checksum_sha256: { bsonType: ["string", "null"], maxLength: 64 }
                    }
                },
                storage_info: {
                    bsonType: ["object", "null"],
                    description: "Storage location information",
                    properties: {
                        file_path: { bsonType: ["string", "null"] },
                        storage_backend: { 
                            bsonType: ["string", "null"],
                            enum: [null, "local", "s3", "gcs", "azure"]
                        },
                        backup_locations: {
                            bsonType: ["array", "null"],
                            items: { bsonType: "string" }
                        },
                        retention_policy: { bsonType: ["string", "null"] },
                        expiry_date: { bsonType: ["date", "null"] }
                    }
                },
                upload_info: {
                    bsonType: ["object", "null"],
                    description: "Upload context",
                    properties: {
                        uploader_id: { bsonType: ["string", "null"], maxLength: 100 },
                        uploader_name: { bsonType: ["string", "null"], maxLength: 255 },
                        upload_method: { 
                            bsonType: ["string", "null"],
                            enum: [null, "web_form", "api", "batch_upload", "ftp"]
                        },
                        client_ip: { bsonType: ["string", "null"], maxLength: 45 },
                        user_agent: { bsonType: ["string", "null"] }
                    }
                },
                processing_info: {
                    bsonType: ["object", "null"],
                    description: "File processing information",
                    properties: {
                        schema_matches: {
                            bsonType: ["array", "null"],
                            items: {
                                bsonType: "object",
                                properties: {
                                    schema_name: { bsonType: "string" },
                                    confidence_score: { bsonType: "number", minimum: 0, maximum: 100 },
                                    matched_fields: { bsonType: "array" },
                                    validation_errors: { bsonType: ["array", "null"] }
                                }
                            }
                        },
                        processing_attempts: { bsonType: ["int", "null"], minimum: 0 },
                        last_processing_attempt: { bsonType: ["date", "null"] },
                        processing_duration_seconds: { bsonType: ["number", "null"], minimum: 0 },
                        records_processed: { bsonType: ["int", "null"], minimum: 0 },
                        records_inserted: { bsonType: ["int", "null"], minimum: 0 },
                        records_failed: { bsonType: ["int", "null"], minimum: 0 }
                    }
                },
                status: {
                    bsonType: "string",
                    enum: ["uploaded", "queued", "processing", "processed", "failed", "archived"],
                    description: "Current processing status"
                },
                description: {
                    bsonType: ["string", "null"],
                    description: "User-provided description",
                    maxLength: 1000
                },
                tags: {
                    bsonType: ["array", "null"],
                    items: { bsonType: "string", maxLength: 50 },
                    description: "User-defined tags for organization"
                },
                upload_timestamp: {
                    bsonType: "date",
                    description: "When the file was uploaded"
                },
                processed_timestamp: {
                    bsonType: ["date", "null"],
                    description: "When processing completed"
                },
                error_log: {
                    bsonType: ["array", "null"],
                    items: {
                        bsonType: "object",
                        properties: {
                            timestamp: { bsonType: "date" },
                            error_type: { bsonType: "string" },
                            error_message: { bsonType: "string" },
                            stack_trace: { bsonType: ["string", "null"] }
                        }
                    }
                },
                metadata: {
                    bsonType: ["object", "null"],
                    description: "Additional file metadata"
                }
            }
        }
    }
});

// Analysis Results Collection
// Stores results from various analytical processes
db.createCollection('analysis_results', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["analysis_id", "analysis_type", "created_date"],
            properties: {
                analysis_id: {
                    bsonType: "string",
                    description: "Unique identifier for the analysis",
                    maxLength: 100
                },
                analysis_type: {
                    bsonType: "string",
                    enum: ["species_identification", "biodiversity_analysis", "spatial_analysis", 
                           "temporal_analysis", "correlation_analysis", "clustering_analysis"],
                    description: "Type of analysis performed"
                },
                input_data: {
                    bsonType: ["object", "null"],
                    description: "Information about input data",
                    properties: {
                        data_sources: { bsonType: ["array", "null"] },
                        date_range: {
                            bsonType: ["object", "null"],
                            properties: {
                                start_date: { bsonType: ["date", "null"] },
                                end_date: { bsonType: ["date", "null"] }
                            }
                        },
                        spatial_extent: {
                            bsonType: ["object", "null"],
                            description: "GeoJSON Polygon",
                            properties: {
                                type: { bsonType: "string", enum: ["Polygon"] },
                                coordinates: { bsonType: "array" }
                            }
                        },
                        filter_criteria: { bsonType: ["object", "null"] }
                    }
                },
                parameters: {
                    bsonType: ["object", "null"],
                    description: "Analysis parameters and configuration"
                },
                results: {
                    bsonType: ["object", "null"],
                    description: "Analysis results and outputs"
                },
                quality_metrics: {
                    bsonType: ["object", "null"],
                    description: "Quality and confidence metrics",
                    properties: {
                        confidence_score: { bsonType: ["number", "null"], minimum: 0, maximum: 1 },
                        p_value: { bsonType: ["number", "null"] },
                        r_squared: { bsonType: ["number", "null"] },
                        sample_size: { bsonType: ["int", "null"] }
                    }
                },
                created_date: {
                    bsonType: "date",
                    description: "When the analysis was created"
                },
                created_by: {
                    bsonType: ["string", "null"],
                    description: "User who created the analysis",
                    maxLength: 255
                },
                computation_info: {
                    bsonType: ["object", "null"],
                    description: "Computational details",
                    properties: {
                        processing_time_seconds: { bsonType: ["number", "null"] },
                        algorithm_version: { bsonType: ["string", "null"] },
                        computing_environment: { bsonType: ["string", "null"] },
                        memory_usage_mb: { bsonType: ["number", "null"] }
                    }
                },
                metadata: {
                    bsonType: ["object", "null"],
                    description: "Additional analysis metadata"
                }
            }
        }
    }
});

// =====================================================
// INDEXES FOR PERFORMANCE
// =====================================================

print("Creating indexes for taxonomy_data collection...");

// Taxonomy Data Indexes
db.taxonomy_data.createIndex({ "species_id": 1 }, { unique: true, name: "idx_species_id_unique" });
db.taxonomy_data.createIndex({ "scientific_name": 1 }, { name: "idx_scientific_name" });
db.taxonomy_data.createIndex({ "common_name": 1 }, { name: "idx_common_name" });
db.taxonomy_data.createIndex({ 
    "taxonomy.kingdom": 1, 
    "taxonomy.phylum": 1, 
    "taxonomy.class": 1, 
    "taxonomy.order": 1, 
    "taxonomy.family": 1, 
    "taxonomy.genus": 1 
}, { name: "idx_taxonomy_hierarchy" });
db.taxonomy_data.createIndex({ "data_source": 1 }, { name: "idx_data_source" });
db.taxonomy_data.createIndex({ "confidence_level": 1 }, { name: "idx_confidence_level" });
db.taxonomy_data.createIndex({ "conservation_status.iucn_status": 1 }, { name: "idx_iucn_status" });
db.taxonomy_data.createIndex({ "ecological_info.habitat_type": 1 }, { name: "idx_habitat_type" });
db.taxonomy_data.createIndex({ "import_date": 1 }, { name: "idx_import_date" });
db.taxonomy_data.createIndex({ "last_modified": 1 }, { name: "idx_last_modified" });

// Text index for full-text search
db.taxonomy_data.createIndex({ 
    "scientific_name": "text", 
    "common_name": "text", 
    "taxonomy.kingdom": "text",
    "taxonomy.phylum": "text",
    "taxonomy.class": "text",
    "taxonomy.family": "text",
    "taxonomy.genus": "text"
}, { name: "idx_taxonomy_text_search" });

print("Creating indexes for edna_sequences collection...");

// eDNA Sequences Indexes
db.edna_sequences.createIndex({ "sequence_id": 1 }, { unique: true, name: "idx_sequence_id_unique" });
db.edna_sequences.createIndex({ "taxonomic_assignment.matched_species_id": 1 }, { name: "idx_matched_species_id" });
db.edna_sequences.createIndex({ "taxonomic_assignment.scientific_name": 1 }, { name: "idx_assigned_scientific_name" });
db.edna_sequences.createIndex({ "taxonomic_assignment.matching_score": 1 }, { name: "idx_matching_score" });
db.edna_sequences.createIndex({ "taxonomic_assignment.confidence_level": 1 }, { name: "idx_sequence_confidence" });
db.edna_sequences.createIndex({ "sampling_info.sample_id": 1 }, { name: "idx_sample_id" });
db.edna_sequences.createIndex({ "sampling_info.sampling_point_id": 1 }, { name: "idx_sampling_point_id" });
db.edna_sequences.createIndex({ "sampling_info.sampling_event_id": 1 }, { name: "idx_sampling_event_id" });
db.edna_sequences.createIndex({ "sampling_info.collection_date": 1 }, { name: "idx_collection_date" });
db.edna_sequences.createIndex({ "sampling_info.depth_meters": 1 }, { name: "idx_sampling_depth" });
db.edna_sequences.createIndex({ "laboratory_info.sequencing_platform": 1 }, { name: "idx_sequencing_platform" });
db.edna_sequences.createIndex({ "laboratory_info.sequencing_date": 1 }, { name: "idx_sequencing_date" });
db.edna_sequences.createIndex({ "quality_control.quality_score": 1 }, { name: "idx_quality_score" });
db.edna_sequences.createIndex({ "quality_control.manual_review_status": 1 }, { name: "idx_review_status" });
db.edna_sequences.createIndex({ "data_source": 1 }, { name: "idx_sequence_data_source" });
db.edna_sequences.createIndex({ "import_date": 1 }, { name: "idx_sequence_import_date" });

// Geospatial index for location queries
db.edna_sequences.createIndex({ "sampling_info.location": "2dsphere" }, { name: "idx_sampling_location_geo" });

// Compound indexes for common query patterns
db.edna_sequences.createIndex({ 
    "taxonomic_assignment.matched_species_id": 1, 
    "taxonomic_assignment.matching_score": -1 
}, { name: "idx_species_score" });

db.edna_sequences.createIndex({ 
    "sampling_info.collection_date": 1, 
    "sampling_info.depth_meters": 1 
}, { name: "idx_date_depth" });

print("Creating indexes for uploaded_files collection...");

// Uploaded Files Indexes
db.uploaded_files.createIndex({ "file_id": 1 }, { unique: true, name: "idx_file_id_unique" });
db.uploaded_files.createIndex({ "status": 1 }, { name: "idx_file_status" });
db.uploaded_files.createIndex({ "upload_timestamp": 1 }, { name: "idx_upload_timestamp" });
db.uploaded_files.createIndex({ "processed_timestamp": 1 }, { name: "idx_processed_timestamp" });
db.uploaded_files.createIndex({ "upload_info.uploader_id": 1 }, { name: "idx_uploader_id" });
db.uploaded_files.createIndex({ "file_info.file_type": 1 }, { name: "idx_file_type" });
db.uploaded_files.createIndex({ "file_info.file_size": 1 }, { name: "idx_file_size" });
db.uploaded_files.createIndex({ "tags": 1 }, { name: "idx_file_tags" });

// Text index for filename and description search
db.uploaded_files.createIndex({ 
    "original_filename": "text", 
    "description": "text" 
}, { name: "idx_file_text_search" });

print("Creating indexes for analysis_results collection...");

// Analysis Results Indexes
db.analysis_results.createIndex({ "analysis_id": 1 }, { unique: true, name: "idx_analysis_id_unique" });
db.analysis_results.createIndex({ "analysis_type": 1 }, { name: "idx_analysis_type" });
db.analysis_results.createIndex({ "created_date": 1 }, { name: "idx_analysis_created_date" });
db.analysis_results.createIndex({ "created_by": 1 }, { name: "idx_analysis_created_by" });
db.analysis_results.createIndex({ "quality_metrics.confidence_score": 1 }, { name: "idx_analysis_confidence" });

// Geospatial index for spatial analyses
db.analysis_results.createIndex({ "input_data.spatial_extent": "2dsphere" }, { name: "idx_analysis_spatial_extent" });

// =====================================================
// ADDITIONAL COLLECTION SETTINGS
// =====================================================

// Set up time-to-live (TTL) for temporary collections if needed
// Example: Auto-delete analysis results older than 1 year
db.analysis_results.createIndex({ "created_date": 1 }, { expireAfterSeconds: 31536000, name: "idx_analysis_ttl" });

// =====================================================
// COLLECTION STATISTICS AND VALIDATION
// =====================================================

print("MongoDB schema setup completed successfully!");
print("Collections created:");
print("- taxonomy_data: Species taxonomy and classification information");
print("- edna_sequences: Environmental DNA sequences and analysis results");
print("- uploaded_files: File upload tracking and metadata");
print("- analysis_results: Analysis results and computational outputs");

print("\nIndexes created for optimal query performance:");
print("- Unique indexes on primary identifiers");
print("- Compound indexes for common query patterns");
print("- Geospatial indexes for location-based queries");  
print("- Text indexes for full-text search capabilities");

print("\nValidation rules applied:");
print("- Required field validation");
print("- Data type and format validation");
print("- Enum value constraints");
print("- Numeric range validation");

// Enable sharding preparation (for future scaling)
// sh.enableSharding("marine_platform");

print("\nMongoDB schema initialization complete!");