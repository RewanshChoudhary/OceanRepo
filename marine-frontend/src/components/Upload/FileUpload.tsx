import React, { useState, useRef } from 'react';
import { Upload, X, FileText, CheckCircle, AlertCircle, Download, RefreshCw } from 'lucide-react';
import { ApiService } from '../../services/api';
import { useApp } from '../../context/AppContext';

interface UploadFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  errorMessage?: string;
  fileId?: string;
  processingResults?: any;
}

const SUPPORTED_FORMATS = {
  'text/csv': 'CSV files',
  'application/json': 'JSON files',
  'text/plain': 'Text files (eDNA sequences)',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel files',
  'application/vnd.ms-excel': 'Excel files (legacy)'
};

export default function FileUpload() {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadType, setUploadType] = useState<'edna' | 'oceanographic' | 'species' | 'taxonomy'>('edna');
  const [description, setDescription] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { loadDatabaseStats } = useApp();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    processFiles(droppedFiles);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    processFiles(selectedFiles);
  };

  const processFiles = (fileList: File[]) => {
    const validFiles = fileList.filter(file => {
      return Object.keys(SUPPORTED_FORMATS).includes(file.type) || 
             file.name.endsWith('.fasta') || 
             file.name.endsWith('.csv') || 
             file.name.endsWith('.json') ||
             file.name.endsWith('.xlsx') ||
             file.name.endsWith('.xls');
    });

    const newFiles: UploadFile[] = validFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0,
    }));

    setFiles(prev => [...prev, ...newFiles]);

    // Start actual upload for each file
    newFiles.forEach((file, index) => {
      const actualFile = validFiles[index];
      uploadFile(file.id, actualFile);
    });
  };

  const uploadFile = async (fileId: string, file: File) => {
    try {
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: 'uploading' } : f
      ));

      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      formData.append('description', description);
      formData.append('auto_process', 'true');
      
      // Add metadata based on upload type
      const metadata = {
        upload_type: uploadType,
        upload_timestamp: new Date().toISOString(),
      };
      formData.append('metadata', JSON.stringify(metadata));

      // Simulate progress during upload
      const progressInterval = setInterval(() => {
        setFiles(prev => prev.map(f => {
          if (f.id === fileId && f.progress < 90) {
            return { ...f, progress: f.progress + 10 };
          }
          return f;
        }));
      }, 200);

      // Upload file
      const response = await ApiService.uploadFile(formData);
      
      clearInterval(progressInterval);

      if (response.success) {
        setFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: response.data.status === 'processed' ? 'completed' : 'processing',
            progress: 100,
            fileId: response.data.file_id,
            processingResults: response.data.processing_results
          } : f
        ));
        
        // Refresh database stats after successful upload
        await loadDatabaseStats();
        
      } else {
        setFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: 'error',
            progress: 0,
            errorMessage: response.message || 'Upload failed'
          } : f
        ));
      }
      
    } catch (error: any) {
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { 
          ...f, 
          status: 'error',
          progress: 0,
          errorMessage: error.response?.data?.message || error.message || 'Upload failed'
        } : f
      ));
    }
  };

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const retryUpload = (fileId: string) => {
    // Find the original file to retry upload
    const fileToRetry = files.find(f => f.id === fileId);
    if (fileToRetry) {
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: 'pending', progress: 0, errorMessage: undefined } : f
      ));
      // Note: We'd need to store the original File object to retry
      // For now, this is a placeholder - in a real app, you'd store the File reference
      console.log('Retry upload for:', fileToRetry.name);
    }
  };

  const processUploadedFile = async (fileId: string) => {
    const file = files.find(f => f.id === fileId);
    if (!file || !file.fileId) return;

    try {
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { ...f, status: 'processing' } : f
      ));

      const response = await ApiService.processFile(file.fileId);
      
      if (response.success) {
        setFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: 'completed',
            processingResults: response.data.processing_results
          } : f
        ));
        
        // Refresh database stats after successful processing
        await loadDatabaseStats();
        
      } else {
        setFiles(prev => prev.map(f => 
          f.id === fileId ? { 
            ...f, 
            status: 'error',
            errorMessage: response.message || 'Processing failed'
          } : f
        ));
      }
    } catch (error: any) {
      setFiles(prev => prev.map(f => 
        f.id === fileId ? { 
          ...f, 
          status: 'error',
          errorMessage: error.response?.data?.message || error.message || 'Processing failed'
        } : f
      ));
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'uploading':
      case 'processing':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <FileText className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (file: UploadFile) => {
    switch (file.status) {
      case 'uploading':
        return 'Uploading...';
      case 'processing':
        return 'Processing...';
      case 'completed':
        if (file.processingResults) {
          const results = file.processingResults;
          if (results.success && results.ingestion_results) {
            const totalRecords = results.ingestion_results.reduce((sum: number, result: any) => 
              sum + (result.records_inserted || result.inserted_count || 0), 0
            );
            return `Processed ${totalRecords} records`;
          }
        }
        return 'Upload completed';
      case 'error':
        return file.errorMessage || 'Upload failed';
      default:
        return `${formatFileSize(file.size)} • ${uploadType} data`;
    }
  };

  return (
    <div className="space-y-6">
      {/* Description Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Description (Optional)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter a description for this upload batch..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-ocean-500 focus:border-ocean-500"
          rows={2}
        />
      </div>

      {/* Upload Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">Data Type</label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {[
            { value: 'edna', label: 'eDNA Sequences', icon: '🧬' },
            { value: 'oceanographic', label: 'Oceanographic', icon: '🌊' },
            { value: 'species', label: 'Species Data', icon: '🐟' },
            { value: 'taxonomy', label: 'Taxonomy', icon: '📋' },
          ].map(type => (
            <button
              key={type.value}
              onClick={() => setUploadType(type.value as any)}
              className={`p-3 rounded-lg border-2 transition-all ${
                uploadType === type.value
                  ? 'border-ocean-500 bg-ocean-50 text-ocean-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-1">{type.icon}</div>
              <div className="text-sm font-medium">{type.label}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-ocean-400 bg-ocean-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".csv,.json,.txt,.fasta,.xlsx,.xls"
          onChange={handleFileSelect}
          className="hidden"
        />
        
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <div className="text-lg font-medium text-gray-900 mb-2">
          Drop your marine data files here
        </div>
        <p className="text-sm text-gray-500 mb-4">
          or <button 
            onClick={() => fileInputRef.current?.click()}
            className="text-ocean-600 hover:text-ocean-700 font-medium"
          >
            browse files
          </button>
        </p>
        
        <div className="text-xs text-gray-400">
          Supported formats: CSV, JSON, TXT, FASTA, Excel
        </div>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-medium text-gray-900">Uploaded Files</h3>
          <div className="space-y-2">
            {files.map(file => (
              <div
                key={file.id}
                className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg"
              >
                <div className="flex items-center space-x-3 flex-1">
                  {getStatusIcon(file.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <div className="text-xs text-gray-500">
                      {getStatusText(file)}
                    </div>
                    {file.processingResults && file.processingResults.schema_detected && (
                      <div className="text-xs text-green-600 mt-1">
                        Schema: {file.processingResults.schema_detected} 
                        {file.processingResults.confidence && (
                          <span className="text-gray-500">({file.processingResults.confidence.toFixed(1)}% confidence)</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {(file.status === 'uploading' || file.status === 'processing') && (
                  <div className="flex items-center space-x-3">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          file.status === 'processing' ? 'bg-orange-500' : 'bg-blue-600'
                        }`}
                        style={{ width: `${file.progress}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-500">
                      {file.status === 'processing' ? 'Processing' : `${file.progress}%`}
                    </span>
                  </div>
                )}

                <div className="flex items-center space-x-2 ml-4">
                  {file.status === 'error' && (
                    <button
                      onClick={() => retryUpload(file.id)}
                      className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                    >
                      Retry
                    </button>
                  )}
                  {file.status === 'completed' && file.processingResults && (
                    <button 
                      className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                      onClick={() => {
                        console.log('Processing results:', file.processingResults);
                        // Here you could open a modal or navigate to results view
                      }}
                    >
                      View Results
                    </button>
                  )}
                  {file.status === 'processing' && (
                    <button 
                      className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded hover:bg-orange-200 transition-colors"
                      onClick={() => processUploadedFile(file.id)}
                    >
                      Process Now
                    </button>
                  )}
                  <button
                    onClick={() => removeFile(file.id)}
                    className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upload Guidelines */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Upload Guidelines</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• eDNA sequences: FASTA or TXT format with sequence data</li>
          <li>• Oceanographic: CSV with latitude, longitude, parameters, and values</li>
          <li>• Species data: CSV/Excel with taxonomic information</li>
          <li>• Maximum file size: 100MB per file</li>
        </ul>
        
        <div className="mt-3 flex items-center space-x-2">
          <Download className="w-4 h-4 text-blue-600" />
          <a 
            href="#" 
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            onClick={(e) => {
              e.preventDefault();
              alert('Template download would be implemented here');
            }}
          >
            Download sample templates
          </a>
        </div>
      </div>
    </div>
  );
}