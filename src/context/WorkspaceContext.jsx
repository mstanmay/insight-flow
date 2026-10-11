import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import { VIEWS } from '../config';

const WorkspaceContext = createContext(null);

export function WorkspaceProvider({ children }) {
  // Theme state
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  });

  // Navigation view state
  const [activeView, setActiveView] = useState(VIEWS.OVERVIEW);

  // Active dataset
  const [activeDataset, setActiveDataset] = useState(null);
  const [datasetsLoading, setDatasetsLoading] = useState(true);

  // Active drawer issue
  const [activeIssueId, setActiveIssueId] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Modals state
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [hotfixModalOpen, setHotfixModalOpen] = useState(false);

  // Toasts notification queue
  const [toasts, setToasts] = useState([]);

  // Apply theme to HTML root element
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Toggle theme
  const toggleTheme = useCallback(() => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  }, []);

  // Toast dispatchers
  const addToast = useCallback((message, type = 'success') => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts(prev => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // Load initial dataset
  const refreshDatasets = useCallback(async () => {
    try {
      setDatasetsLoading(true);
      const res = await api.getDatasets(1, 10);
      if (res.items && res.items.length > 0) {
        setActiveDataset(res.items[0]);
        window.activeDatasetId = res.items[0].id;
      }
    } catch (err) {
      console.warn('Failed to load datasets:', err);
    } finally {
      setDatasetsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshDatasets();
  }, [refreshDatasets]);

  // Drawer handlers
  const openDrawer = useCallback((issueId) => {
    setActiveIssueId(issueId);
    setDrawerOpen(true);
    // Legacy support for existing HTML drawer if rendered outside React
    const drawer = document.getElementById('evidence-drawer');
    const overlay = document.getElementById('drawer-overlay');
    if (drawer) drawer.classList.remove('translate-x-full');
    if (overlay) overlay.classList.remove('hidden');
    if (window.openEvidenceDrawer) window.openEvidenceDrawer(issueId);
  }, []);

  const closeDrawer = useCallback(() => {
    setDrawerOpen(false);
    setActiveIssueId(null);
    const drawer = document.getElementById('evidence-drawer');
    const overlay = document.getElementById('drawer-overlay');
    if (drawer) drawer.classList.add('translate-x-full');
    if (overlay) overlay.classList.add('hidden');
  }, []);

  // Switch active view
  const switchView = useCallback((viewName) => {
    setActiveView(viewName);
    if (window.switchView) window.switchView(viewName);
  }, []);

  const value = {
    theme,
    toggleTheme,
    activeView,
    switchView,
    activeDataset,
    setActiveDataset,
    datasetsLoading,
    refreshDatasets,
    activeIssueId,
    drawerOpen,
    openDrawer,
    closeDrawer,
    importModalOpen,
    setImportModalOpen,
    hotfixModalOpen,
    setHotfixModalOpen,
    toasts,
    addToast,
    removeToast,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}
