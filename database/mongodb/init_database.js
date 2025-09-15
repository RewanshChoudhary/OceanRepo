// Marine Data Integration Platform - MongoDB Database Initialization Script
// This script creates the database, collections, indexes, and users

print("Starting MongoDB database initialization for Marine Data Platform...");

// Use the marine platform database
use('marine_platform');

// Create database administrator user
db.createUser({
    user: "marine_admin",
    pwd: "marine_admin_2024!",
    roles: [
        { role: "dbAdmin", db: "marine_platform" },
        { role: "readWrite", db: "marine_platform" }
    ]
});

// Create application user with read-write access
db.createUser({
    user: "marine_app_user",
    pwd: "marine_platform_2024!",
    roles: [
        { role: "readWrite", db: "marine_platform" }
    ]
});

// Create read-only user for analytics
db.createUser({
    user: "marine_read_user",
    pwd: "marine_read_2024!",
    roles: [
        { role: "read", db: "marine_platform" }
    ]
});

print("Database users created successfully");

// Apply the schema with collections and indexes
load('schema.js');

print("Schema applied successfully");

// =====================================================
// ADDITIONAL CONFIGURATION
// =====================================================

print("Applying additional database configuration...");

// Enable profiler to monitor slow operations (threshold: 100ms)
db.setProfilingLevel(1, { slowms: 100 });

// Set read concern and write concern defaults
db.adminCommand({
    setDefaultRWConcern: 1,
    defaultReadConcern: { level: "majority" },
    defaultWriteConcern: {
        w: "majority",
        wtimeout: 5000
    }
});

print("Database configuration applied");

// =====================================================
// UTILITY FUNCTIONS AND STORED PROCEDURES
// =====================================================

print("Creating utility functions...");

// Function to validate DNA sequences
function validateDNASequence(sequence) {
    if (!sequence || typeof sequence !== 'string') {
        return { valid: false, errors: ['Sequence must be a non-empty string'] };
    }
    
    const validBases = /^[ATGCNRYSWKMBDHV-]+$/i;
    const errors = [];
    
    if (!validBases.test(sequence)) {
        errors.push('Sequence contains invalid characters. Only IUPAC nucleotide codes are allowed.');
    }
    
    if (sequence.length < 10) {
        errors.push('Sequence too short. Minimum length is 10 bases.');
    }
    
    if (sequence.length > 10000) {
        errors.push('Sequence too long. Maximum length is 10,000 bases.');
    }
    
    return {
        valid: errors.length === 0,
        errors: errors,
        length: sequence.length,
        gc_content: calculateGCContent(sequence)
    };
}

// Function to calculate GC content
function calculateGCContent(sequence) {
    const gcCount = (sequence.match(/[GCgc]/g) || []).length;
    return gcCount / sequence.length;
}

// Function to generate unique identifiers
function generateUniqueId(prefix = '') {
    const timestamp = new Date().getTime().toString();
    const random = Math.random().toString(36).substring(2, 8);
    return prefix + timestamp + '_' + random;
}

// Function to validate geographic coordinates
function validateCoordinates(longitude, latitude) {
    return {
        valid: (
            typeof longitude === 'number' && 
            typeof latitude === 'number' &&
            longitude >= -180 && longitude <= 180 &&
            latitude >= -90 && latitude <= 90
        ),
        longitude: longitude,
        latitude: latitude
    };
}

print("Utility functions created");

// =====================================================
// DATA VALIDATION FUNCTIONS
// =====================================================

print("Creating data validation functions...");

// Taxonomy data validation
function validateTaxonomyData(doc) {
    const errors = [];
    const warnings = [];
    
    // Required field validation
    if (!doc.species_id) errors.push('species_id is required');
    if (!doc.scientific_name) errors.push('scientific_name is required');
    if (!doc.data_source) errors.push('data_source is required');
    
    // Scientific name format validation
    if (doc.scientific_name && !/^[A-Z][a-z]+ [a-z]+/.test(doc.scientific_name)) {
        warnings.push('Scientific name may not follow proper binomial nomenclature');
    }
    
    // Conservation status validation
    if (doc.conservation_status && doc.conservation_status.iucn_status) {
        const validIUCN = ['LC', 'NT', 'VU', 'EN', 'CR', 'EW', 'EX', 'DD', 'NE'];
        if (!validIUCN.includes(doc.conservation_status.iucn_status)) {
            errors.push('Invalid IUCN status code');
        }
    }
    
    return { errors, warnings };
}

// eDNA sequence validation
function validateEDNASequence(doc) {
    const errors = [];
    const warnings = [];
    
    // Required fields
    if (!doc.sequence_id) errors.push('sequence_id is required');
    if (!doc.sequence) errors.push('sequence is required');
    
    // Sequence validation
    if (doc.sequence) {
        const seqValidation = validateDNASequence(doc.sequence);
        if (!seqValidation.valid) {
            errors.push(...seqValidation.errors);
        }
        
        // Update sequence info
        if (!doc.sequence_info) doc.sequence_info = {};
        doc.sequence_info.length = seqValidation.length;
        doc.sequence_info.gc_content = seqValidation.gc_content;
    }
    
    // Geographic coordinates validation
    if (doc.sampling_info && doc.sampling_info.location) {
        const coords = doc.sampling_info.location.coordinates;
        if (coords && coords.length >= 2) {
            const coordValidation = validateCoordinates(coords[0], coords[1]);
            if (!coordValidation.valid) {
                errors.push('Invalid geographic coordinates');
            }
        }
    }
    
    // Quality control validation
    if (doc.quality_control) {
        if (doc.quality_control.quality_score !== undefined) {
            if (doc.quality_control.quality_score < 0 || doc.quality_control.quality_score > 100) {
                errors.push('Quality score must be between 0 and 100');
            }
        }
    }
    
    return { errors, warnings };
}

print("Data validation functions created");

// =====================================================
// AGGREGATION PIPELINES FOR COMMON QUERIES
// =====================================================

print("Creating aggregation pipeline templates...");

// Pipeline for species diversity analysis
const speciesDiversityPipeline = [
    {
        $group: {
            _id: {
                kingdom: "$taxonomy.kingdom",
                phylum: "$taxonomy.phylum",
                class: "$taxonomy.class"
            },
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
    {
        $sort: { species_count: -1 }
    }
];

// Pipeline for temporal analysis of eDNA sequences
const temporalAnalysisPipeline = [
    {
        $match: {
            "sampling_info.collection_date": { $exists: true }
        }
    },
    {
        $group: {
            _id: {
                year: { $year: "$sampling_info.collection_date" },
                month: { $month: "$sampling_info.collection_date" }
            },
            sequence_count: { $sum: 1 },
            unique_species: { $addToSet: "$taxonomic_assignment.matched_species_id" },
            avg_quality_score: { $avg: "$quality_control.quality_score" }
        }
    },
    {
        $addFields: {
            unique_species_count: { $size: "$unique_species" }
        }
    },
    {
        $sort: { "_id.year": 1, "_id.month": 1 }
    }
];

// Pipeline for spatial distribution analysis
const spatialDistributionPipeline = [
    {
        $match: {
            "sampling_info.location": { $exists: true }
        }
    },
    {
        $group: {
            _id: "$taxonomic_assignment.matched_species_id",
            scientific_name: { $first: "$taxonomic_assignment.scientific_name" },
            locations: { $push: "$sampling_info.location" },
            occurrence_count: { $sum: 1 },
            depth_range: {
                $push: "$sampling_info.depth_meters"
            }
        }
    },
    {
        $addFields: {
            location_count: { $size: "$locations" },
            min_depth: { $min: "$depth_range" },
            max_depth: { $max: "$depth_range" },
            avg_depth: { $avg: "$depth_range" }
        }
    }
];

print("Aggregation pipelines created");

// =====================================================
// SAMPLE DATA OPERATIONS
// =====================================================

print("Creating sample data management functions...");

// Function to insert sample taxonomy data
function insertSampleTaxonomyData() {
    const sampleSpecies = [
        {
            species_id: "SAMPLE_001",
            scientific_name: "Calanus finmarchicus",
            common_name: "Arctic copepod",
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
                iucn_status: "LC"
            },
            ecological_info: {
                habitat_type: "pelagic",
                depth_range: { min_meters: 0, max_meters: 2000 },
                temperature_range: { min_celsius: -2, max_celsius: 15 },
                feeding_type: "filter_feeder",
                trophic_level: 2.1
            },
            data_source: "SAMPLE_DB",
            confidence_level: "HIGH",
            import_date: new Date()
        },
        {
            species_id: "SAMPLE_002",
            scientific_name: "Gadus morhua",
            common_name: "Atlantic cod",
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
                iucn_status: "VU"
            },
            ecological_info: {
                habitat_type: "demersal",
                depth_range: { min_meters: 10, max_meters: 600 },
                temperature_range: { min_celsius: 2, max_celsius: 20 },
                feeding_type: "predator",
                trophic_level: 4.2
            },
            data_source: "SAMPLE_DB",
            confidence_level: "VERY_HIGH",
            import_date: new Date()
        }
    ];
    
    try {
        const result = db.taxonomy_data.insertMany(sampleSpecies);
        print(`Inserted ${result.insertedIds.length} sample taxonomy records`);
        return result;
    } catch (error) {
        print(`Error inserting sample taxonomy data: ${error.message}`);
        return null;
    }
}

// Function to insert sample eDNA sequences
function insertSampleEDNASequences() {
    const sampleSequences = [
        {
            sequence_id: "SEQ_SAMPLE_001",
            sequence: "ATGCGATCGATCGATCGATCATGCGATCGATCGATCGATCATGCGATCGATCGATCGATC",
            sequence_info: {
                length: 60,
                gc_content: 0.5,
                primer_info: {
                    target_gene: "COI",
                    amplicon_length: 658
                }
            },
            sampling_info: {
                sample_id: "SAMPLE_001",
                location: {
                    type: "Point",
                    coordinates: [-63.5, 44.7] // Halifax, Nova Scotia
                },
                collection_date: new Date('2024-08-15'),
                depth_meters: 50,
                water_type: "marine"
            },
            laboratory_info: {
                extraction_method: "CTAB",
                sequencing_platform: "Illumina",
                sequencing_date: new Date('2024-08-20'),
                processing_lab: "Marine Genomics Lab"
            },
            taxonomic_assignment: {
                matched_species_id: "SAMPLE_001",
                scientific_name: "Calanus finmarchicus",
                taxonomy: {
                    kingdom: "Animalia",
                    phylum: "Arthropoda",
                    class: "Copepoda",
                    family: "Calanidae",
                    genus: "Calanus"
                },
                matching_score: 98.5,
                confidence_level: "HIGH",
                assignment_method: "k-mer_matching",
                reference_database: "NCBI_NT"
            },
            quality_control: {
                contamination_check: false,
                chimera_check: false,
                quality_score: 92.3,
                manual_review_status: "APPROVED"
            },
            import_date: new Date(),
            data_source: "SAMPLE_PROJECT"
        },
        {
            sequence_id: "SEQ_SAMPLE_002",
            sequence: "TACGTAGCTAGCTAGCTAGCTACGTAGCTAGCTAGCTAGCTACGTAGCTAGCTAGCTAGC",
            sequence_info: {
                length: 60,
                gc_content: 0.45,
                primer_info: {
                    target_gene: "16S",
                    amplicon_length: 500
                }
            },
            sampling_info: {
                sample_id: "SAMPLE_002",
                location: {
                    type: "Point",
                    coordinates: [-66.0, 45.3] // Bay of Fundy
                },
                collection_date: new Date('2024-09-01'),
                depth_meters: 150,
                water_type: "marine"
            },
            laboratory_info: {
                extraction_method: "PowerSoil",
                sequencing_platform: "PacBio",
                sequencing_date: new Date('2024-09-05'),
                processing_lab: "Marine Genomics Lab"
            },
            taxonomic_assignment: {
                matched_species_id: "SAMPLE_002",
                scientific_name: "Gadus morhua",
                taxonomy: {
                    kingdom: "Animalia",
                    phylum: "Chordata",
                    class: "Actinopterygii",
                    family: "Gadidae",
                    genus: "Gadus"
                },
                matching_score: 95.2,
                confidence_level: "HIGH",
                assignment_method: "blast",
                reference_database: "BOLD"
            },
            quality_control: {
                contamination_check: false,
                chimera_check: false,
                quality_score: 88.7,
                manual_review_status: "PENDING"
            },
            import_date: new Date(),
            data_source: "SAMPLE_PROJECT"
        }
    ];
    
    try {
        const result = db.edna_sequences.insertMany(sampleSequences);
        print(`Inserted ${result.insertedIds.length} sample eDNA sequence records`);
        return result;
    } catch (error) {
        print(`Error inserting sample eDNA data: ${error.message}`);
        return null;
    }
}

print("Sample data management functions created");

// =====================================================
// MAINTENANCE AND MONITORING FUNCTIONS
// =====================================================

print("Creating maintenance functions...");

// Function to check collection statistics
function getCollectionStats() {
    const collections = ['taxonomy_data', 'edna_sequences', 'uploaded_files', 'analysis_results'];
    const stats = {};
    
    collections.forEach(collName => {
        try {
            const collStats = db.getCollection(collName).stats();
            stats[collName] = {
                document_count: collStats.count,
                size_bytes: collStats.size,
                avg_doc_size: collStats.avgObjSize,
                storage_size: collStats.storageSize,
                index_count: collStats.nindexes,
                index_size: collStats.totalIndexSize
            };
        } catch (error) {
            stats[collName] = { error: error.message };
        }
    });
    
    return stats;
}

// Function to check index usage
function getIndexUsageStats() {
    const collections = ['taxonomy_data', 'edna_sequences', 'uploaded_files'];
    const indexStats = {};
    
    collections.forEach(collName => {
        try {
            const indexes = db.getCollection(collName).aggregate([
                { $indexStats: {} }
            ]).toArray();
            indexStats[collName] = indexes;
        } catch (error) {
            indexStats[collName] = { error: error.message };
        }
    });
    
    return indexStats;
}

// Function to perform database maintenance
function performMaintenance() {
    print("Performing database maintenance...");
    
    // Compact collections to reclaim space
    const collections = db.listCollectionNames();
    collections.forEach(collName => {
        try {
            db.runCommand({ compact: collName });
            print(`Compacted collection: ${collName}`);
        } catch (error) {
            print(`Error compacting ${collName}: ${error.message}`);
        }
    });
    
    // Update collection statistics
    collections.forEach(collName => {
        try {
            db.runCommand({ reIndex: collName });
            print(`Reindexed collection: ${collName}`);
        } catch (error) {
            print(`Error reindexing ${collName}: ${error.message}`);
        }
    });
    
    print("Database maintenance completed");
}

print("Maintenance functions created");

// =====================================================
// FINAL INITIALIZATION STEPS
// =====================================================

print("Performing final initialization steps...");

// Insert sample data (optional - can be commented out for production)
print("Inserting sample data...");
// insertSampleTaxonomyData();
// insertSampleEDNASequences();

// Display database information
print("Database initialization completed successfully!");
print("\n" + "=".repeat(60));
print("MARINE DATA INTEGRATION PLATFORM - MONGODB");
print("=".repeat(60));

print(`Database: ${db.getName()}`);
print(`Collections: ${db.listCollectionNames().length}`);

// Show collection statistics
const stats = getCollectionStats();
print("\nCollection Statistics:");
Object.keys(stats).forEach(collName => {
    const stat = stats[collName];
    if (stat.error) {
        print(`  ${collName}: Error - ${stat.error}`);
    } else {
        print(`  ${collName}: ${stat.document_count} documents, ${Math.round(stat.size_bytes/1024)} KB`);
    }
});

// Show users
print("\nDatabase Users:");
try {
    const users = db.getUsers();
    users.forEach(user => {
        print(`  ${user.user}: ${user.roles.map(r => r.role).join(', ')}`);
    });
} catch (error) {
    print(`  Error retrieving users: ${error.message}`);
}

print("\nConnection Details:");
print("  Database: marine_platform");
print("  Application User: marine_app_user");
print("  Read-only User: marine_read_user");
print("  Admin User: marine_admin");
print("  Default Port: 27017");

print("\nFeatures Enabled:");
print("  - Document validation with JSON Schema");
print("  - Comprehensive indexing for performance");
print("  - Geospatial queries with 2dsphere indexes");
print("  - Full-text search capabilities");
print("  - TTL (Time-To-Live) for automatic data expiration");
print("  - Aggregation pipeline templates");
print("  - Data validation functions");

print("\nMongoDB initialization complete! Database is ready for use.");
print("=".repeat(60));