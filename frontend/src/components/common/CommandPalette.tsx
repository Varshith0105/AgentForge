import React, { useState, useEffect } from 'react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { Search, Code, Terminal, Play, Bot, FileText, Zap, X } from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const { setCurrentView, openFile } = useWorkspace();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else {
          // Open
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const actions = [
    { label: 'Go to Workspace', icon: Code, action: () => setCurrentView('workspace') },
    { label: 'Go to AI Chat', icon: Zap, action: () => setCurrentView('chat') },
    { label: 'Go to Agents Orchestrator', icon: Bot, action: () => setCurrentView('agents') },
    { label: 'Go to Knowledge Graph', icon: Search, action: () => setCurrentView('knowledge') },
    { label: 'Open Terminal', icon: Terminal, action: () => setCurrentView('workspace') },
    { label: 'Run Full Repository Analysis', icon: Play, action: () => setCurrentView('workspace') },
    { label: 'Open main.py', icon: FileText, action: () => openFile({ name: 'main.py', path: 'app/main.py' }) },
  ];

  const filtered = actions.filter((a) => a.label.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-start justify-center pt-24 px-4">
      <div className="w-full max-w-xl glass-panel rounded-2xl border border-border shadow-2xl overflow-hidden">
        <div className="flex items-center px-4 border-b border-border bg-surface/80">
          <Search className="w-4 h-4 text-primary mr-3" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search files..."
            className="w-full bg-transparent py-3 text-sm text-text-primary outline-none placeholder:text-text-muted font-sans"
            autoFocus
          />
          <button onClick={onClose} className="p-1 hover:bg-surface-hover rounded text-text-muted">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filtered.length === 0 ? (
            <div className="p-4 text-center text-xs text-text-muted">No commands found matching "{query}"</div>
          ) : (
            filtered.map((item, idx) => {
              const Icon = item.icon;
              return (
                <button
                  key={idx}
                  onClick={() => {
                    item.action();
                    onClose();
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs text-text-primary hover:bg-surface-hover transition text-left"
                >
                  <Icon className="w-4 h-4 text-primary" />
                  <span>{item.label}</span>
                </button>
              );
            })
          )}
        </div>

        <div className="px-4 py-2 bg-surface/90 border-t border-border flex items-center justify-between text-[11px] text-text-muted">
          <span>Use Enter to select</span>
          <span>Esc to exit</span>
        </div>
      </div>
    </div>
  );
};
