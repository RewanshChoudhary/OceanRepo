import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import type { DatabaseStats, DashboardTab, Species } from '../types';
import ApiService from '../services/api';

// State interface
interface AppState {
  // Navigation
  currentModule: string;
  currentTab: DashboardTab;
  
  // Data
  databaseStats: DatabaseStats | null;
  species: Species[];
  
  // UI State
  loading: boolean;
  error: string | null;
  sidebarOpen: boolean;
}

// Action types
type AppAction =
  | { type: 'SET_CURRENT_MODULE'; payload: string }
  | { type: 'SET_CURRENT_TAB'; payload: DashboardTab }
  | { type: 'SET_DATABASE_STATS'; payload: DatabaseStats }
  | { type: 'SET_SPECIES'; payload: Species[] }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_SIDEBAR_OPEN'; payload: boolean };

// Initial state
const initialState: AppState = {
  currentModule: 'dashboard',
  currentTab: 'timeseries',
  databaseStats: null,
  species: [],
  loading: false,
  error: null,
  sidebarOpen: true,
};

// Reducer function
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_CURRENT_MODULE':
      return { ...state, currentModule: action.payload };
    case 'SET_CURRENT_TAB':
      return { ...state, currentTab: action.payload };
    case 'SET_DATABASE_STATS':
      return { ...state, databaseStats: action.payload };
    case 'SET_SPECIES':
      return { ...state, species: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarOpen: !state.sidebarOpen };
    case 'SET_SIDEBAR_OPEN':
      return { ...state, sidebarOpen: action.payload };
    default:
      return state;
  }
}

// Context interface
interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  // Action creators
  setCurrentModule: (module: string) => void;
  setCurrentTab: (tab: DashboardTab) => void;
  loadDatabaseStats: () => Promise<void>;
  loadSpecies: (params?: { kingdom?: string; limit?: number }) => Promise<void>;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

// Create context
const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider component
interface AppProviderProps {
  children: ReactNode;
}

export function AppProvider({ children }: AppProviderProps) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Action creators
  const setCurrentModule = (module: string) => {
    dispatch({ type: 'SET_CURRENT_MODULE', payload: module });
  };

  const setCurrentTab = (tab: DashboardTab) => {
    dispatch({ type: 'SET_CURRENT_TAB', payload: tab });
  };

  const loadDatabaseStats = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });
      
      const stats = await ApiService.getDatabaseStats();
      dispatch({ type: 'SET_DATABASE_STATS', payload: stats });
    } catch (error) {
      console.error('Failed to load database stats:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load database statistics' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const loadSpecies = async (params?: { kingdom?: string; limit?: number }) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });
      
      const response = await ApiService.getSpecies({
        per_page: params?.limit || 20,
        kingdom: params?.kingdom,
      });
      
      dispatch({ type: 'SET_SPECIES', payload: response.data });
    } catch (error) {
      console.error('Failed to load species:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load species data' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const toggleSidebar = () => {
    dispatch({ type: 'TOGGLE_SIDEBAR' });
  };

  const setSidebarOpen = (open: boolean) => {
    dispatch({ type: 'SET_SIDEBAR_OPEN', payload: open });
  };

  // Load initial data
  useEffect(() => {
    loadDatabaseStats();
  }, []);

  // Context value
  const contextValue: AppContextType = {
    state,
    dispatch,
    setCurrentModule,
    setCurrentTab,
    loadDatabaseStats,
    loadSpecies,
    toggleSidebar,
    setSidebarOpen,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook to use the context
export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

export default AppContext;