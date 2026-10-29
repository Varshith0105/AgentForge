import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Project } from '../types/api';
import { api } from '../services/api';

export interface EditorTab {
  id: string;
  name: string;
  path: string;
  content: string;
  language: string;
  isDirty?: boolean;
}

interface WorkspaceContextType {
  currentProject: Project | null;
  projects: Project[];
  openTabs: EditorTab[];
  activeTabId: string | null;
  currentView: string;
  activeBottomPanel: string;
  setCurrentView: (view: string) => void;
  setActiveBottomPanel: (panel: string) => void;
  setCurrentProject: (project: Project | null) => void;
  openFile: (file: { name: string; path: string; content?: string; language?: string }) => void;
  closeTab: (tabId: string) => void;
  setActiveTabId: (tabId: string) => void;
  refreshProjects: () => Promise<void>;
  createProject: (name: string, description?: string) => Promise<Project>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [openTabs, setOpenTabs] = useState<EditorTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState('workspace');
  const [activeBottomPanel, setActiveBottomPanel] = useState('terminal');

  const refreshProjects = async () => {
    try {
      const list = await api.projects.list();
      setProjects(list);
      if (list.length > 0 && !currentProject) {
        setCurrentProject(list[0]);
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  const createProject = async (name: string, description?: string) => {
    const proj = await api.projects.create({ name, description });
    await refreshProjects();
    setCurrentProject(proj);
    return proj;
  };

  const openFile = (file: { name: string; path: string; content?: string; language?: string }) => {
    const existing = openTabs.find((t) => t.path === file.path);
    if (existing) {
      setActiveTabId(existing.id);
      return;
    }

    const ext = file.name.split('.').pop() || '';
    const langMap: Record<string, string> = {
      py: 'python',
      js: 'javascript',
      ts: 'typescript',
      tsx: 'typescript',
      jsx: 'javascript',
      json: 'json',
      html: 'html',
      css: 'css',
      md: 'markdown',
    };

    const newTab: EditorTab = {
      id: `tab_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      name: file.name,
      path: file.path,
      content: file.content || '',
      language: file.language || langMap[ext] || 'plaintext',
    };

    setOpenTabs((prev) => [...prev, newTab]);
    setActiveTabId(newTab.id);
  };

  const closeTab = (tabId: string) => {
    setOpenTabs((prev) => {
      const next = prev.filter((t) => t.id !== tabId);
      if (activeTabId === tabId) {
        setActiveTabId(next.length > 0 ? next[next.length - 1].id : null);
      }
      return next;
    });
  };

  return (
    <WorkspaceContext.Provider
      value={{
        currentProject,
        projects,
        openTabs,
        activeTabId,
        currentView,
        activeBottomPanel,
        setCurrentView,
        setActiveBottomPanel,
        setCurrentProject,
        openFile,
        closeTab,
        setActiveTabId,
        refreshProjects,
        createProject,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error('useWorkspace must be used within WorkspaceProvider');
  return context;
};
