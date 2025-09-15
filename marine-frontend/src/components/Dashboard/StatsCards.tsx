import React from 'react';
import { Database, Fish, Waves, TestTube, BarChart3, TrendingUp } from 'lucide-react';
import { useApp } from '../../context/AppContext';

const iconMap = {
  Database,
  Fish,
  Waves,
  TestTube,
  BarChart3,
};

interface StatCard {
  id: string;
  title: string;
  value: number;
  icon: keyof typeof iconMap;
  color: string;
  change?: number;
  changeType?: 'increase' | 'decrease';
}

export default function StatsCards() {
  const { state } = useApp();
  const { databaseStats, loading } = state;

  const cards: StatCard[] = [
    {
      id: 'oceanographic',
      title: 'Oceanographic Data',
      value: databaseStats?.oceanographic_count || 0,
      icon: 'Waves',
      color: 'ocean',
      change: 12,
      changeType: 'increase',
    },
    {
      id: 'species',
      title: 'Species Data',
      value: databaseStats?.species_count || 0,
      icon: 'Fish',
      color: 'green',
      change: 5,
      changeType: 'increase',
    },
    {
      id: 'edna',
      title: 'eDNA Samples',
      value: databaseStats?.edna_count || 0,
      icon: 'TestTube',
      color: 'purple',
      change: 8,
      changeType: 'increase',
    },
    {
      id: 'otolith',
      title: 'Otolith Samples',
      value: databaseStats?.otolith_count || 0,
      icon: 'Database',
      color: 'blue',
      change: 0,
      changeType: 'increase',
    },
    {
      id: 'total',
      title: 'Total Records',
      value: databaseStats?.total_records || 0,
      icon: 'BarChart3',
      color: 'indigo',
      change: 15,
      changeType: 'increase',
    },
  ];

  const getColorClasses = (color: string) => {
    const colorMap = {
      ocean: 'bg-ocean-600 text-white',
      green: 'bg-green-600 text-white',
      purple: 'bg-purple-600 text-white',
      blue: 'bg-blue-600 text-white',
      indigo: 'bg-indigo-600 text-white',
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.ocean;
  };

  const getChangeColor = (changeType?: 'increase' | 'decrease') => {
    if (changeType === 'increase') return 'text-green-600 bg-green-50';
    if (changeType === 'decrease') return 'text-red-600 bg-red-50';
    return 'text-gray-600 bg-gray-50';
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="flex items-center justify-between">
              <div>
                <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-16"></div>
              </div>
              <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
            </div>
            <div className="mt-4 flex items-center">
              <div className="h-4 bg-gray-200 rounded w-16"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
      {cards.map((card) => {
        const IconComponent = iconMap[card.icon];
        const iconColorClasses = getColorClasses(card.color);
        const changeColorClasses = getChangeColor(card.changeType);

        return (
          <div key={card.id} className="card hover:shadow-lg transition-shadow duration-200">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 truncate">{card.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {card.value.toLocaleString()}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${iconColorClasses}`}>
                <IconComponent className="w-6 h-6" />
              </div>
            </div>
            
            {card.change !== undefined && (
              <div className="mt-4 flex items-center">
                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${changeColorClasses}`}>
                  <TrendingUp className="w-3 h-3 mr-1" />
                  +{card.change}%
                </div>
                <span className="text-xs text-gray-500 ml-2">vs last month</span>
              </div>
            )}
            
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full ${card.color === 'ocean' ? 'bg-ocean-600' : 
                    card.color === 'green' ? 'bg-green-600' : 
                    card.color === 'purple' ? 'bg-purple-600' : 
                    card.color === 'blue' ? 'bg-blue-600' : 'bg-indigo-600'}`}
                  style={{ width: `${Math.min((card.value / (databaseStats?.total_records || 1)) * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}