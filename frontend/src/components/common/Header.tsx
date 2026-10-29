import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { Zap, GitBranch, FolderOpen, Coins, User as UserIcon, LogOut, Settings, Command } from 'lucide-react';
import { api } from '../../services/api';

interface HeaderProps {
  onOpenCommandPalette: () => void;
  onOpenRepoModal: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenCommandPalette, onOpenRepoModal }) => {
  const { user, logout } = useAuth();
  const { currentProject, setCurrentView } = useWorkspace();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [totalCost, setTotalCost] = useState<number | null>(null);

  // Fetch live cost data every 30 s
  useEffect(() => {
    const fetchCost = () => {
      api.costs.summary().then(c => setTotalCost(c.total_cost)).catch(() => {});
    };
    fetchCost();
    const id = setInterval(fetchCost, 30_000);
    return () => clearInterval(id);
  }, []);

  // Close user-menu on outside click
  useEffect(() => {
    if (!showUserMenu) return;
    const handler = () => setShowUserMenu(false);
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, [showUserMenu]);

  return (
    <header className="h-14 bg-surface/90 backdrop-blur-md border-b border-border flex items-center justify-between px-4 z-30 select-none">

      {/* ── Left: Brand + Repo chip ─────────────────────────────────────────── */}
      <div className="flex items-center gap-4">
        <div
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => setCurrentView('workspace')}
        >
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center shadow-glow">
            <Zap className="w-5 h-5 text-black" />
          </div>
          <span className="font-extrabold text-lg bg-gradient-to-r from-text-primary via-primary to-accent-purple bg-clip-text text-transparent">
            AgentForge
          </span>
        </div>

        <div className="h-4 w-px bg-border mx-1" />

        <button
          onClick={onOpenRepoModal}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-hover hover:bg-border/60 border border-border/40 transition text-xs"
        >
          <FolderOpen className="w-3.5 h-3.5 text-primary" />
          <span className="font-medium text-text-primary">
            {currentProject ? currentProject.name : 'No Repository Open'}
          </span>
          <div className="flex items-center gap-1 text-text-secondary pl-2 border-l border-border">
            <GitBranch className="w-3 h-3 text-accent-green" />
            <span>{currentProject?.branch || 'main'}</span>
          </div>
        </button>
      </div>

      {/* ── Centre: Command Palette trigger ─────────────────────────────────── */}
      <button
        onClick={onOpenCommandPalette}
        className="flex items-center gap-3 px-4 py-1.5 rounded-lg bg-background/60 hover:bg-surface-hover border border-border text-xs text-text-secondary transition w-64 justify-between"
      >
        <span className="flex items-center gap-2">
          <Command className="w-3.5 h-3.5 text-primary" />
          <span>Search or command...</span>
        </span>
        <kbd className="px-1.5 py-0.5 rounded bg-border text-[10px] text-text-muted font-mono">
          Ctrl K
        </kbd>
      </button>

      {/* ── Right: AI status + cost + user ──────────────────────────────────── */}
      <div className="flex items-center gap-3">
        {/* Live router badge */}
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-primary-muted border border-primary/30 text-xs">
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span className="font-semibold text-primary">Live AI Router</span>
        </div>

        {/* Real-time cost */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-hover border border-border text-xs text-text-secondary">
          <Coins className="w-3.5 h-3.5 text-accent-amber" />
          <span className="text-text-primary tabular-nums">
            {totalCost !== null ? `$${totalCost.toFixed(4)}` : '—'}
          </span>
        </div>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={e => { e.stopPropagation(); setShowUserMenu(v => !v); }}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-surface-hover transition"
          >
            <div className="w-7 h-7 rounded-full bg-accent-purple/30 border border-accent-purple flex items-center justify-center text-xs font-semibold text-text-primary">
              {user?.name ? user.name[0].toUpperCase() : <UserIcon className="w-4 h-4" />}
            </div>
            <span className="text-xs font-medium text-text-primary max-w-[100px] truncate">
              {user?.name || 'User'}
            </span>
          </button>

          {showUserMenu && (
            <div
              className="absolute right-0 mt-2 w-48 rounded-xl glass-panel shadow-xl py-1 z-50 border border-border"
              onClick={e => e.stopPropagation()}
            >
              <div className="px-3 py-2 border-b border-border">
                <p className="text-xs font-semibold text-text-primary truncate">{user?.name}</p>
                <p className="text-[11px] text-text-secondary truncate">{user?.email}</p>
              </div>
              <button
                onClick={() => { setCurrentView('settings'); setShowUserMenu(false); }}
                className="w-full text-left px-3 py-2 text-xs text-text-secondary hover:bg-surface-hover flex items-center gap-2"
              >
                <Settings className="w-3.5 h-3.5" /> Settings
              </button>
              <button
                onClick={() => { logout(); setShowUserMenu(false); }}
                className="w-full text-left px-3 py-2 text-xs text-red-400 hover:bg-red-500/10 flex items-center gap-2"
              >
                <LogOut className="w-3.5 h-3.5" /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
