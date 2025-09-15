// Marine Data Integration Platform - MongoDB Sample Data
// Comprehensive test data to validate schema functionality

print("Inserting sample data for Marine Data Platform MongoDB...");

// Use the marine platform database
use('marine_platform');

// =====================================================
// TAXONOMY DATA
// =====================================================

print("Inserting taxonomy data...");

const taxonomyData = [
    {
        species_id: "CFIN001",
        scientific_name: "Calanus finmarchicus",
        common_name: "Arctic Copepod",
        authority: "(Gunnerus, 1770)",
        taxonomic_status: "ACCEPTED",
        taxonomy: {
            kingdom: "Animalia",
            phylum: "Arthropoda",
            class: "Copepoda",
            order: "Calanoida",
            family: "Calanidae",
            genus: "Calanus",
            species: "finmarchicus"
        },
        conservation_status: {
            iucn_status: "LC",
            regional_status: "Common"
        },
        ecological_info: {
            habitat_type: "pelagic",
            depth_range: {
                min_meters: 0,
                max_meters: 2000
            },
            temperature_range: {
                min_celsius: -2.0,
                max_celsius: 15.0
            },
            salinity_range: {
                min_psu: 30.0,
                max_psu: 36.0
            },
            geographic_distribution: "North Atlantic and Arctic Oceans",
            feeding_type: "filter_feeder",
            trophic_level: 2.1,
            body_size: {
                length_mm: 3.2,
                weight_g: 0.00045
            }
        },
        reference_info: {
            reference_source: "WoRMS - World Register of Marine Species",
            reference_url: "https://www.marinespecies.org/aphia.php?p=taxdetails&id=104464",
            reference_doi: "10.14284/170",
            authors: ["Boxshall, G.A.", "Halsey, S.H."],
            publication_year: 2004
        },
        data_source: "WoRMS",
        confidence_level: "VERY_HIGH",
        genetic_info: {
            genome_size_bp: 180000000,
            chromosome_count: 22,
            mitochondrial_genes: ["COI", "16S", "12S"],
            genetic_markers: ["COI", "28S", "18S"]
        },
        import_date: new Date("2024-08-15T10:00:00Z"),
        last_modified: new Date("2024-08-15T10:00:00Z"),
        metadata: {
            worms_id: 104464,
            gbif_key: 2192628,
            arctic_species: true,
            commercial_importance: "high",
            research_priority: "high"
        }
    },
    {
        species_id: "GMOR001",
        scientific_name: "Gadus morhua",
        common_name: "Atlantic Cod",
        authority: "Linnaeus, 1758",
        taxonomic_status: "ACCEPTED",
        taxonomy: {
            kingdom: "Animalia",
            phylum: "Chordata",
            class: "Actinopterygii",
            order: "Gadiformes",
            family: "Gadidae",
            genus: "Gadus",
            species: "morhua"
        },
        conservation_status: {
            iucn_status: "VU",
            cites_status: "Not listed",
            national_status: "Vulnerable",
            regional_status: "Overfished"
        },
        ecological_info: {
            habitat_type: "demersal",
            depth_range: {
                min_meters: 10,
                max_meters: 600
            },
            temperature_range: {
                min_celsius: 2.0,
                max_celsius: 20.0
            },
            salinity_range: {
                min_psu: 32.0,
                max_psu: 36.0
            },
            geographic_distribution: "North Atlantic Ocean",
            feeding_type: "predator",
            trophic_level: 4.2,
            body_size: {
                length_mm: 1200,
                weight_g: 25000
            }
        },
        reference_info: {
            reference_source: "FishBase",
            reference_url: "https://www.fishbase.se/summary/69",
            reference_doi: "10.1038/nature06851",
            authors: ["Froese, R.", "Pauly, D."],
            publication_year: 2023
        },
        data_source: "FishBase",
        confidence_level: "VERY_HIGH",
        genetic_info: {
            genome_size_bp: 830000000,
            chromosome_count: 23,
            mitochondrial_genes: ["COI", "cytB", "16S", "12S"],
            genetic_markers: ["COI", "microsatellites", "SNPs"]
        },
        import_date: new Date("2024-08-15T10:30:00Z"),
        last_modified: new Date("2024-08-15T10:30:00Z"),
        metadata: {
            fishbase_id: 69,
            commercial_importance: "very_high",
            stock_status: "overfished",
            fishery_value_usd: 2500000000
        }
    },
    {
        species_id: "EHAM001",
        scientific_name: "Euphausia hamiltoni",
        common_name: "Hamilton Krill",
        authority: "Tattersall, 1906",
        taxonomic_status: "ACCEPTED",
        taxonomy: {
            kingdom: "Animalia",
            phylum: "Arthropoda",
            class: "Malacostraca",
            order: "Euphausiacea",
            family: "Euphausiidae",
            genus: "Euphausia",
            species: "hamiltoni"
        },
        conservation_status: {
            iucn_status: "LC"
        },
        ecological_info: {
            habitat_type: "pelagic",
            depth_range: {
                min_meters: 50,
                max_meters: 1000
            },
            temperature_range: {
                min_celsius: -1.0,
                max_celsius: 12.0
            },
            salinity_range: {
                min_psu: 33.5,
                max_psu: 35.0
            },
            geographic_distribution: "Southern Ocean and Sub-Antarctic waters",
            feeding_type: "filter_feeder",
            trophic_level: 2.5,
            body_size: {
                length_mm: 12.5,
                weight_g: 0.025
            }
        },
        reference_info: {
            reference_source: "World Register of Marine Species",
            reference_url: "https://www.marinespecies.org/aphia.php?p=taxdetails&id=110675",
            authors: ["Tattersall, W.M."],
            publication_year: 1906
        },
        data_source: "WoRMS",
        confidence_level: "HIGH",
        import_date: new Date("2024-08-15T11:00:00Z"),
        last_modified: new Date("2024-08-15T11:00:00Z"),
        metadata: {
            worms_id: 110675,
            vertical_migration: true,
            swarming_species: true,
            antarctic_species: true
        }
    },
    {
        species_id: "PMON001",
        scientific_name: "Pseudocalanus monachus",
        common_name: "Monk Copepod",
        authority: "Willey, 1920",
        taxonomic_status: "ACCEPTED",
        taxonomy: {
            kingdom: "Animalia",
            phylum: "Arthropoda",
            class: "Copepoda",
            order: "Calanoida",
            family: "Pseudocalanidae",
            genus: "Pseudocalanus",
            species: "monachus"
        },
        conservation_status: {
            iucn_status: "LC"
        },
        ecological_info: {
            habitat_type: "pelagic",
            depth_range: {
                min_meters: 0,
                max_meters: 500
            },
            temperature_range: {
                min_celsius: -2.0,
                max_celsius: 18.0
            },
            salinity_range: {
                min_psu: 31.0,
                max_psu: 36.0
            },
            geographic_distribution: "North Atlantic Ocean, coastal and shelf waters",
            feeding_type: "filter_feeder",
            trophic_level: 2.0,
            body_size: {
                length_mm: 1.8,
                weight_g: 0.00012
            }
        },
        reference_info: {
            reference_source: "COPEPODS - The Global Copepod Database",
            reference_url: "https://www.st.nmfs.noaa.gov/copepod/",
            authors: ["Willey, A."],
            publication_year: 1920
        },
        data_source: "COPEPODS",
        confidence_level: "HIGH",
        import_date: new Date("2024-08-15T11:30:00Z"),
        last_modified: new Date("2024-08-15T11:30:00Z"),
        metadata: {
            cold_water_species: true,
            biomass_indicator: true,
            shelf_species: true
        }
    },
    {
        species_id: "TLONG001",
        scientific_name: "Thysanoessa longicaudata",
        common_name: "Long-tailed Krill",
        authority: "Krøyer, 1846",
        taxonomic_status: "ACCEPTED",
        taxonomy: {
            kingdom: "Animalia",
            phylum: "Arthropoda",
            class: "Malacostraca",
            order: "Euphausiacea",
            family: "Euphausiidae",
            genus: "Thysanoessa",
            species: "longicaudata"
        },
        conservation_status: {
            iucn_status: "LC"
        },
        ecological_info: {
            habitat_type: "pelagic",
            depth_range: {
                min_meters: 25,
                max_meters: 800
            },
            temperature_range: {
                min_celsius: -1.5,
                max_celsius: 10.0
            },
            salinity_range: {
                min_psu: 32.0,
                max_psu: 35.5
            },
            geographic_distribution: "Arctic and North Atlantic Oceans",
            feeding_type: "omnivore",
            trophic_level: 2.8,
            body_size: {
                length_mm: 18.0,
                weight_g: 0.035
            }
        },
        reference_info: {
            reference_source: "Arctic Ocean Diversity",
            reference_url: "https://www.arcodiv.org/",
            authors: ["Krøyer, H."],
            publication_year: 1846
        },
        data_source: "ArctOD",
        confidence_level: "HIGH",
        import_date: new Date("2024-08-15T12:00:00Z"),
        last_modified: new Date("2024-08-15T12:00:00Z"),
        metadata: {
            arctic_endemic: true,
            sea_ice_associated: true,
            climate_indicator: true
        }
    }
];

try {
    const taxonomyResult = db.taxonomy_data.insertMany(taxonomyData);
    print(`Inserted ${taxonomyResult.insertedIds.length} taxonomy records`);
} catch (error) {
    print(`Error inserting taxonomy data: ${error.message}`);
}

// =====================================================
// eDNA SEQUENCES
// =====================================================

print("Inserting eDNA sequence data...");

const ednaData = [
    {
        sequence_id: "SEQ_AMBS_001",
        sequence: "ATGCGATCGATCGATCGATCATGCGATCGATCGATCGATCATGCGATCGATCGATCGATCATGCGATCGATCGATCGATC",
        sequence_info: {
            length: 80,
            gc_content: 0.50,
            quality_scores: [35, 38, 42, 38, 35, 40, 38, 35, 42, 38],
            primer_info: {
                forward_primer: "GGWACWGGWTGAACWGTWTAYCCYCC",
                reverse_primer: "TAAACTTCAGGGTGACCAAARAAYCA",
                target_gene: "COI",
                amplicon_length: 658
            }
        },
        sampling_info: {
            sample_id: "AMBS2024_HUD_001_S01",
            sampling_point_id: "AMBS2024_HUD_001_P01",
            sampling_event_id: "AMBS2024_HUD_001",
            location: {
                type: "Point",
                coordinates: [-63.5833, 44.6333]
            },
            collection_date: new Date("2024-08-15T08:30:00Z"),
            depth_meters: 5.0,
            water_type: "marine",
            habitat_description: "Surface pelagic waters with high phytoplankton activity"
        },
        laboratory_info: {
            extraction_method: "CTAB extraction protocol",
            amplification_method: "PCR with Folmer primers",
            sequencing_platform: "Illumina",
            sequencing_date: new Date("2024-08-20T14:00:00Z"),
            library_preparation: "TruSeq DNA PCR-Free",
            barcode_sequence: "ATCACG",
            processing_lab: "Bedford Institute Marine Genomics Lab",
            technician: "Dr. Sarah Chen"
        },
        taxonomic_assignment: {
            matched_species_id: "CFIN001",
            scientific_name: "Calanus finmarchicus",
            common_name: "Arctic Copepod",
            taxonomy: {
                kingdom: "Animalia",
                phylum: "Arthropoda",
                class: "Copepoda",
                order: "Calanoida",
                family: "Calanidae",
                genus: "Calanus",
                species: "finmarchicus"
            },
            matching_score: 98.5,
            confidence_level: "HIGH",
            assignment_method: "k-mer_matching",
            reference_database: "NCBI_NT",
            alternative_matches: [
                {
                    species_id: "CGLA001",
                    scientific_name: "Calanus glacialis",
                    matching_score: 89.2
                },
                {
                    species_id: "CHYP001", 
                    scientific_name: "Calanus hyperboreus",
                    matching_score: 85.7
                }
            ]
        },
        quality_control: {
            contamination_check: false,
            chimera_check: false,
            quality_score: 92.3,
            length_filter_passed: true,
            abundance_filter_passed: true,
            manual_review_status: "APPROVED",
            reviewer: "Dr. Michael Thompson",
            review_date: new Date("2024-08-22T09:00:00Z"),
            qc_flags: ["high_quality", "species_verified"]
        },
        analysis_results: {
            abundance_count: 147,
            relative_abundance: 0.285,
            diversity_indices: {
                shannon: 2.45,
                simpson: 0.12,
                chao1: 28.5
            },
            blast_results: [
                {
                    hit_id: "KJ001234",
                    e_value: 1.2e-45,
                    bit_score: 187.3,
                    identity_percent: 98.5,
                    coverage_percent: 95.2
                }
            ]
        },
        import_date: new Date("2024-08-15T15:00:00Z"),
        last_modified: new Date("2024-08-22T09:30:00Z"),
        data_source: "AMBS_PROJECT",
        metadata: {
            project_code: "AMBS2024",
            cruise_id: "HUD2024_08",
            principal_investigator: "Dr. Sarah Johnson",
            funding_source: "NSERC"
        }
    },
    {
        sequence_id: "SEQ_CEMP_002",
        sequence: "TACGTAGCTAGCTAGCTAGCTACGTAGCTAGCTAGCTAGCTACGTAGCTAGCTAGCTAGCTACGTAGCTAGCTAGCTAGC",
        sequence_info: {
            length: 80,
            gc_content: 0.425,
            quality_scores: [32, 35, 38, 35, 32, 37, 35, 32, 38, 35],
            primer_info: {
                forward_primer: "AGAGTTTGATCMTGGCTCAG",
                reverse_primer: "TACGGYTACCTTGTTACGACTT",
                target_gene: "16S",
                amplicon_length: 500
            }
        },
        sampling_info: {
            sample_id: "CEMP2024_OCE_005_S01",
            sampling_point_id: "CEMP2024_OCE_005_P01",
            sampling_event_id: "CEMP2024_OCE_005",
            location: {
                type: "Point",
                coordinates: [-66.0667, 45.2833]
            },
            collection_date: new Date("2024-09-02T07:00:00Z"),
            depth_meters: 10.0,
            water_type: "marine",
            habitat_description: "Coastal tidal mixing zone with high turbidity"
        },
        laboratory_info: {
            extraction_method: "PowerSoil DNA Isolation Kit",
            amplification_method: "16S rRNA gene amplification",
            sequencing_platform: "PacBio",
            sequencing_date: new Date("2024-09-05T10:00:00Z"),
            library_preparation: "SMRTbell library",
            barcode_sequence: "CGATGT",
            processing_lab: "Dalhousie Marine Molecular Lab",
            technician: "Dr. Lisa Wang"
        },
        taxonomic_assignment: {
            matched_species_id: "GMOR001",
            scientific_name: "Gadus morhua",
            common_name: "Atlantic Cod",
            taxonomy: {
                kingdom: "Animalia",
                phylum: "Chordata",
                class: "Actinopterygii",
                order: "Gadiformes",
                family: "Gadidae",
                genus: "Gadus",
                species: "morhua"
            },
            matching_score: 95.2,
            confidence_level: "HIGH",
            assignment_method: "blast",
            reference_database: "BOLD",
            alternative_matches: [
                {
                    species_id: "GMAC001",
                    scientific_name: "Gadus macrocephalus",
                    matching_score: 87.3
                }
            ]
        },
        quality_control: {
            contamination_check: false,
            chimera_check: false,
            quality_score: 88.7,
            length_filter_passed: true,
            abundance_filter_passed: true,
            manual_review_status: "PENDING",
            qc_flags: ["good_quality", "needs_verification"]
        },
        analysis_results: {
            abundance_count: 23,
            relative_abundance: 0.045,
            diversity_indices: {
                shannon: 3.12,
                simpson: 0.08,
                chao1: 42.1
            }
        },
        import_date: new Date("2024-09-02T18:00:00Z"),
        last_modified: new Date("2024-09-05T15:30:00Z"),
        data_source: "CEMP_PROJECT",
        metadata: {
            project_code: "CEMP2024",
            cruise_id: "OCE2024_09", 
            tidal_state: "flood",
            current_speed_ms: 1.8
        }
    },
    {
        sequence_id: "SEQ_DSEI_003",
        sequence: "GCTAGCTAGCTAGCTAGCGCTAGCTAGCTAGCTAGCGCTAGCTAGCTAGCTAGCGCTAGCTAGCTAGCTAGCGCTAGC",
        sequence_info: {
            length: 78,
            gc_content: 0.55,
            quality_scores: [40, 42, 45, 42, 40, 43, 42, 40, 45, 42],
            primer_info: {
                forward_primer: "GGWACWGGWTGAACWGTWTAYCCYCC",
                reverse_primer: "TAAACTTCAGGGTGACCAAARAAYCA",
                target_gene: "COI",
                amplicon_length: 658
            }
        },
        sampling_info: {
            sample_id: "DSEI2023_AMU_012_S01",
            sampling_point_id: "DSEI2023_AMU_012_P01",
            sampling_event_id: "DSEI2023_AMU_012",
            location: {
                type: "Point",
                coordinates: [-58.7500, 55.4167]
            },
            collection_date: new Date("2024-04-20T18:30:00Z"),
            depth_meters: 2800.0,
            water_type: "marine",
            habitat_description: "Deep abyssal waters near seafloor with fine sediment"
        },
        laboratory_info: {
            extraction_method: "DNeasy Blood & Tissue Kit",
            amplification_method: "Deep-sea adapted PCR protocol",
            sequencing_platform: "Illumina",
            sequencing_date: new Date("2024-04-25T11:00:00Z"),
            library_preparation: "Nextera XT",
            barcode_sequence: "TTAGGC",
            processing_lab: "Memorial University Deep Sea Lab",
            technician: "Dr. James Rodriguez"
        },
        taxonomic_assignment: {
            matched_species_id: "EHAM001",
            scientific_name: "Euphausia hamiltoni",
            common_name: "Hamilton Krill",
            taxonomy: {
                kingdom: "Animalia",
                phylum: "Arthropoda",
                class: "Malacostraca",
                order: "Euphausiacea",
                family: "Euphausiidae",
                genus: "Euphausia",
                species: "hamiltoni"
            },
            matching_score: 91.8,
            confidence_level: "MEDIUM",
            assignment_method: "phylogenetic_placement",
            reference_database: "Silva_138",
            alternative_matches: [
                {
                    species_id: "ESUP001",
                    scientific_name: "Euphausia superba",
                    matching_score: 88.4
                }
            ]
        },
        quality_control: {
            contamination_check: false,
            chimera_check: false,
            quality_score: 94.1,
            length_filter_passed: true,
            abundance_filter_passed: false,
            manual_review_status: "APPROVED",
            reviewer: "Dr. Emily Rodriguez",
            review_date: new Date("2024-04-26T14:00:00Z"),
            qc_flags: ["high_quality", "low_abundance", "deep_water"]
        },
        analysis_results: {
            abundance_count: 3,
            relative_abundance: 0.012,
            diversity_indices: {
                shannon: 4.82,
                simpson: 0.02,
                chao1: 156.3
            }
        },
        import_date: new Date("2024-04-20T22:00:00Z"),
        last_modified: new Date("2024-04-26T14:30:00Z"),
        data_source: "DSEI_PROJECT",
        metadata: {
            project_code: "DSEI2023",
            cruise_id: "AMU2024_04",
            bottom_distance_m: 50.0,
            water_mass: "Labrador_Sea_Deep_Water"
        }
    },
    {
        sequence_id: "SEQ_AMBS_004",
        sequence: "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC",
        sequence_info: {
            length: 72,
            gc_content: 0.50,
            quality_scores: [36, 38, 40, 38, 36, 39, 38, 36, 40, 38],
            primer_info: {
                forward_primer: "AGAGTTTGATCMTGGCTCAG",
                reverse_primer: "TACGGYTACCTTGTTACGACTT",
                target_gene: "16S",
                amplicon_length: 500
            }
        },
        sampling_info: {
            sample_id: "AMBS2024_HUD_001_S02",
            sampling_point_id: "AMBS2024_HUD_001_P02",
            sampling_event_id: "AMBS2024_HUD_001",
            location: {
                type: "Point",
                coordinates: [-63.5833, 44.6333]
            },
            collection_date: new Date("2024-08-15T09:15:00Z"),
            depth_meters: 45.0,
            water_type: "marine",
            habitat_description: "Thermocline layer with temperature stratification"
        },
        laboratory_info: {
            extraction_method: "CTAB extraction protocol",
            amplification_method: "16S rRNA universal primers",
            sequencing_platform: "Illumina",
            sequencing_date: new Date("2024-08-20T15:30:00Z"),
            library_preparation: "TruSeq DNA PCR-Free",
            barcode_sequence: "GCCAAT",
            processing_lab: "Bedford Institute Marine Genomics Lab",
            technician: "Dr. Sarah Chen"
        },
        taxonomic_assignment: {
            matched_species_id: "PMON001",
            scientific_name: "Pseudocalanus monachus",
            common_name: "Monk Copepod",
            taxonomy: {
                kingdom: "Animalia",
                phylum: "Arthropoda",
                class: "Copepoda",
                order: "Calanoida",
                family: "Pseudocalanidae",
                genus: "Pseudocalanus",
                species: "monachus"
            },
            matching_score: 94.7,
            confidence_level: "HIGH",
            assignment_method: "k-mer_matching",
            reference_database: "NCBI_NT",
            alternative_matches: [
                {
                    species_id: "PMIN001",
                    scientific_name: "Pseudocalanus minutus",
                    matching_score: 91.3
                }
            ]
        },
        quality_control: {
            contamination_check: false,
            chimera_check: false,
            quality_score: 89.4,
            length_filter_passed: true,
            abundance_filter_passed: true,
            manual_review_status: "APPROVED",
            reviewer: "Dr. Michael Thompson",
            review_date: new Date("2024-08-22T10:15:00Z"),
            qc_flags: ["good_quality", "species_verified", "thermocline_sample"]
        },
        analysis_results: {
            abundance_count: 89,
            relative_abundance: 0.173,
            diversity_indices: {
                shannon: 2.12,
                simpson: 0.18,
                chao1: 19.8
            }
        },
        import_date: new Date("2024-08-15T16:00:00Z"),
        last_modified: new Date("2024-08-22T10:30:00Z"),
        data_source: "AMBS_PROJECT",
        metadata: {
            project_code: "AMBS2024",
            developmental_stage: "copepodite",
            temperature_c: 12.32,
            depth_layer: "thermocline"
        }
    }
];

try {
    const ednaResult = db.edna_sequences.insertMany(ednaData);
    print(`Inserted ${ednaResult.insertedIds.length} eDNA sequence records`);
} catch (error) {
    print(`Error inserting eDNA data: ${error.message}`);
}

// =====================================================
// UPLOADED FILES
// =====================================================

print("Inserting uploaded files data...");

const uploadedFiles = [
    {
        file_id: "20240815_143022_oceanographic_data.csv",
        original_filename: "oceanographic_data.csv",
        file_info: {
            file_size: 156789,
            file_type: "csv",
            mime_type: "text/csv",
            encoding: "utf-8",
            checksum_md5: "d41d8cd98f00b204e9800998ecf8427e",
            checksum_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        },
        storage_info: {
            file_path: "/tmp/marine_platform_uploads/20240815_143022_oceanographic_data.csv",
            storage_backend: "local",
            retention_policy: "90_days",
            expiry_date: new Date("2024-11-13T14:30:22Z")
        },
        upload_info: {
            uploader_id: "dr.s.johnson",
            uploader_name: "Dr. Sarah Johnson",
            upload_method: "web_form",
            client_ip: "192.168.1.100",
            user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        processing_info: {
            schema_matches: [
                {
                    schema_name: "oceanographic_data",
                    confidence_score: 95.2,
                    matched_fields: ["timestamp", "depth_meters", "temperature_celsius", "salinity_psu"],
                    validation_errors: []
                }
            ],
            processing_attempts: 1,
            last_processing_attempt: new Date("2024-08-15T14:31:00Z"),
            processing_duration_seconds: 12.5,
            records_processed: 156,
            records_inserted: 156,
            records_failed: 0
        },
        status: "processed",
        description: "Oceanographic measurements from Halifax Line station 1",
        tags: ["oceanographic", "CTD", "halifax_line", "ambs2024"],
        upload_timestamp: new Date("2024-08-15T14:30:22Z"),
        processed_timestamp: new Date("2024-08-15T14:31:12Z"),
        error_log: [],
        metadata: {
            project_code: "AMBS2024",
            cruise_id: "HUD2024_08",
            station_number: 1,
            data_quality: "validated"
        }
    },
    {
        file_id: "20240902_072015_edna_sequences.json",
        original_filename: "bay_of_fundy_edna_sequences.json",
        file_info: {
            file_size: 2456789,
            file_type: "json",
            mime_type: "application/json",
            encoding: "utf-8",
            checksum_md5: "c4ca4238a0b923820dcc509a6f75849b",
            checksum_sha256: "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
        },
        storage_info: {
            file_path: "/tmp/marine_platform_uploads/20240902_072015_edna_sequences.json",
            storage_backend: "local",
            retention_policy: "365_days",
            expiry_date: new Date("2025-09-02T07:20:15Z")
        },
        upload_info: {
            uploader_id: "dr.m.chen",
            uploader_name: "Dr. Michael Chen",
            upload_method: "api",
            client_ip: "10.0.1.50"
        },
        processing_info: {
            schema_matches: [
                {
                    schema_name: "edna_sequences",
                    confidence_score: 88.7,
                    matched_fields: ["sequence_id", "sequence", "taxonomic_assignment"],
                    validation_errors: ["missing_quality_scores"]
                }
            ],
            processing_attempts: 2,
            last_processing_attempt: new Date("2024-09-02T07:25:30Z"),
            processing_duration_seconds: 45.8,
            records_processed: 342,
            records_inserted: 298,
            records_failed: 44
        },
        status: "processed",
        description: "eDNA sequences from Bay of Fundy coastal monitoring",
        tags: ["edna", "bay_of_fundy", "coastal", "cemp2024"],
        upload_timestamp: new Date("2024-09-02T07:20:15Z"),
        processed_timestamp: new Date("2024-09-02T07:26:15Z"),
        error_log: [
            {
                timestamp: new Date("2024-09-02T07:22:45Z"),
                error_type: "validation_error",
                error_message: "44 sequences failed quality score validation",
                stack_trace: null
            }
        ],
        metadata: {
            project_code: "CEMP2024",
            sequencing_platform: "PacBio",
            target_gene: "16S"
        }
    },
    {
        file_id: "20240420_190045_species_data.csv",
        original_filename: "deep_sea_species_inventory.csv",
        file_info: {
            file_size: 89456,
            file_type: "csv",
            mime_type: "text/csv",
            encoding: "utf-8",
            checksum_md5: "098f6bcd4621d373cade4e832627b4f6",
            checksum_sha256: "5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5"
        },
        storage_info: {
            file_path: "/tmp/marine_platform_uploads/20240420_190045_species_data.csv",
            storage_backend: "local",
            retention_policy: "730_days",
            expiry_date: new Date("2026-04-20T19:00:45Z")
        },
        upload_info: {
            uploader_id: "dr.e.rodriguez",
            uploader_name: "Dr. Emily Rodriguez",
            upload_method: "ftp",
            client_ip: "134.112.45.22"
        },
        processing_info: {
            schema_matches: [
                {
                    schema_name: "species_data",
                    confidence_score: 92.1,
                    matched_fields: ["species_id", "scientific_name", "taxonomy"],
                    validation_errors: []
                }
            ],
            processing_attempts: 1,
            last_processing_attempt: new Date("2024-04-20T19:05:00Z"),
            processing_duration_seconds: 8.3,
            records_processed: 67,
            records_inserted: 67,
            records_failed: 0
        },
        status: "processed",
        description: "Deep-sea species taxonomy from Labrador Sea exploration",
        tags: ["taxonomy", "deep_sea", "labrador_sea", "dsei2023"],
        upload_timestamp: new Date("2024-04-20T19:00:45Z"),
        processed_timestamp: new Date("2024-04-20T19:05:08Z"),
        error_log: [],
        metadata: {
            project_code: "DSEI2023",
            max_depth: 2850,
            habitat_type: "abyssal"
        }
    }
];

try {
    const filesResult = db.uploaded_files.insertMany(uploadedFiles);
    print(`Inserted ${filesResult.insertedIds.length} uploaded file records`);
} catch (error) {
    print(`Error inserting uploaded files: ${error.message}`);
}

// =====================================================
// ANALYSIS RESULTS
// =====================================================

print("Inserting analysis results data...");

const analysisResults = [
    {
        analysis_id: "BIODIV_AMBS_20240815_001",
        analysis_type: "biodiversity_analysis",
        input_data: {
            data_sources: ["edna_sequences", "biological_observations"],
            date_range: {
                start_date: new Date("2024-08-01T00:00:00Z"),
                end_date: new Date("2024-08-31T23:59:59Z")
            },
            spatial_extent: {
                type: "Polygon",
                coordinates: [[[-65.0, 43.0], [-62.0, 43.0], [-62.0, 46.0], [-65.0, 46.0], [-65.0, 43.0]]]
            },
            filter_criteria: {
                project_codes: ["AMBS2024"],
                quality_threshold: 0.8
            }
        },
        parameters: {
            diversity_indices: ["shannon", "simpson", "chao1"],
            rarefaction_enabled: true,
            bootstrap_iterations: 1000,
            confidence_level: 0.95
        },
        results: {
            total_species: 42,
            total_sequences: 1245,
            shannon_diversity: 2.87,
            simpson_diversity: 0.13,
            chao1_estimate: 58.3,
            dominance_species: [
                {
                    species_id: "CFIN001",
                    scientific_name: "Calanus finmarchicus",
                    relative_abundance: 0.285
                },
                {
                    species_id: "PMON001",
                    scientific_name: "Pseudocalanus monachus",
                    relative_abundance: 0.173
                }
            ],
            rare_species_count: 18,
            endemic_species_count: 3
        },
        quality_metrics: {
            confidence_score: 0.92,
            sample_size: 1245,
            spatial_coverage: 0.85,
            temporal_coverage: 1.0
        },
        created_date: new Date("2024-08-16T10:00:00Z"),
        created_by: "dr.s.johnson",
        computation_info: {
            processing_time_seconds: 124.7,
            algorithm_version: "BioDivAnalyzer_v2.1",
            computing_environment: "R 4.3.1, vegan package",
            memory_usage_mb: 512.3
        },
        metadata: {
            analysis_purpose: "baseline_biodiversity_assessment",
            peer_review_status: "pending",
            publication_intent: true
        }
    },
    {
        analysis_id: "SPATIAL_CEMP_20240903_001",
        analysis_type: "spatial_analysis",
        input_data: {
            data_sources: ["edna_sequences"],
            date_range: {
                start_date: new Date("2024-09-01T00:00:00Z"),
                end_date: new Date("2024-09-03T23:59:59Z")
            },
            spatial_extent: {
                type: "Polygon",
                coordinates: [[[-67.0, 44.5], [-65.0, 44.5], [-65.0, 46.0], [-67.0, 46.0], [-67.0, 44.5]]]
            },
            filter_criteria: {
                project_codes: ["CEMP2024"],
                habitat_types: ["coastal", "pelagic"]
            }
        },
        parameters: {
            analysis_methods: ["spatial_autocorrelation", "hotspot_detection"],
            grid_resolution_km: 1.0,
            neighbor_distance_km: 5.0,
            significance_level: 0.05
        },
        results: {
            hotspot_locations: [
                {
                    coordinates: [-66.0667, 45.2833],
                    species_richness: 15,
                    significance_p: 0.003
                }
            ],
            moran_i: 0.42,
            spatial_autocorr_p: 0.001,
            clustering_patterns: {
                high_diversity_clusters: 3,
                low_diversity_clusters: 1
            }
        },
        quality_metrics: {
            confidence_score: 0.88,
            p_value: 0.001,
            sample_size: 342
        },
        created_date: new Date("2024-09-03T14:30:00Z"),
        created_by: "dr.m.chen",
        computation_info: {
            processing_time_seconds: 67.2,
            algorithm_version: "SpatialEcol_v1.8",
            computing_environment: "Python 3.9, geopandas, scipy",
            memory_usage_mb: 256.8
        },
        metadata: {
            tidal_influence: true,
            coastal_zone_analysis: true
        }
    },
    {
        analysis_id: "TEMPORAL_MULTI_20240901_001",
        analysis_type: "temporal_analysis",
        input_data: {
            data_sources: ["edna_sequences", "oceanographic_data"],
            date_range: {
                start_date: new Date("2024-04-01T00:00:00Z"),
                end_date: new Date("2024-09-01T23:59:59Z")
            },
            spatial_extent: null,
            filter_criteria: {
                project_codes: ["AMBS2024", "CEMP2024", "DSEI2023"]
            }
        },
        parameters: {
            time_series_methods: ["trend_analysis", "seasonal_decomposition"],
            temporal_resolution: "monthly",
            detrending_method: "linear"
        },
        results: {
            temporal_trends: {
                species_richness_trend: "increasing",
                trend_significance: 0.02,
                seasonal_pattern: true
            },
            peak_diversity_month: "August",
            lowest_diversity_month: "April",
            temperature_correlation: 0.67,
            correlation_p_value: 0.001
        },
        quality_metrics: {
            confidence_score: 0.85,
            r_squared: 0.72,
            sample_size: 1634
        },
        created_date: new Date("2024-09-01T16:45:00Z"),
        created_by: "system_auto",
        computation_info: {
            processing_time_seconds: 203.5,
            algorithm_version: "TimeSeriesAnalyzer_v3.2",
            computing_environment: "R 4.3.1, forecast package",
            memory_usage_mb: 1024.7
        },
        metadata: {
            multi_project_analysis: true,
            climate_correlation: true,
            seasonal_analysis: true
        }
    }
];

try {
    const analysisResult = db.analysis_results.insertMany(analysisResults);
    print(`Inserted ${analysisResult.insertedIds.length} analysis result records`);
} catch (error) {
    print(`Error inserting analysis results: ${error.message}`);
}

// =====================================================
// VERIFICATION AND STATISTICS
// =====================================================

print("Running verification queries...");

// Count records in each collection
print("\nCollection record counts:");
const collections = ['taxonomy_data', 'edna_sequences', 'uploaded_files', 'analysis_results'];
collections.forEach(collName => {
    try {
        const count = db.getCollection(collName).countDocuments({});
        print(`  ${collName}: ${count} documents`);
    } catch (error) {
        print(`  ${collName}: Error - ${error.message}`);
    }
});

// Show taxonomy summary
print("\nTaxonomy summary:");
try {
    const taxonomySummary = db.taxonomy_data.aggregate([
        {
            $group: {
                _id: "$taxonomy.phylum",
                species_count: { $sum: 1 },
                conservation_concerns: {
                    $sum: {
                        $cond: [
                            { $in: ["$conservation_status.iucn_status", ["VU", "EN", "CR"]] },
                            1, 0
                        ]
                    }
                }
            }
        },
        { $sort: { species_count: -1 } }
    ]).toArray();
    
    taxonomySummary.forEach(phylum => {
        print(`  ${phylum._id}: ${phylum.species_count} species (${phylum.conservation_concerns} of conservation concern)`);
    });
} catch (error) {
    print(`  Error in taxonomy summary: ${error.message}`);
}

// Show eDNA sequence summary
print("\neDNA sequences summary:");
try {
    const ednaSummary = db.edna_sequences.aggregate([
        {
            $group: {
                _id: "$taxonomic_assignment.confidence_level",
                sequence_count: { $sum: 1 },
                avg_score: { $avg: "$taxonomic_assignment.matching_score" }
            }
        },
        { $sort: { sequence_count: -1 } }
    ]).toArray();
    
    ednaSummary.forEach(conf => {
        print(`  ${conf._id || 'Unknown'} confidence: ${conf.sequence_count} sequences (avg score: ${conf.avg_score ? conf.avg_score.toFixed(1) : 'N/A'})`);
    });
} catch (error) {
    print(`  Error in eDNA summary: ${error.message}`);
}

// Show processing status summary
print("\nFile processing status:");
try {
    const processingStatus = db.uploaded_files.aggregate([
        {
            $group: {
                _id: "$status",
                file_count: { $sum: 1 },
                total_size: { $sum: "$file_info.file_size" }
            }
        }
    ]).toArray();
    
    processingStatus.forEach(status => {
        const sizeMB = status.total_size ? (status.total_size / (1024*1024)).toFixed(1) : 'N/A';
        print(`  ${status._id}: ${status.file_count} files (${sizeMB} MB)`);
    });
} catch (error) {
    print(`  Error in processing status summary: ${error.message}`);
}

// Test geospatial queries
print("\nTesting geospatial queries...");
try {
    const spatialQuery = db.edna_sequences.find({
        "sampling_info.location": {
            $near: {
                $geometry: {
                    type: "Point",
                    coordinates: [-63.5833, 44.6333]
                },
                $maxDistance: 10000  // 10km radius
            }
        }
    }).count();
    
    print(`  Sequences within 10km of Halifax: ${spatialQuery}`);
} catch (error) {
    print(`  Geospatial query error: ${error.message}`);
}

print("\n" + "=".repeat(60));
print("MongoDB sample data verification complete!");
print("Database contains comprehensive test data and is ready for development.");
print("=".repeat(60));