import axios from 'axios';
import type {
  ApiResponse,
  DatabaseStats,
  Species,
  eDNASequence,
  OceanographicData,
  SamplingPoint,
} from '../types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API Service class
export class ApiService {
  // Health check
  static async healthCheck(): Promise<ApiResponse<any>> {
    const response = await api.get('/health');
    return response.data;
  }

  // Get API information
  static async getApiInfo(): Promise<ApiResponse<any>> {
    const response = await api.get('/info');
    return response.data;
  }

  // Get database statistics
  static async getDatabaseStats(): Promise<DatabaseStats> {
    try {
      // Get species statistics
      const speciesResponse = await api.get('/species/statistics');
      const speciesStats = speciesResponse.data.data;

      // Mock additional statistics for demonstration
      const stats: DatabaseStats = {
        oceanographic_count: 202, // From your database validation
        species_count: speciesStats.taxonomy.total_species || 207,
        edna_count: speciesStats.edna_sequences.total_sequences || 200,
        otolith_count: 0, // Mock data
        total_records: 609, // Sum of all records
        last_updated: new Date().toISOString(),
      };

      return stats;
    } catch (error) {
      console.error('Error fetching database stats:', error);
      // Return mock data if API fails
      return {
        oceanographic_count: 202,
        species_count: 207,
        edna_count: 200,
        otolith_count: 0,
        total_records: 609,
        last_updated: new Date().toISOString(),
      };
    }
  }

  // Species API endpoints
  static async getSpecies(params?: { page?: number; per_page?: number; kingdom?: string }): Promise<ApiResponse<Species[]>> {
    const response = await api.get('/species/taxonomy', { params });
    return response.data;
  }

  static async getSpeciesById(id: string): Promise<ApiResponse<Species>> {
    const response = await api.get(`/species/taxonomy/${id}`);
    return response.data;
  }

  static async getSpeciesStatistics(): Promise<ApiResponse<any>> {
    const response = await api.get('/species/statistics');
    return response.data;
  }

  // File upload endpoints
  static async uploadFile(formData: FormData): Promise<ApiResponse<any>> {
    const response = await api.post('/ingestion/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  static async processFile(fileId: string): Promise<ApiResponse<any>> {
    const response = await api.post(`/ingestion/process/${fileId}`);
    return response.data;
  }

  static async getUploadedFiles(params?: {
    page?: number;
    per_page?: number;
    status?: string;
  }): Promise<ApiResponse<any>> {
    const response = await api.get('/ingestion/files', { params });
    return response.data;
  }

  static async getFileDetails(fileId: string): Promise<ApiResponse<any>> {
    const response = await api.get(`/ingestion/files/${fileId}`);
    return response.data;
  }

  static async getSupportedSchemas(): Promise<ApiResponse<any>> {
    const response = await api.get('/ingestion/schemas');
    return response.data;
  }

  // eDNA API endpoints
  static async identifySequence(data: {
    sequence: string;
    min_score?: number;
    top_matches?: number;
  }): Promise<ApiResponse<any>> {
    const response = await api.post('/species/identify', data);
    return response.data;
  }

  static async batchIdentifySequences(data: {
    sequences: Array<{
      id: string;
      sequence: string;
      metadata?: any;
    }>;
    min_score?: number;
    top_matches?: number;
  }): Promise<ApiResponse<any>> {
    const response = await api.post('/species/batch-identify', data);
    return response.data;
  }

  // Mock API endpoints for missing functionality
  static async getOceanographicData(params?: {
    limit?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<OceanographicData[]> {
    // Mock data for demonstration
    return Array.from({ length: 50 }, (_, i) => ({
      id: `ocean_${i + 1}`,
      location: {
        latitude: 10 + Math.random() * 10,
        longitude: 75 + Math.random() * 10,
      },
      parameter_type: ['temperature', 'salinity', 'ph', 'dissolved_oxygen'][Math.floor(Math.random() * 4)],
      value: Math.random() * 30 + 10,
      unit: 'various',
      timestamp: new Date(Date.now() - Math.random() * 86400000 * 30).toISOString(),
      depth: Math.random() * 100,
    }));
  }

  static async getSamplingPoints(): Promise<SamplingPoint[]> {
    // Mock data for demonstration
    return Array.from({ length: 25 }, (_, i) => ({
      id: `sample_${i + 1}`,
      location: {
        latitude: 8 + Math.random() * 15,
        longitude: 70 + Math.random() * 15,
      },
      timestamp: new Date(Date.now() - Math.random() * 86400000 * 60).toISOString(),
      sample_type: ['water', 'sediment', 'tissue'][Math.floor(Math.random() * 3)],
      parameters: {
        temperature: Math.random() * 30 + 15,
        depth: Math.random() * 200,
      },
    }));
  }

  // Time series data for charts
  static async getTimeSeriesData(parameter: string, days: number = 30): Promise<any[]> {
    const data = [];
    const now = new Date();
    
    for (let i = days; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.random() * 30 + 10 + Math.sin(i / 5) * 5,
        parameter: parameter,
      });
    }
    
    return data;
  }

  // Biodiversity data for charts
  static async getBiodiversityData(): Promise<any[]> {
    try {
      const response = await this.getSpeciesStatistics();
      const phylumData = response.data.taxonomy.phylum_distribution;
      
      return phylumData.map((item: any) => ({
        kingdom: item.phylum,
        count: item.count,
        percentage: (item.count / response.data.taxonomy.total_species) * 100,
      }));
    } catch (error) {
      // Return mock data if API fails
      return [
        { kingdom: 'Chordata', count: 54, percentage: 26.1 },
        { kingdom: 'Tracheophyta', count: 44, percentage: 21.3 },
        { kingdom: 'Proteobacteria', count: 32, percentage: 15.5 },
        { kingdom: 'Firmicutes', count: 14, percentage: 6.8 },
        { kingdom: 'Basidiomycota', count: 12, percentage: 5.8 },
        { kingdom: 'Others', count: 51, percentage: 24.5 },
      ];
    }
  }
}

export default ApiService;