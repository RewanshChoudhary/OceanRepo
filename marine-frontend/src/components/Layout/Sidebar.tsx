import React, { Fragment, useState } from 'react';
import { Listbox, Transition } from '@headlessui/react';
import {
  Home,
  Upload,
  BarChart3,
  Settings,
  Menu,
  X,
  ChevronDown,
  Database,
  Fish,
  Waves,
  Map,
} from 'lucide-react';
import FileUpload from '../Upload/FileUpload';
import { useApp } from '../../context/AppContext';
import type { NavigationModule } from '../../types';

const modules: NavigationModule[] = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    icon: 'Home',
    path: '/dashboard',
    description: 'Overview and analytics',
  },
  {
    id: 'data-upload',
    name: 'Data Upload',
    icon: 'Upload',
    path: '/upload',
    description: 'Import marine data',
  },
  {
    id: 'data-analysis',
    name: 'Data Analysis',
    icon: 'BarChart3',
    path: '/analysis',
    description: 'Advanced analytics tools',
  },
  {
    id: 'settings',
    name: 'Settings',
    icon: 'Settings',
    path: '/settings',
    description: 'System configuration',
  },
];

const iconMap = {
  Home,
  Upload,
  BarChart3,
  Settings,
  Database,
  Fish,
  Waves,
  Map,
};

interface SidebarProps {
  className?: string;
}

export default function Sidebar({ className = '' }: SidebarProps) {
  const { state, setCurrentModule, toggleSidebar, setSidebarOpen } = useApp();
  const { currentModule, sidebarOpen, databaseStats } = state;
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Find current module
  const selectedModule = modules.find(m => m.id === currentModule) || modules[0];

  // Handle module selection
  const handleModuleChange = (module: NavigationModule) => {
    setCurrentModule(module.id);
  };

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0 lg:static lg:inset-0
          ${className}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-8 h-8 bg-ocean-600 rounded-lg">
              <Waves className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">CMLRE</h1>
              <p className="text-xs text-gray-500">Marine Platform</p>
            </div>
          </div>
          
          {/* Mobile close button */}
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Module Selector */}
        <div className="p-4 border-b border-gray-200">
          <Listbox value={selectedModule} onChange={handleModuleChange}>
            <div className="relative">
              <Listbox.Button className="relative w-full cursor-pointer rounded-lg bg-white py-3 pl-3 pr-10 text-left shadow-md border border-gray-200 hover:border-ocean-300 focus:outline-none focus:ring-2 focus:ring-ocean-500 focus:ring-opacity-50">
                <span className="flex items-center">
                  {React.createElement(iconMap[selectedModule.icon as keyof typeof iconMap], {
                    className: "w-5 h-5 text-ocean-600 mr-3"
                  })}
                  <span className="block truncate font-medium">{selectedModule.name}</span>
                </span>
                <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                </span>
              </Listbox.Button>
              
              <Transition
                as={Fragment}
                leave="transition ease-in duration-100"
                leaveFrom="opacity-100"
                leaveTo="opacity-0"
              >
                <Listbox.Options className="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                  {modules.map((module) => {
                    const IconComponent = iconMap[module.icon as keyof typeof iconMap];
                    return (
                      <Listbox.Option
                        key={module.id}
                        className={({ active }) =>
                          `relative cursor-pointer select-none py-3 pl-3 pr-9 ${
                            active ? 'bg-ocean-50 text-ocean-700' : 'text-gray-900'
                          }`
                        }
                        value={module}
                      >
                        {({ selected, active }) => (
                          <>
                            <div className="flex items-center">
                              <IconComponent className={`w-5 h-5 mr-3 ${active ? 'text-ocean-600' : 'text-gray-400'}`} />
                              <div>
                                <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>
                                  {module.name}
                                </span>
                                <span className="text-sm text-gray-500">{module.description}</span>
                              </div>
                            </div>
                          </>
                        )}
                      </Listbox.Option>
                    );
                  })}
                </Listbox.Options>
              </Transition>
            </div>
          </Listbox>
        </div>

        {/* Quick Stats */}
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Database Status</h3>
          <div className="space-y-2">
            {databaseStats ? (
              <>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Species</span>
                  <span className="font-medium text-gray-900">{databaseStats.species_count.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">eDNA</span>
                  <span className="font-medium text-gray-900">{databaseStats.edna_count.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Ocean Data</span>
                  <span className="font-medium text-gray-900">{databaseStats.oceanographic_count.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm pt-2 border-t border-gray-200">
                  <span className="text-gray-600">Total</span>
                  <span className="font-semibold text-ocean-600">{databaseStats.total_records.toLocaleString()}</span>
                </div>
              </>
            ) : (
              <div className="text-sm text-gray-500">Loading...</div>
            )}
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 p-4 space-y-1">
          <div className="space-y-1">
            <button className="sidebar-nav-item active w-full">
              <Database className="w-5 h-5 mr-3" />
              <span>Data Overview</span>
            </button>
            <button 
              onClick={() => setShowUploadModal(true)}
              className="sidebar-nav-item w-full hover:bg-ocean-50 hover:text-ocean-600"
            >
              <Upload className="w-5 h-5 mr-3" />
              <span>Upload Data</span>
            </button>
            <button className="sidebar-nav-item w-full">
              <Fish className="w-5 h-5 mr-3" />
              <span>Species Analysis</span>
            </button>
            <button className="sidebar-nav-item w-full">
              <Waves className="w-5 h-5 mr-3" />
              <span>Ocean Monitoring</span>
            </button>
            <button className="sidebar-nav-item w-full">
              <Map className="w-5 h-5 mr-3" />
              <span>Geographic View</span>
            </button>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            <p>CMLRE Marine Data Platform</p>
            <p>v1.0.0 - {new Date().getFullYear()}</p>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div 
              className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
              onClick={() => setShowUploadModal(false)}
            />

            {/* Modal content */}
            <div className="inline-block w-full max-w-4xl p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
              {/* Modal header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                  <Upload className="w-6 h-6 text-ocean-600" />
                  <h2 className="text-2xl font-bold text-gray-900">Upload Marine Data</h2>
                </div>
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Modal body */}
              <div className="max-h-96 overflow-y-auto">
                <FileUpload />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
