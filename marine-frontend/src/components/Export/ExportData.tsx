import React, { useState } from 'react';
import { Download, FileText, Calendar, Filter, Settings, CheckCircle, Loader2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface ExportConfig {
  format: 'csv' | 'excel' | 'json' | 'pdf';
  dataTypes: string[];
  dateRange: {
    start: string;
    end: string;
  };
  filters: {
    regions?: string[];
    species?: string[];
    parameters?: string[];
  };
  includeMetadata: boolean;
  includeCharts: boolean;
}

interface ExportJob {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  config: ExportConfig;
  createdAt: string;
  completedAt?: string;
  downloadUrl?: string;
  errorMessage?: string;
}

export default function ExportData() {
  const { state } = useApp();
  const { databaseStats } = state;

  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    format: 'csv',
    dataTypes: ['species'],
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0],
    },
    filters: {},
    includeMetadata: true,
    includeCharts: false,
  });

  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [isExporting, setIsExporting] = useState(false);

  const dataTypeOptions = [
    { value: 'species', label: 'Species Data', count: databaseStats?.species_count || 0, icon: '🐟' },
    { value: 'edna', label: 'eDNA Sequences', count: databaseStats?.edna_count || 0, icon: '🧬' },
    { value: 'oceanographic', label: 'Oceanographic Data', count: databaseStats?.oceanographic_count || 0, icon: '🌊' },
    { value: 'taxonomy', label: 'Taxonomy Records', count: databaseStats?.species_count || 0, icon: '📋' },
  ];

  const formatOptions = [
    { value: 'csv', label: 'CSV', description: 'Comma-separated values', icon: '📄' },
    { value: 'excel', label: 'Excel', description: 'Microsoft Excel spreadsheet', icon: '📊' },
    { value: 'json', label: 'JSON', description: 'JavaScript Object Notation', icon: '🔧' },
    { value: 'pdf', label: 'PDF Report', description: 'Formatted report with charts', icon: '📑' },
  ];

  const regionOptions = [
    'Arabian Sea', 'Bay of Bengal', 'Lakshadweep Sea', 'Andaman Sea',
    'Gujarat Coast', 'Tamil Nadu Coast', 'Kerala Coast', 'Odisha Coast'
  ];

  const handleExport = async () => {
    const jobId = Date.now().toString();
    const exportJob: ExportJob = {
      id: jobId,
      name: `${exportConfig.dataTypes.join(', ')} Export`,
      status: 'pending',
      progress: 0,
      config: exportConfig,
      createdAt: new Date().toISOString(),
    };

    setExportJobs(prev => [exportJob, ...prev]);
    setIsExporting(true);

    // Simulate export process
    try {
      // Update status to processing
      setExportJobs(prev => prev.map(job =>
        job.id === jobId ? { ...job, status: 'processing' } : job
      ));

      // Simulate progress
      for (let progress = 10; progress <= 100; progress += 10) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setExportJobs(prev => prev.map(job =>
          job.id === jobId ? { ...job, progress } : job
        ));
      }

      // Complete export
      const downloadUrl = `${window.location.origin}/exports/export_${jobId}.${exportConfig.format}`;
      setExportJobs(prev => prev.map(job =>
        job.id === jobId ? {
          ...job,
          status: 'completed',
          completedAt: new Date().toISOString(),
          downloadUrl
        } : job
      ));

    } catch (error) {
      setExportJobs(prev => prev.map(job =>
        job.id === jobId ? {
          ...job,
          status: 'error',
          errorMessage: 'Export failed. Please try again.'
        } : job
      ));
    } finally {
      setIsExporting(false);
    }
  };

  const handleDownload = (job: ExportJob) => {
    // Simulate file download
    const element = document.createElement('a');
    element.href = '#';
    element.download = `marine_data_export_${job.id}.${job.config.format}`;
    element.click();
    alert(`Downloading ${job.name} in ${job.config.format.toUpperCase()} format`);
  };

  const updateDataTypes = (dataType: string) => {
    setExportConfig(prev => ({
      ...prev,
      dataTypes: prev.dataTypes.includes(dataType)
        ? prev.dataTypes.filter(type => type !== dataType)
        : [...prev.dataTypes, dataType]
    }));
  };

  const updateRegionFilter = (region: string) => {
    setExportConfig(prev => ({
      ...prev,
      filters: {
        ...prev.filters,
        regions: prev.filters.regions?.includes(region)
          ? prev.filters.regions.filter(r => r !== region)
          : [...(prev.filters.regions || []), region]
      }
    }));
  };

  const getStatusIcon = (status: ExportJob['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <div className="w-5 h-5 rounded-full bg-red-500" />;
      case 'processing':
        return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />;
      default:
        return <div className="w-5 h-5 rounded-full bg-gray-300" />;
    }
  };

  const getTotalRecords = () => {
    return exportConfig.dataTypes.reduce((total, type) => {
      const option = dataTypeOptions.find(opt => opt.value === type);
      return total + (option?.count || 0);
    }, 0);
  };

  return (
    <div className="space-y-6">
      {/* Export Configuration */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Export Configuration</h2>

        {/* Data Types Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">Select Data Types</label>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {dataTypeOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => updateDataTypes(option.value)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  exportConfig.dataTypes.includes(option.value)
                    ? 'border-ocean-500 bg-ocean-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-2">{option.icon}</div>
                <div className="font-medium text-gray-900 text-sm">{option.label}</div>
                <div className="text-xs text-gray-500">{option.count.toLocaleString()} records</div>
              </button>
            ))}
          </div>
        </div>

        {/* Format Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">Export Format</label>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {formatOptions.map((format) => (
              <button
                key={format.value}
                onClick={() => setExportConfig(prev => ({ ...prev, format: format.value as any }))}
                className={`p-4 rounded-lg border-2 transition-all ${
                  exportConfig.format === format.value
                    ? 'border-ocean-500 bg-ocean-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-2">{format.icon}</div>
                <div className="font-medium text-gray-900 text-sm">{format.label}</div>
                <div className="text-xs text-gray-500">{format.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={exportConfig.dateRange.start}
              onChange={(e) => setExportConfig(prev => ({
                ...prev,
                dateRange: { ...prev.dateRange, start: e.target.value }
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={exportConfig.dateRange.end}
              onChange={(e) => setExportConfig(prev => ({
                ...prev,
                dateRange: { ...prev.dateRange, end: e.target.value }
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
            />
          </div>
        </div>

        {/* Region Filters */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">Filter by Region (Optional)</label>
          <div className="flex flex-wrap gap-2">
            {regionOptions.map((region) => (
              <button
                key={region}
                onClick={() => updateRegionFilter(region)}
                className={`px-3 py-1 rounded-full text-sm transition-all ${
                  exportConfig.filters.regions?.includes(region)
                    ? 'bg-ocean-100 text-ocean-800 border border-ocean-300'
                    : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
                }`}
              >
                {region}
              </button>
            ))}
          </div>
        </div>

        {/* Options */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">Export Options</label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={exportConfig.includeMetadata}
                onChange={(e) => setExportConfig(prev => ({ ...prev, includeMetadata: e.target.checked }))}
                className="rounded border-gray-300 text-ocean-600 focus:ring-ocean-500"
              />
              <span className="ml-2 text-sm text-gray-600">Include metadata and data collection info</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={exportConfig.includeCharts}
                onChange={(e) => setExportConfig(prev => ({ ...prev, includeCharts: e.target.checked }))}
                className="rounded border-gray-300 text-ocean-600 focus:ring-ocean-500"
                disabled={exportConfig.format !== 'pdf'}
              />
              <span className={`ml-2 text-sm ${exportConfig.format !== 'pdf' ? 'text-gray-400' : 'text-gray-600'}`}>
                Include charts and visualizations (PDF only)
              </span>
            </label>
          </div>
        </div>

        {/* Export Summary */}
        <div className="bg-ocean-50 border border-ocean-200 rounded-lg p-4 mb-6">
          <h4 className="font-medium text-ocean-900 mb-2">Export Summary</h4>
          <div className="text-sm text-ocean-800">
            <p>• Data types: {exportConfig.dataTypes.length > 0 ? exportConfig.dataTypes.join(', ') : 'None selected'}</p>
            <p>• Format: {formatOptions.find(f => f.value === exportConfig.format)?.label}</p>
            <p>• Date range: {exportConfig.dateRange.start} to {exportConfig.dateRange.end}</p>
            <p>• Estimated records: {getTotalRecords().toLocaleString()}</p>
            {exportConfig.filters.regions && exportConfig.filters.regions.length > 0 && (
              <p>• Regions: {exportConfig.filters.regions.join(', ')}</p>
            )}
          </div>
        </div>

        {/* Export Button */}
        <button
          onClick={handleExport}
          disabled={isExporting || exportConfig.dataTypes.length === 0}
          className="w-full flex items-center justify-center space-x-2 px-6 py-3 bg-ocean-600 text-white rounded-lg hover:bg-ocean-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isExporting ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Preparing Export...</span>
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              <span>Generate Export</span>
            </>
          )}
        </button>
      </div>

      {/* Export Jobs */}
      {exportJobs.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Exports</h3>
          <div className="space-y-3">
            {exportJobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(job.status)}
                  <div>
                    <p className="font-medium text-gray-900">{job.name}</p>
                    <div className="flex items-center space-x-2 text-sm text-gray-500">
                      <span>{job.config.format.toUpperCase()}</span>
                      <span>•</span>
                      <span>{new Date(job.createdAt).toLocaleDateString()}</span>
                      {job.status === 'processing' && (
                        <>
                          <span>•</span>
                          <span>{job.progress}%</span>
                        </>
                      )}
                    </div>
                    {job.status === 'error' && job.errorMessage && (
                      <p className="text-sm text-red-600 mt-1">{job.errorMessage}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {job.status === 'processing' && (
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                  )}
                  
                  {job.status === 'completed' && (
                    <button
                      onClick={() => handleDownload(job)}
                      className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      <span>Download</span>
                    </button>
                  )}
                  
                  {job.status === 'error' && (
                    <button
                      onClick={() => setExportJobs(prev => prev.filter(j => j.id !== job.id))}
                      className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                    >
                      Remove
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pre-built Reports */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Reports</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              name: 'Species Summary Report',
              description: 'Complete species database with taxonomy',
              icon: '🐟',
              dataTypes: ['species', 'taxonomy'],
            },
            {
              name: 'eDNA Analysis Report',
              description: 'All eDNA sequences with identification results',
              icon: '🧬',
              dataTypes: ['edna'],
            },
            {
              name: 'Oceanographic Dataset',
              description: 'Environmental parameters and measurements',
              icon: '🌊',
              dataTypes: ['oceanographic'],
            },
          ].map((report, index) => (
            <button
              key={index}
              onClick={() => setExportConfig(prev => ({ ...prev, dataTypes: report.dataTypes }))}
              className="p-4 text-left border border-gray-200 rounded-lg hover:border-ocean-300 hover:bg-ocean-50 transition-all"
            >
              <div className="text-2xl mb-2">{report.icon}</div>
              <h4 className="font-medium text-gray-900 mb-1">{report.name}</h4>
              <p className="text-sm text-gray-600">{report.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}