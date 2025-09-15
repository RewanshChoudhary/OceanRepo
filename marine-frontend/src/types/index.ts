// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  timestamp: string;
}

// Database Statistics
export interface DatabaseStats {
  oceanographic_count: number;
  species_count: number;
  edna_count: number;
  otolith_count: number;
  total_records: number;
  last_updated: string;
}

// Species Data
export interface Species {
  species_id: string;
  scientific_name: string;
  common_name: string;
  taxonomy: {
    kingdom: string;
    phylum: string;
    class: string;
    order: string;
    family: string;
    genus: string;
  };
  description?: string;
  data_source?: string;
  import_date?: string;
}

// eDNA Sequence
export interface eDNASequence {
  sequence_id: string;
  sequence: string;
  matched_species_id: string;
  matching_score: number;
  confidence_level: 'low' | 'medium' | 'high' | 'very_high';
  sample_location?: string;
  collection_date?: string;
  method?: string;
}

// Oceanographic Data
export interface OceanographicData {
  id: string;
  location: {
    latitude: number;
    longitude: number;
  };
  parameter_type: string;
  value: number;
  unit?: string;
  timestamp: string;
  depth?: number;
  temperature?: number;
  salinity?: number;
  ph?: number;
  dissolved_oxygen?: number;
}

// Sampling Point
export interface SamplingPoint {
  id: string;
  location: {
    latitude: number;
    longitude: number;
  };
  timestamp: string;
  parameters?: Record<string, any>;
  metadata?: Record<string, any>;
  sample_type?: string;
}

// Chart Data Types
export interface TimeSeriesData {
  date: string;
  value: number;
  parameter: string;
}

export interface BiodiversityData {
  kingdom: string;
  count: number;
  percentage: number;
}

export interface GeographicData {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  type: 'sampling_point' | 'species_location' | 'edna_site';
  data?: any;
}

// Navigation Types
export interface NavigationModule {
  id: string;
  name: string;
  icon: string;
  path: string;
  description?: string;
}

// Dashboard Tab Types
export type DashboardTab = 'timeseries' | 'geographic' | 'biodiversity' | 'ecosystem';

export interface TabConfig {
  id: DashboardTab;
  name: string;
  icon: string;
}