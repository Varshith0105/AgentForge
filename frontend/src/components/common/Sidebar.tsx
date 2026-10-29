import React from 'react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { Code2, FolderTree, MessageSquare, Bot, Network, Database, Activity, Server, Settings, LayoutDashboard } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { currentView, setCurrentView } = useWorkspace();

  const navItems = [
    { id: 'workspace', label: 'Workspace', icon: Code2 },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'chat', label: 'AI Chat', icon: MessageSquare, badge: 'SSE' },
    { id: 'agents', label: 'Agents', icon: Bot },
    { id: 'knowledge', label: 'Knowledge Graph', icon: Network },
    { id: 'memory', label: 'Memory', icon: Database },
    { id: 'monitoring', label: 'Monitoring', icon: Activity },
    { id: 'jobs', label: 'Jobs', icon: Server },
  ];

  return (
    <aside className="w-56 bg-surface/95 border-r border-border flex flex-col justify-between select-none py-2">
      <div className="space-y-1 px-2">
        <div className="px-3 py-1.5 text-[10px] font-bold tracking-wider text-text-muted uppercase">Platform Navigation</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition ${
                isActive
                  ? 'bg-primary-muted text-primary border border-primary/30 font-semibold'
                  : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-primary' : 'text-text-secondary'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-accent-purple/20 text-accent-purple font-mono font-bold">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="px-2 pt-2 border-t border-border">
        <button
          onClick={() => setCurrentView('settings')}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition ${
            currentView === 'settings'
              ? 'bg-primary-muted text-primary border border-primary/30 font-semibold'
              : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
          }`}
        >
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </button>
      </div>
    </aside>
  );
};
