import React, { useState } from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ScatterChart,
  Scatter,
  LineChart,
  Line,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { TrendingUp, PieChart as PieChartIcon, BarChart3, Filter, Download } from 'lucide-react';
import { useApp } from '../../../context/AppContext';

// Mock biodiversity data
const speciesDistributionData = [
  { name: 'Fish Species', count: 245, percentage: 45, color: '#0ea5e9' },
  { name: 'Marine Invertebrates', count: 189, percentage: 35, color: '#10b981' },
  { name: 'Coral Species', count: 67, percentage: 12, color: '#f59e0b' },
  { name: 'Marine Plants', count: 43, percentage: 8, color: '#8b5cf6' },
];

const diversityTrendsData = [
  { region: 'Arabian Sea', shannonIndex: 3.2, simpsonIndex: 0.85, speciesRichness: 156 },
  { region: 'Bay of Bengal', shannonIndex: 2.8, simpsonIndex: 0.78, speciesRichness: 143 },
  { region: 'Lakshadweep Sea', shannonIndex: 3.5, simpsonIndex: 0.92, speciesRichness: 98 },
  { region: 'Andaman Sea', shannonIndex: 3.8, simpsonIndex: 0.95, speciesRichness: 187 },
  { region: 'Gujarat Coast', shannonIndex: 2.1, simpsonIndex: 0.65, speciesRichness: 89 },
  { region: 'Tamil Nadu Coast', shannonIndex: 2.6, simpsonIndex: 0.74, speciesRichness: 112 },
];

const endemicSpeciesData = [
  { category: 'Endemic Fish', count: 23, threat_level: 'Low' },
  { category: 'Endemic Corals', count: 15, threat_level: 'Medium' },
  { category: 'Endemic Invertebrates', count: 31, threat_level: 'Low' },
  { category: 'Endemic Plants', count: 8, threat_level: 'High' },
];

const radarData = [
  { metric: 'Species Richness', current: 85, historical: 95, max: 100 },
  { metric: 'Shannon Diversity', current: 75, historical: 82, max: 100 },
  { metric: 'Simpson Index', current: 88, historical: 90, max: 100 },
  { metric: 'Evenness', current: 70, historical: 78, max: 100 },
  { metric: 'Endemic Species', current: 60, historical: 85, max: 100 },
  { metric: 'Conservation Status', current: 45, historical: 65, max: 100 },
];

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4'];

const chartTypes = [
  { id: 'pie', label: 'Species Distribution', icon: PieChartIcon },
  { id: 'bar', label: 'Regional Diversity', icon: BarChart3 },
  { id: 'scatter', label: 'Diversity Indices', icon: TrendingUp },
  { id: 'radar', label: 'Conservation Metrics', icon: TrendingUp },
];

export default function BiodiversityPanel() {
  const { state } = useApp();
  const [selectedChart, setSelectedChart] = useState('pie');
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [timeRange, setTimeRange] = useState('current');

  const renderChart = () => {
    switch (selectedChart) {
      case 'pie':
        return (
          <div className="space-y-4">
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={speciesDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name}: ${percentage}%`}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {speciesDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value} species`, 'Count']} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              {speciesDistributionData.map((item, index) => (
                <div key={index} className="text-center p-3 bg-gray-50 rounded-lg">
                  <div 
                    className="w-4 h-4 rounded-full mx-auto mb-2" 
                    style={{ backgroundColor: item.color }}
                  />
                  <div className="text-sm text-gray-600">{item.name}</div>
                  <div className="text-lg font-semibold text-gray-900">{item.count}</div>
                  <div className="text-xs text-gray-500">{item.percentage}%</div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={diversityTrendsData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="shannonIndex" fill="#0ea5e9" name="Shannon Diversity Index" />
              <Bar dataKey="simpsonIndex" fill="#10b981" name="Simpson Diversity Index" />
              <Bar dataKey="speciesRichness" fill="#f59e0b" name="Species Richness" yAxisId="right" />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid />
              <XAxis 
                type="number" 
                dataKey="shannonIndex" 
                name="Shannon Index"
                domain={[0, 4]}
              />
              <YAxis 
                type="number" 
                dataKey="simpsonIndex" 
                name="Simpson Index"
                domain={[0, 1]}
              />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter 
                name="Regions" 
                data={diversityTrendsData} 
                fill="#8b5cf6"
              />
            </ScatterChart>
          </ResponsiveContainer>
        );

      case 'radar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" className="text-sm" />
              <PolarRadiusAxis domain={[0, 100]} className="text-xs" />
              <Radar
                name="Current"
                dataKey="current"
                stroke="#0ea5e9"
                fill="#0ea5e9"
                fillOpacity={0.3}
                strokeWidth={2}
              />
              <Radar
                name="Historical"
                dataKey="historical"
                stroke="#ef4444"
                fill="#ef4444"
                fillOpacity={0.1}
                strokeWidth={2}
                strokeDasharray="5 5"
              />
              <Legend />
              <Tooltip />
            </RadarChart>
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
            {diversityTrendsData.map(region => (
              <option key={region.region} value={region.region}>{region.region}</option>
            ))}
          </select>

          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
          >
            <option value="current">Current Year</option>
            <option value="5year">Last 5 Years</option>
            <option value="10year">Last 10 Years</option>
            <option value="historical">Historical Trend</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 text-sm text-ocean-600 border border-ocean-300 rounded-md hover:bg-ocean-50 transition-colors">
            <Filter className="w-4 h-4" />
            <span>Filter</span>
          </button>
          
          <button 
            onClick={() => {
              const exportData = {
                chart_type: selectedChart,
                region: selectedRegion,
                time_range: timeRange,
                species_distribution: speciesDistributionData,
                diversity_trends: diversityTrendsData,
                endemic_species: endemicSpeciesData,
                exported_at: new Date().toISOString()
              };
              const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `biodiversity_analysis_${Date.now()}.json`;
              a.click();
              URL.revokeObjectURL(url);
              alert('Biodiversity data exported successfully!');
            }}
            className="flex items-center space-x-2 px-3 py-2 text-sm text-ocean-600 border border-ocean-300 rounded-md hover:bg-ocean-50 transition-colors"
          >
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
            {selectedChart === 'pie' && 'Distribution of species across different taxonomic groups'}
            {selectedChart === 'bar' && 'Biodiversity indices comparison across marine regions'}
            {selectedChart === 'scatter' && 'Relationship between Shannon and Simpson diversity indices'}
            {selectedChart === 'radar' && 'Current vs historical conservation and biodiversity metrics'}
          </p>
        </div>
        
        {renderChart()}
      </div>

      {/* Additional Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Key Metrics */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h4 className="font-medium text-gray-900 mb-3">Key Biodiversity Metrics</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Total Species Count</span>
              <span className="font-semibold text-gray-900">544</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Endemic Species</span>
              <span className="font-semibold text-gray-900">77</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Threatened Species</span>
              <span className="font-semibold text-red-600">23</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Average Shannon Index</span>
              <span className="font-semibold text-gray-900">3.0</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Average Simpson Index</span>
              <span className="font-semibold text-gray-900">0.82</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-gray-600">Biodiversity Health Score</span>
              <span className="font-semibold text-green-600">78%</span>
            </div>
          </div>
        </div>

        {/* Endemic Species Status */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h4 className="font-medium text-gray-900 mb-3">Endemic Species Status</h4>
          <div className="space-y-3">
            {endemicSpeciesData.map((item, index) => {
              const threatColors = {
                Low: 'text-green-600 bg-green-50',
                Medium: 'text-yellow-600 bg-yellow-50',
                High: 'text-red-600 bg-red-50',
              };
              const threatColor = threatColors[item.threat_level as keyof typeof threatColors];

              return (
                <div key={index} className="flex items-center justify-between py-2">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{item.category}</div>
                    <div className="text-sm text-gray-500">{item.count} species identified</div>
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${threatColor}`}>
                    {item.threat_level} Risk
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-4 pt-3 border-t border-gray-200">
            <div className="text-sm text-gray-600">
              <strong>Conservation Priority:</strong> Focus on high-risk endemic species, 
              particularly marine plants which show the highest threat level.
            </div>
          </div>
        </div>
      </div>

      {/* Regional Comparison Table */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="font-medium text-gray-900 mb-3">Regional Biodiversity Comparison</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 font-medium text-gray-900">Region</th>
                <th className="text-right py-2 font-medium text-gray-900">Species Richness</th>
                <th className="text-right py-2 font-medium text-gray-900">Shannon Index</th>
                <th className="text-right py-2 font-medium text-gray-900">Simpson Index</th>
                <th className="text-right py-2 font-medium text-gray-900">Status</th>
              </tr>
            </thead>
            <tbody>
              {diversityTrendsData.map((region, index) => (
                <tr key={index} className="border-b border-gray-100">
                  <td className="py-2 font-medium text-gray-900">{region.region}</td>
                  <td className="text-right py-2">{region.speciesRichness}</td>
                  <td className="text-right py-2">{region.shannonIndex.toFixed(1)}</td>
                  <td className="text-right py-2">{region.simpsonIndex.toFixed(2)}</td>
                  <td className="text-right py-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      region.shannonIndex > 3.5 ? 'text-green-600 bg-green-50' :
                      region.shannonIndex > 2.5 ? 'text-yellow-600 bg-yellow-50' :
                      'text-red-600 bg-red-50'
                    }`}>
                      {region.shannonIndex > 3.5 ? 'Excellent' : 
                       region.shannonIndex > 2.5 ? 'Good' : 'Needs Attention'}
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