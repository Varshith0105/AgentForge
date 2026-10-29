import React, { useState } from 'react';
import { Header } from '../components/common/Header';
import { Sidebar } from '../components/common/Sidebar';
import { CommandPalette } from '../components/common/CommandPalette';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { WorkspacePage } from '../pages/WorkspacePage';
import { DashboardPage } from '../pages/DashboardPage';
import { AgentsPage } from '../pages/AgentsPage';
import { KnowledgePage } from '../pages/KnowledgePage';
import { JobsPage } from '../pages/JobsPage';
import { MonitoringPage } from '../pages/MonitoringPage';
import { SettingsPage } from '../pages/SettingsPage';
import { api } from '../services/api';
import { FolderPlus, X } from 'lucide-react';

export const WorkspaceLayout: React.FC = () => {
  const { currentView, createProject, setCurrentProject } = useWorkspace();
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isRepoModalOpen, setIsRepoModalOpen] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [repoBranch, setRepoBranch] = useState('main');
  const [isCloning, setIsCloning] = useState(false);

  const handleCloneRepo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setIsCloning(true);
    try {
      const res = await api.github.clone({ repo_url: repoUrl, branch: repoBranch });
      if (res.project) {
        setCurrentProject(res.project);
      } else {
        await createProject(res.name || 'Cloned Repository', `Cloned from ${repoUrl}`);
      }
      setIsRepoModalOpen(false);
      setRepoUrl('');
    } catch (err: any) {
      alert(err.message || 'Clone failed');
    } finally {
      setIsCloning(false);
    }
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'workspace':
      case 'chat': // AI Chat lives in the workspace right panel
        return <WorkspacePage />;
      case 'dashboard':
        return <DashboardPage />;
      case 'agents':
        return <AgentsPage />;
      case 'knowledge':
      case 'memory':
        return <KnowledgePage />;
      case 'jobs':
        return <JobsPage />;
      case 'monitoring':
        return <MonitoringPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <WorkspacePage />;
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-background text-text-primary overflow-hidden font-sans">
      <Header
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        onOpenRepoModal={() => setIsRepoModalOpen(true)}
      />

      <div className="flex-1 flex min-h-0 overflow-hidden">
        <Sidebar />
        <main className="flex-1 min-w-0 h-full overflow-hidden bg-background">
          {renderCurrentView()}
        </main>
      </div>

      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />

      {/* Repository Open Modal */}
      {isRepoModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md glass-panel p-6 rounded-2xl border border-border space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2 font-bold text-sm text-text-primary">
                <FolderPlus className="w-4 h-4 text-primary" />
                <span>Open or Clone Repository</span>
              </div>
              <button onClick={() => setIsRepoModalOpen(false)} className="p-1 hover:bg-surface-hover rounded text-text-muted">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCloneRepo} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-text-secondary">GitHub Repository URL</label>
                <input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/username/repository"
                  required
                  className="w-full bg-surface border border-border rounded-xl px-3 py-2.5 text-xs text-text-primary outline-none focus:border-primary placeholder:text-text-muted"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-text-secondary">Branch</label>
                <input
                  type="text"
                  value={repoBranch}
                  onChange={(e) => setRepoBranch(e.target.value)}
                  placeholder="main"
                  className="w-full bg-surface border border-border rounded-xl px-3 py-2.5 text-xs text-text-primary outline-none focus:border-primary"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsRepoModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-surface border border-border text-xs text-text-secondary hover:text-text-primary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCloning}
                  className="px-4 py-2 rounded-xl bg-primary text-black font-bold text-xs hover:bg-primary-hover shadow-glow transition"
                >
                  {isCloning ? 'Cloning...' : 'Clone & Open'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
