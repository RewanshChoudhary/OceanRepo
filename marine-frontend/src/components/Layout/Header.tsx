import React from 'react';
import { Menu, RotateCcw, Bell, Search, User } from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export default function Header({ title = 'Dashboard', subtitle = 'Marine Data Overview' }: HeaderProps) {
  const { state, toggleSidebar, loadDatabaseStats } = useApp();
  const { loading } = state;

  const handleRefresh = () => {
    loadDatabaseStats();
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between h-16 px-4 lg:px-6">
        {/* Left section */}
        <div className="flex items-center space-x-4">
          {/* Mobile menu button */}
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 lg:hidden"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Page title */}
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
            <p className="text-sm text-gray-500">{subtitle}</p>
          </div>
        </div>

        {/* Center section - Search */}
        <div className="hidden md:flex flex-1 max-w-lg mx-4">
          <div className="relative w-full">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search marine data..."
              className="block w-full pl-10 pr-3 py-2 border border-gray-200 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-ocean-500 focus:ring-opacity-50 focus:border-ocean-500 sm:text-sm"
            />
          </div>
        </div>

        {/* Right section */}
        <div className="flex items-center space-x-4">
          {/* Refresh button */}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className={`p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 ${
              loading ? 'animate-spin' : ''
            }`}
            title="Refresh data"
          >
            <RotateCcw className="w-5 h-5" />
          </button>

          {/* Notifications */}
          <button className="p-2 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 relative">
            <Bell className="w-5 h-5" />
            <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-400 ring-2 ring-white" />
          </button>

          {/* User menu */}
          <div className="relative">
            <button className="flex items-center space-x-2 p-2 rounded-md text-gray-700 hover:bg-gray-100">
              <div className="w-8 h-8 rounded-full bg-ocean-600 flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <span className="hidden md:block text-sm font-medium">Researcher</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}