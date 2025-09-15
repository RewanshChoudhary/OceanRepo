import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import StatsCards from './StatsCards';
import DashboardTabs from './DashboardTabs';
import SpeciesIdentification from '../Identification/SpeciesIdentification';
import FileUpload from '../Upload/FileUpload';
import ExportData from '../Export/ExportData';
import { X } from 'lucide-react';

interface ModalState {
  isOpen: boolean;
  type: 'upload' | 'identification' | 'export' | 'settings' | null;
  title: string;
}

export default function Dashboard() {
  const { state } = useApp();
  const { loading, error } = state;
  
  const [modal, setModal] = useState<ModalState>({
    isOpen: false,
    type: null,
    title: '',
  });

  const openModal = (type: ModalState['type'], title: string) => {
    setModal({ isOpen: true, type, title });
  };

  const closeModal = () => {
    setModal({ isOpen: false, type: null, title: '' });
  };

  const renderModalContent = () => {
    switch (modal.type) {
      case 'upload':
        return <FileUpload />;
      case 'identification':
        return <SpeciesIdentification />;
      case 'export':
        return <ExportData />;
      case 'settings':
        return (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">⚙️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Settings Panel</h3>
            <p className="text-gray-600">Configuration options would be implemented here</p>
          </div>
        );
      default:
        return null;
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🌊</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Connection Error</h2>
          <p className="text-gray-600 mb-4">Unable to load dashboard data</p>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-ocean-600 text-white rounded-md hover:bg-ocean-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <div className="border-b border-gray-200 pb-6">
        <h1 className="text-3xl font-bold text-gray-900">Marine Data Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Monitor and analyze marine biodiversity, oceanographic conditions, and ecosystem health
        </p>
      </div>

      {/* Stats Cards */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Database Overview</h2>
        <StatsCards />
      </div>

      {/* Interactive Visualization Tabs */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Visualization</h2>
        <DashboardTabs />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button 
            onClick={() => openModal('export', 'Generate Report')}
            className="flex items-center justify-center space-x-2 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-ocean-400 hover:bg-ocean-50 transition-colors group"
          >
            <div className="text-2xl">📊</div>
            <div className="text-left">
              <div className="font-medium text-gray-900 group-hover:text-ocean-600">Generate Report</div>
              <div className="text-sm text-gray-500">Export comprehensive analysis</div>
            </div>
          </button>
          
          <button 
            onClick={() => openModal('identification', 'Species Identification')}
            className="flex items-center justify-center space-x-2 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-ocean-400 hover:bg-ocean-50 transition-colors group"
          >
            <div className="text-2xl">🔍</div>
            <div className="text-left">
              <div className="font-medium text-gray-900 group-hover:text-ocean-600">Species Identification</div>
              <div className="text-sm text-gray-500">Analyze new samples</div>
            </div>
          </button>
          
          <button 
            onClick={() => openModal('settings', 'Alert Settings')}
            className="flex items-center justify-center space-x-2 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-ocean-400 hover:bg-ocean-50 transition-colors group"
          >
            <div className="text-2xl">⚠️</div>
            <div className="text-left">
              <div className="font-medium text-gray-900 group-hover:text-ocean-600">Alert Settings</div>
              <div className="text-sm text-gray-500">Configure monitoring alerts</div>
            </div>
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-4">
          <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
              ✓
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                Species identification completed for Arabian Sea samples
              </p>
              <p className="text-xs text-gray-500 mt-1">2 hours ago • 45 sequences processed</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
              📈
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                New oceanographic data uploaded from Bay of Bengal
              </p>
              <p className="text-xs text-gray-500 mt-1">5 hours ago • 125 data points</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="flex-shrink-0 w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
              ⚠️
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                Temperature anomaly detected in Lakshadweep region
              </p>
              <p className="text-xs text-gray-500 mt-1">1 day ago • Monitoring ongoing</p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="flex-shrink-0 w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
              🔬
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                Biodiversity analysis report generated
              </p>
              <p className="text-xs text-gray-500 mt-1">2 days ago • Available for download</p>
            </div>
          </div>
        </div>
        
        <div className="mt-4 text-center">
          <button className="text-sm text-ocean-600 hover:text-ocean-700 font-medium">
            View all activity →
          </button>
        </div>
      </div>

      {/* Modal */}
      {modal.isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div 
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={closeModal}
            />

            {/* Modal content */}
            <div className="inline-block w-full max-w-6xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
              {/* Modal header */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">{modal.title}</h2>
                <button
                  onClick={closeModal}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Modal body */}
              <div className="max-h-96 overflow-y-auto">
                {renderModalContent()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
