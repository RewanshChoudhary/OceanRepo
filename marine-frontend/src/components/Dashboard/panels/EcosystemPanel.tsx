import React, { useState } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ComposedChart,
  ScatterChart,
  Scatter
} from 'recharts';
import { 
  Activity, 
  Thermometer, 
  Droplets, 
  Wind, 
  Eye, 
  AlertTriangle, 
  TrendingUp,
  Filter,
  Download
} from 'lucide-react';
import { useApp } from '../../../context/AppContext';

// Mock ecosystem health data
const ecosystemHealthData = [
  { 
    region: 'Arabian Sea', 
    healthScore: 78, 
    temperature: 26.5, 
    salinity: 36.2, 
    pH: 8.1, 
    dissolvedOxygen: 6.8,
    turbidity: 12,
    pollutionIndex: 23,
    coralCoverage: 45
  },
  { 
    region: 'Bay of Bengal', 
    healthScore: 65, 
    temperature: 28.2, 
    salinity: 34.8, 
    pH: 7.9, 
    dissolvedOxygen: 5.4,
    turbidity: 18,
    pollutionIndex: 35,
    coralCoverage: 32
  },
  { 
    region: 'Lakshadweep Sea', 
    healthScore: 89, 
    temperature: 27.8, 
    salinity: 35.1, 
    pH: 8.3, 
    dissolvedOxygen: 7.2,
    turbidity: 8,
    pollutionIndex: 12,
    coralCoverage: 78
  },
  { 
    region: 'Andaman Sea', 
    healthScore: 82, 
    temperature: 27.2, 
    salinity: 34.5, 
    pH: 8.2, 
    dissolvedOxygen: 6.9,
    turbidity: 10,
    pollutionIndex: 18,
    coralCoverage: 65
  },
];

const timeSeriesData = Array.from({ length: 12 }, (_, i) => ({
  month: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i],
  temperature: 25 + Math.sin(i * 0.5) * 3 + Math.random() * 2,
  pH: 7.8 + Math.sin(i * 0.3) * 0.3 + Math.random() * 0.2,
  dissolvedOxygen: 6 + Math.sin(i * 0.4) * 1 + Math.random() * 0.5,
  pollutionIndex: 20 + Math.sin(i * 0.6) * 10 + Math.random() * 5,
  healthScore: 75 + Math.sin(i * 0.2) * 10 + Math.random() * 5,
}));

const threats = [
  { name: 'Ocean Acidification', severity: 'High', trend: 'Increasing', regions: 4 },
  { name: 'Temperature Rise', severity: 'High', trend: 'Increasing', regions: 6 },
  { name: 'Pollution', severity: 'Medium', trend: 'Stable', regions: 3 },
  { name: 'Overfishing', severity: 'Medium', trend: 'Decreasing', regions: 5 },
  { name: 'Habitat Loss', severity: 'Low', trend: 'Stable', regions: 2 },
];

const chartTypes = [
  { id: 'health', label: 'Health Overview', icon: Activity },
  { id: 'environmental', label: 'Environmental Parameters', icon: Thermometer },
  { id: 'trends', label: 'Temporal Trends', icon: TrendingUp },
  { id: 'threats', label: 'Threat Analysis', icon: AlertTriangle },
];

export default function EcosystemPanel() {
  const { state } = useApp();
  const [selectedChart, setSelectedChart] = useState('health');
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [timeRange, setTimeRange] = useState('12months');

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getThreatColor = (severity: string) => {
    switch (severity) {
      case 'High': return 'text-red-600 bg-red-50';
      case 'Medium': return 'text-yellow-600 bg-yellow-50';
      case 'Low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'Increasing': return '↗️';
      case 'Decreasing': return '↘️';
      case 'Stable': return '➡️';
      default: return '❓';
    }
  };

  const renderChart = () => {
    switch (selectedChart) {
      case 'health':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={ecosystemHealthData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" angle={-45} textAnchor="end" height={100} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Bar 
                dataKey="healthScore" 
                fill="#10b981" 
                name="Ecosystem Health Score (%)"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'environmental':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={ecosystemHealthData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" angle={-45} textAnchor="end" height={100} />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="temperature" fill="#f59e0b" name="Temperature (°C)" />
              <Line yAxisId="right" type="monotone" dataKey="pH" stroke="#8b5cf6" name="pH Level" strokeWidth={3} />
              <Line yAxisId="left" type="monotone" dataKey="dissolvedOxygen" stroke="#0ea5e9" name="Dissolved Oxygen (mg/L)" strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
        );

      case 'trends':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={timeSeriesData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="healthScore" 
                stroke="#10b981" 
                strokeWidth={3}
                name="Health Score (%)"
                dot={{ r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="temperature" 
                stroke="#f59e0b" 
                strokeWidth={2}
                name="Temperature (°C)"
                dot={{ r: 3 }}
              />
              <Line 
                type="monotone" 
                dataKey="pH" 
                stroke="#8b5cf6" 
                strokeWidth={2}
                name="pH Level"
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'threats':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid />
              <XAxis 
                type="number" 
                dataKey="pollutionIndex" 
                name="Pollution Index"
                domain={[0, 50]}
              />
              <YAxis 
                type="number" 
                dataKey="healthScore" 
                name="Health Score"
                domain={[40, 100]}
              />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter 
                name="Regions" 
                data={ecosystemHealthData} 
                fill="#ef4444"
                r={8}
              />
            </ScatterChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="flex rounded-lg border border-gray-300 overflow-hidden">
            {chartTypes.map((chart) => (
              <button
                key={chart.id}
                onClick={() => setSelectedChart(chart.id)}
                className={`flex items-center space-x-2 px-3 py-2 text-sm transition-all ${
                  selectedChart === chart.id
                    ? 'bg-ocean-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                <chart.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{chart.label}</span>
              </button>
            ))}
          </div>

          <select 
            value={selectedRegion}
            onChange={(e) => setSelectedRegion(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
          >
            <option value="all">All Regions</option>
            {ecosystemHealthData.map(region => (
              <option key={region.region} value={region.region}>{region.region}</option>
            ))}
          </select>

          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
          >
            <option value="6months">Last 6 Months</option>
            <option value="12months">Last 12 Months</option>
            <option value="2years">Last 2 Years</option>
            <option value="5years">Last 5 Years</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 text-sm text-ocean-600 border border-ocean-300 rounded-md hover:bg-ocean-50 transition-colors">
            <Filter className="w-4 h-4" />
            <span>Filter</span>
          </button>
          
          <button className="flex items-center space-x-2 px-3 py-2 text-sm text-ocean-600 border border-ocean-300 rounded-md hover:bg-ocean-50 transition-colors">
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            {chartTypes.find(c => c.id === selectedChart)?.label}
          </h3>
          <p className="text-sm text-gray-600">
            {selectedChart === 'health' && 'Overall ecosystem health scores across marine regions'}
            {selectedChart === 'environmental' && 'Key environmental parameters affecting ecosystem health'}
            {selectedChart === 'trends' && 'Temporal trends in ecosystem health and environmental conditions'}
            {selectedChart === 'threats' && 'Correlation between pollution levels and ecosystem health'}
          </p>
        </div>
        
        {renderChart()}
      </div>

      {/* Health Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {ecosystemHealthData.map((region, index) => (
          <div key={index} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-gray-900 truncate">{region.region}</h4>
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${getHealthColor(region.healthScore)}`}>
                {region.healthScore}%
              </div>
            </div>
            
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Thermometer className="w-3 h-3 text-red-500" />
                  <span className="text-gray-600">Temp</span>
                </div>
                <span className="font-medium">{region.temperature.toFixed(1)}°C</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Droplets className="w-3 h-3 text-blue-500" />
                  <span className="text-gray-600">pH</span>
                </div>
                <span className="font-medium">{region.pH.toFixed(1)}</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Wind className="w-3 h-3 text-green-500" />
                  <span className="text-gray-600">DO</span>
                </div>
                <span className="font-medium">{region.dissolvedOxygen.toFixed(1)} mg/L</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1">
                  <Eye className="w-3 h-3 text-purple-500" />
                  <span className="text-gray-600">Coral</span>
                </div>
                <span className="font-medium">{region.coralCoverage}%</span>
              </div>
            </div>
            
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center space-x-1 text-xs text-gray-500">
                <AlertTriangle className="w-3 h-3" />
                <span>Pollution Index: {region.pollutionIndex}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Threats and Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Threat Assessment */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h4 className="font-medium text-gray-900 mb-3">Current Threats</h4>
          <div className="space-y-3">
            {threats.map((threat, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">{threat.name}</span>
                    <span className="text-lg">{getTrendIcon(threat.trend)}</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    Affecting {threat.regions} regions • {threat.trend}
                  </div>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${getThreatColor(threat.severity)}`}>
                  {threat.severity}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Ecosystem Metrics */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h4 className="font-medium text-gray-900 mb-3">Key Ecosystem Metrics</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Overall Health Score</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full">
                  <div 
                    className="h-2 bg-green-500 rounded-full" 
                    style={{ width: '78%' }}
                  />
                </div>
                <span className="font-semibold text-gray-900">78%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Biodiversity Index</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full">
                  <div 
                    className="h-2 bg-blue-500 rounded-full" 
                    style={{ width: '72%' }}
                  />
                </div>
                <span className="font-semibold text-gray-900">72%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Water Quality</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full">
                  <div 
                    className="h-2 bg-yellow-500 rounded-full" 
                    style={{ width: '65%' }}
                  />
                </div>
                <span className="font-semibold text-gray-900">65%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Habitat Integrity</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full">
                  <div 
                    className="h-2 bg-green-500 rounded-full" 
                    style={{ width: '82%' }}
                  />
                </div>
                <span className="font-semibold text-gray-900">82%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Resilience Score</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-gray-200 rounded-full">
                  <div 
                    className="h-2 bg-orange-500 rounded-full" 
                    style={{ width: '58%' }}
                  />
                </div>
                <span className="font-semibold text-gray-900">58%</span>
              </div>
            </div>
          </div>
          
          <div className="mt-4 pt-3 border-t border-gray-200 text-sm text-gray-600">
            <strong>Recommendation:</strong> Focus conservation efforts on improving water quality 
            and ecosystem resilience, particularly in the Bay of Bengal region.
          </div>
        </div>
      </div>

      {/* Environmental Parameters Table */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="font-medium text-gray-900 mb-3">Environmental Parameters by Region</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 font-medium text-gray-900">Region</th>
                <th className="text-right py-2 font-medium text-gray-900">Temperature (°C)</th>
                <th className="text-right py-2 font-medium text-gray-900">Salinity (PSU)</th>
                <th className="text-right py-2 font-medium text-gray-900">pH</th>
                <th className="text-right py-2 font-medium text-gray-900">DO (mg/L)</th>
                <th className="text-right py-2 font-medium text-gray-900">Turbidity</th>
                <th className="text-right py-2 font-medium text-gray-900">Status</th>
              </tr>
            </thead>
            <tbody>
              {ecosystemHealthData.map((region, index) => (
                <tr key={index} className="border-b border-gray-100">
                  <td className="py-2 font-medium text-gray-900">{region.region}</td>
                  <td className="text-right py-2">{region.temperature.toFixed(1)}</td>
                  <td className="text-right py-2">{region.salinity.toFixed(1)}</td>
                  <td className="text-right py-2">{region.pH.toFixed(1)}</td>
                  <td className="text-right py-2">{region.dissolvedOxygen.toFixed(1)}</td>
                  <td className="text-right py-2">{region.turbidity}</td>
                  <td className="text-right py-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getHealthColor(region.healthScore)}`}>
                      {region.healthScore >= 80 ? 'Excellent' : 
                       region.healthScore >= 60 ? 'Good' : 'Poor'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}