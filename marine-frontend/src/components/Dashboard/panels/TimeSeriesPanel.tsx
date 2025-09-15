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
  Bar
} from 'recharts';
import { Calendar, Filter, Download } from 'lucide-react';
import { useApp } from '../../../context/AppContext';

// Mock data for time series - in real app this would come from API
const generateTimeSeriesData = () => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return months.map(month => ({
    month,
    species: Math.floor(Math.random() * 50) + 100,
    edna_samples: Math.floor(Math.random() * 30) + 80,
    oceanographic: Math.floor(Math.random() * 40) + 120,
    temperature: Math.random() * 5 + 20,
    salinity: Math.random() * 2 + 34,
  }));
};

const chartTypes = [
  { id: 'line', label: 'Line Chart', component: 'LineChart' },
  { id: 'area', label: 'Area Chart', component: 'AreaChart' },
  { id: 'bar', label: 'Bar Chart', component: 'BarChart' },
];

const dataMetrics = [
  { id: 'species', label: 'Species Count', color: '#10b981' },
  { id: 'edna_samples', label: 'eDNA Samples', color: '#8b5cf6' },
  { id: 'oceanographic', label: 'Oceanographic Data', color: '#0ea5e9' },
  { id: 'temperature', label: 'Temperature (°C)', color: '#f59e0b' },
  { id: 'salinity', label: 'Salinity (PSU)', color: '#ef4444' },
];

export default function TimeSeriesPanel() {
  const { state } = useApp();
  const [selectedChart, setSelectedChart] = useState('line');
  const [selectedMetrics, setSelectedMetrics] = useState(['species', 'edna_samples', 'oceanographic']);
  const [timeRange, setTimeRange] = useState('12months');
  
  const data = generateTimeSeriesData();

  const handleMetricToggle = (metricId: string) => {
    setSelectedMetrics(prev => 
      prev.includes(metricId) 
        ? prev.filter(id => id !== metricId)
        : [...prev, metricId]
    );
  };

  const renderChart = () => {
    const chartProps = {
      width: '100%',
      height: 400,
      data,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    };

    switch (selectedChart) {
      case 'area':
        return (
          <ResponsiveContainer {...chartProps}>
            <AreaChart data={data}>
              <defs>
                {selectedMetrics.map((metric) => {
                  const color = dataMetrics.find(m => m.id === metric)?.color || '#8884d8';
                  return (
                    <linearGradient key={metric} id={`gradient-${metric}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={color} stopOpacity={0.8}/>
                      <stop offset="95%" stopColor={color} stopOpacity={0.1}/>
                    </linearGradient>
                  );
                })}
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              {selectedMetrics.map((metric) => {
                const config = dataMetrics.find(m => m.id === metric);
                return (
                  <Area
                    key={metric}
                    type="monotone"
                    dataKey={metric}
                    stackId="1"
                    stroke={config?.color}
                    fill={`url(#gradient-${metric})`}
                    name={config?.label}
                  />
                );
              })}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer {...chartProps}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              {selectedMetrics.map((metric) => {
                const config = dataMetrics.find(m => m.id === metric);
                return (
                  <Bar
                    key={metric}
                    dataKey={metric}
                    fill={config?.color}
                    name={config?.label}
                  />
                );
              })}
            </BarChart>
          </ResponsiveContainer>
        );

      default:
        return (
          <ResponsiveContainer {...chartProps}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              {selectedMetrics.map((metric) => {
                const config = dataMetrics.find(m => m.id === metric);
                return (
                  <Line
                    key={metric}
                    type="monotone"
                    dataKey={metric}
                    stroke={config?.color}
                    strokeWidth={2}
                    name={config?.label}
                    dot={{ r: 4 }}
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
            >
              <option value="3months">Last 3 Months</option>
              <option value="6months">Last 6 Months</option>
              <option value="12months">Last 12 Months</option>
              <option value="2years">Last 2 Years</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select 
              value={selectedChart}
              onChange={(e) => setSelectedChart(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
            >
              {chartTypes.map(chart => (
                <option key={chart.id} value={chart.id}>{chart.label}</option>
              ))}
            </select>
          </div>
        </div>

        <button 
          onClick={() => {
            const data = {
              chart_type: selectedChart,
              metrics: selectedMetrics,
              time_range: timeRange,
              data: timeSeriesData,
              exported_at: new Date().toISOString()
            };
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `time_series_data_${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            alert('Time series data exported successfully!');
          }}
          className="flex items-center space-x-2 px-3 py-1 text-sm text-ocean-600 border border-ocean-300 rounded-md hover:bg-ocean-50 transition-colors"
        >
          <Download className="w-4 h-4" />
          <span>Export</span>
        </button>
      </div>

      {/* Metric Selection */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">Select Metrics to Display:</h4>
        <div className="flex flex-wrap gap-2">
          {dataMetrics.map(metric => (
            <button
              key={metric.id}
              onClick={() => handleMetricToggle(metric.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-sm transition-all ${
                selectedMetrics.includes(metric.id)
                  ? 'bg-gray-200 text-gray-800 border border-gray-300'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: metric.color }}
              />
              <span>{metric.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {selectedMetrics.length > 0 ? (
          renderChart()
        ) : (
          <div className="h-96 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">📊</div>
              <p className="text-lg font-medium">Select at least one metric to display</p>
              <p className="text-sm">Choose from the options above to visualize your data</p>
            </div>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        {selectedMetrics.slice(0, 3).map(metricId => {
          const metric = dataMetrics.find(m => m.id === metricId);
          const values = data.map(d => d[metricId as keyof typeof d] as number);
          const avg = values.reduce((a, b) => a + b, 0) / values.length;
          const max = Math.max(...values);
          const min = Math.min(...values);

          return (
            <div key={metricId} className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center space-x-2 mb-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: metric?.color }}
                />
                <h5 className="font-medium text-gray-900">{metric?.label}</h5>
              </div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Average:</span>
                  <span className="font-medium">{avg.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Max:</span>
                  <span className="font-medium">{max.toFixed(1)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Min:</span>
                  <span className="font-medium">{min.toFixed(1)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}