import React, { useState, useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, LayersControl } from 'react-leaflet';
import { Icon } from 'leaflet';
import { MapPin, Layers, Search, Download, Filter } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import '../../../utils/leafletFix';
import ApiService from '../../../services/api';

// Mock data for sampling locations
const generateSampleLocations = () => {
  const locations = [
    { name: 'Arabian Sea', lat: 19.0760, lng: 72.8777, type: 'edna', count: 45 },
    { name: 'Bay of Bengal', lat: 13.0827, lng: 80.2707, type: 'oceanographic', count: 32 },
    { name: 'Lakshadweep Sea', lat: 10.5667, lng: 72.6417, type: 'species', count: 28 },
    { name: 'Andaman Sea', lat: 11.7401, lng: 92.6586, type: 'edna', count: 38 },
    { name: 'Gujarat Coast', lat: 22.2587, lng: 71.1924, type: 'oceanographic', count: 55 },
    { name: 'Tamil Nadu Coast', lat: 11.1271, lng: 78.6569, type: 'species', count: 42 },
    { name: 'Kerala Coast', lat: 10.8505, lng: 76.2711, type: 'edna', count: 35 },
    { name: 'Odisha Coast', lat: 20.9517, lng: 85.0985, type: 'oceanographic', count: 25 },
    { name: 'West Bengal Coast', lat: 22.9868, lng: 87.8550, type: 'species', count: 30 },
    { name: 'Goa Coast', lat: 15.2993, lng: 74.1240, type: 'edna', count: 40 },
  ];
  
  return locations.map(loc => ({
    ...loc,
    id: `${loc.name}-${Math.random().toString(36).substr(2, 9)}`,
    temperature: Math.random() * 10 + 20,
    salinity: Math.random() * 5 + 32,
    biodiversityIndex: Math.random() * 0.8 + 0.2,
  }));
};

// Custom icons for different data types
const createCustomIcon = (type: string, color: string) => {
  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="${color}">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
      </svg>
    `)}`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -24],
  });
};

const dataTypeConfig = {
  edna: { color: '#8b5cf6', label: 'eDNA Samples' },
  oceanographic: { color: '#0ea5e9', label: 'Oceanographic Data' },
  species: { color: '#10b981', label: 'Species Data' },
};

export default function GeographicPanel() {
  const [selectedLayers, setSelectedLayers] = useState(['oceanographic']);
  const [searchTerm, setSearchTerm] = useState('');
  const [mapView, setMapView] = useState<'normal' | 'satellite' | 'terrain'>('normal');
  const [realLocations, setRealLocations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Load real sampling locations
  useEffect(() => {
    const loadRealLocations = async () => {
      setLoading(true);
      try {
        const samplingPoints = await ApiService.getSamplingPoints();
        const oceanographicData = await ApiService.getOceanographicData({ limit: 100 });
        
        // Transform real data to map format
        const locations = oceanographicData.map((data, index) => ({
          id: data.id,
          name: `Sample Point ${index + 1}`,
          lat: data.location.latitude,
          lng: data.location.longitude,
          type: 'oceanographic',
          count: 1,
          temperature: data.parameter_type === 'temperature' ? data.value : null,
          salinity: data.parameter_type === 'salinity' ? data.value : null,
          biodiversityIndex: Math.random() * 0.8 + 0.2, // Mock for now
          parameter_type: data.parameter_type,
          value: data.value,
          unit: data.unit,
          timestamp: data.timestamp
        }));
        
        setRealLocations(locations);
      } catch (error) {
        console.error('Error loading real locations:', error);
        // Fallback to mock data
        setRealLocations(generateSampleLocations());
      } finally {
        setLoading(false);
      }
    };
    
    loadRealLocations();
  }, []);
  
  const sampleLocations = useMemo(() => 
    realLocations.length > 0 ? realLocations : generateSampleLocations(), 
    [realLocations]
  );

  const filteredLocations = useMemo(() => {
    return sampleLocations.filter(location => 
      selectedLayers.includes(location.type) &&
      location.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [sampleLocations, selectedLayers, searchTerm]);

  const handleLayerToggle = (layer: string) => {
    setSelectedLayers(prev => 
      prev.includes(layer)
        ? prev.filter(l => l !== layer)
        : [...prev, layer]
    );
  };

  const getTileLayerUrl = () => {
    switch (mapView) {
      case 'satellite':
        return 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
      case 'terrain':
        return 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}';
      default:
        return 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    }
  };

  const getHeatmapRadius = (count: number) => {
    return Math.max(count * 1000, 5000); // Minimum 5km radius
  };

  const getHeatmapColor = (biodiversityIndex: number) => {
    if (biodiversityIndex > 0.7) return '#10b981'; // High biodiversity - green
    if (biodiversityIndex > 0.5) return '#f59e0b'; // Medium biodiversity - yellow
    return '#ef4444'; // Low biodiversity - red
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Search className="w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search locations..."
              className="px-3 py-1 border border-gray-300 rounded-md text-sm w-48 focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-gray-500" />
            <select 
              value={mapView}
              onChange={(e) => setMapView(e.target.value as typeof mapView)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
            >
              <option value="normal">Normal View</option>
              <option value="satellite">Satellite View</option>
              <option value="terrain">Terrain View</option>
            </select>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-1 text-sm text-ocean-600 border border-ocean-300 rounded-md hover:bg-ocean-50 transition-colors">
            <Filter className="w-4 h-4" />
            <span>Filter</span>
          </button>
          
          <button className="flex items-center space-x-2 px-3 py-1 text-sm text-ocean-600 border border-ocean-300 rounded-md hover:bg-ocean-50 transition-colors">
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Layer Selection */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">Data Layers:</h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(dataTypeConfig).map(([key, config]) => (
            <button
              key={key}
              onClick={() => handleLayerToggle(key)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-sm transition-all ${
                selectedLayers.includes(key)
                  ? 'bg-gray-200 text-gray-800 border border-gray-300'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: config.color }}
              />
              <span>{config.label}</span>
              <span className="text-xs bg-gray-300 px-2 py-0.5 rounded-full">
                {sampleLocations.filter(loc => loc.type === key).length}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Map */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div style={{ height: '500px', width: '100%' }}>
          <MapContainer
            center={[15.0, 77.0]} // Center on India
            zoom={5}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url={getTileLayerUrl()}
              attribution={mapView === 'normal' 
                ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                : '&copy; Esri'
              }
            />
            
            {filteredLocations.map((location) => {
              const config = dataTypeConfig[location.type as keyof typeof dataTypeConfig];
              return (
                <React.Fragment key={location.id}>
                  {/* Sample point marker */}
                  <Marker
                    position={[location.lat, location.lng]}
                    icon={createCustomIcon(location.type, config.color)}
                  >
                    <Popup>
                      <div className="p-2 min-w-48">
                        <h3 className="font-semibold text-gray-900 mb-2">{location.name}</h3>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Type:</span>
                            <span className="font-medium">{config.label}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Parameter:</span>
                            <span className="font-medium">{location.parameter_type}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Value:</span>
                            <span className="font-medium">{location.value?.toFixed(2)} {location.unit}</span>
                          </div>
                          {location.temperature && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Temperature:</span>
                              <span className="font-medium">{location.temperature.toFixed(1)}°C</span>
                            </div>
                          )}
                          {location.salinity && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Salinity:</span>
                              <span className="font-medium">{location.salinity.toFixed(1)} PSU</span>
                            </div>
                          )}
                          <div className="flex justify-between">
                            <span className="text-gray-600">Biodiversity:</span>
                            <span className="font-medium">{(location.biodiversityIndex * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                        <div className="mt-2 pt-2 border-t border-gray-200">
                          <div className="text-xs text-gray-500">
                            Coordinates: {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
                          </div>
                          {location.timestamp && (
                            <div className="text-xs text-gray-500">
                              Date: {new Date(location.timestamp).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                  
                  {/* Biodiversity heatmap circle */}
                  <Circle
                    center={[location.lat, location.lng]}
                    radius={getHeatmapRadius(location.count)}
                    pathOptions={{
                      color: getHeatmapColor(location.biodiversityIndex),
                      weight: 1,
                      opacity: 0.3,
                      fillColor: getHeatmapColor(location.biodiversityIndex),
                      fillOpacity: 0.1,
                    }}
                  />
                </React.Fragment>
              );
            })}
          </MapContainer>
        </div>
      </div>

      {/* Legend and Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Legend */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h4 className="font-medium text-gray-900 mb-3">Map Legend</h4>
          <div className="space-y-3">
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-2">Data Types</h5>
              <div className="space-y-1">
                {Object.entries(dataTypeConfig).map(([key, config]) => (
                  <div key={key} className="flex items-center space-x-2 text-sm">
                    <div 
                      className="w-4 h-4 rounded-full flex-shrink-0" 
                      style={{ backgroundColor: config.color }}
                    />
                    <span>{config.label}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h5 className="text-sm font-medium text-gray-700 mb-2">Biodiversity Index</h5>
              <div className="space-y-1">
                <div className="flex items-center space-x-2 text-sm">
                  <div className="w-4 h-4 rounded-full bg-green-500 flex-shrink-0" />
                  <span>High (70-100%)</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <div className="w-4 h-4 rounded-full bg-yellow-500 flex-shrink-0" />
                  <span>Medium (50-70%)</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <div className="w-4 h-4 rounded-full bg-red-500 flex-shrink-0" />
                  <span>Low (20-50%)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h4 className="font-medium text-gray-900 mb-3">Sampling Statistics</h4>
          <div className="space-y-3">
            <div className="text-sm">
              <div className="flex justify-between mb-1">
                <span className="text-gray-600">Total Locations:</span>
                <span className="font-medium">{filteredLocations.length}</span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-gray-600">Total Samples:</span>
                <span className="font-medium">
                  {filteredLocations.reduce((sum, loc) => sum + loc.count, 0)}
                </span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-gray-600">Avg. Temperature:</span>
                <span className="font-medium">
                  {(filteredLocations.reduce((sum, loc) => sum + loc.temperature, 0) / filteredLocations.length).toFixed(1)}°C
                </span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-gray-600">Avg. Salinity:</span>
                <span className="font-medium">
                  {(filteredLocations.reduce((sum, loc) => sum + loc.salinity, 0) / filteredLocations.length).toFixed(1)} PSU
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Avg. Biodiversity:</span>
                <span className="font-medium">
                  {((filteredLocations.reduce((sum, loc) => sum + loc.biodiversityIndex, 0) / filteredLocations.length) * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-gray-200">
              <h5 className="text-sm font-medium text-gray-700 mb-2">By Data Type</h5>
              {Object.entries(dataTypeConfig).map(([key, config]) => {
                const typeLocations = filteredLocations.filter(loc => loc.type === key);
                const totalSamples = typeLocations.reduce((sum, loc) => sum + loc.count, 0);
                return (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-gray-600">{config.label}:</span>
                    <span className="font-medium">{totalSamples} samples</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}