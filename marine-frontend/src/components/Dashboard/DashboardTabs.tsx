import React from 'react';
import { Tab } from '@headlessui/react';
import { clsx } from 'clsx';
import { 
  Clock, 
  MapPin, 
  TrendingUp, 
  Activity,
  BarChart3,
  PieChart,
  LineChart,
  Globe
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import TimeSeriesPanel from './panels/TimeSeriesPanel';
import GeographicPanel from './panels/GeographicPanel';
import BiodiversityPanel from './panels/BiodiversityPanel';
import EcosystemPanel from './panels/EcosystemPanel';

const tabsConfig = [
  {
    id: 'timeseries',
    label: 'Time Series',
    icon: Clock,
    description: 'Temporal data trends',
    component: TimeSeriesPanel,
  },
  {
    id: 'geographic',
    label: 'Geographic Distribution',
    icon: MapPin,
    description: 'Spatial analysis and mapping',
    component: GeographicPanel,
  },
  {
    id: 'biodiversity',
    label: 'Biodiversity Trends',
    icon: TrendingUp,
    description: 'Species diversity analysis',
    component: BiodiversityPanel,
  },
  {
    id: 'ecosystem',
    label: 'Ecosystem Analysis',
    icon: Activity,
    description: 'Ecosystem health metrics',
    component: EcosystemPanel,
  },
];

export default function DashboardTabs() {
  const { state } = useApp();
  const { loading } = state;

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 mb-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex-1 h-12 bg-gray-200 rounded-md"></div>
          ))}
        </div>
        <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 bg-gray-300 rounded mx-auto mb-4"></div>
            <div className="h-4 bg-gray-300 rounded w-32 mx-auto mb-2"></div>
            <div className="h-3 bg-gray-300 rounded w-24 mx-auto"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <Tab.Group>
        <Tab.List className="flex space-x-1 rounded-lg bg-gray-100 p-1">
          {tabsConfig.map((tab) => (
            <Tab
              key={tab.id}
              className={({ selected }) =>
                clsx(
                  'w-full rounded-md py-3 px-4 text-sm font-medium leading-5',
                  'ring-white/60 ring-offset-2 ring-offset-ocean-400 focus:outline-none focus:ring-2',
                  'transition-all duration-200',
                  selected
                    ? 'bg-white text-ocean-700 shadow'
                    : 'text-gray-600 hover:bg-white/60 hover:text-gray-800'
                )
              }
            >
              {({ selected }) => (
                <div className="flex items-center justify-center space-x-2">
                  <tab.icon 
                    className={clsx(
                      'w-4 h-4 transition-colors',
                      selected ? 'text-ocean-600' : 'text-gray-500'
                    )} 
                  />
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.label.split(' ')[0]}</span>
                </div>
              )}
            </Tab>
          ))}
        </Tab.List>

        <Tab.Panels className="mt-6">
          {tabsConfig.map((tab) => (
            <Tab.Panel
              key={tab.id}
              className={clsx(
                'rounded-lg bg-white p-6',
                'ring-white/60 ring-offset-2 ring-offset-ocean-400 focus:outline-none focus:ring-2',
                'shadow-sm border border-gray-200'
              )}
            >
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-2">
                  <tab.icon className="w-5 h-5 text-ocean-600" />
                  <h3 className="text-lg font-semibold text-gray-900">{tab.label}</h3>
                </div>
                <p className="text-sm text-gray-600">{tab.description}</p>
              </div>
              
              <div className="min-h-[400px]">
                <tab.component />
              </div>
            </Tab.Panel>
          ))}
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}