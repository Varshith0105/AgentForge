import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Project, ObservabilityMetrics, CostSummary } from '../types/api';
import { Folder, Activity, Coins, ShieldCheck, Zap, ArrowUpRight } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [costs, setCosts] = useState<CostSummary | null>(null);

  useEffect(() => {
    api.projects.list().then(setProjects).catch(() => {});
    api.observability.metrics().then(setMetrics).catch(() => {});
    api.costs.summary().then(setCosts).catch(() => {});
  }, []);

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 bg-background">
      <div>
        <h1 className="text-2xl font-extrabold text-text-primary">Engineering Dashboard</h1>
        <p className="text-xs text-text-secondary">Real-time system health, agent activity, and analytics</p>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 rounded-xl border border-border space-y-2">
          <div className="flex items-center justify-between text-text-secondary text-xs">
            <span>Total Projects</span>
            <Folder className="w-4 h-4 text-primary" />
          </div>
          <div className="text-2xl font-black text-text-primary">{projects.length}</div>
          <div className="text-[11px] text-accent-green font-medium flex items-center gap-1">
            <ArrowUpRight className="w-3 h-3" /> Active Workspaces
          </div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-border space-y-2">
          <div className="flex items-center justify-between text-text-secondary text-xs">
            <span>API Execution Calls</span>
            <Activity className="w-4 h-4 text-accent-purple" />
          </div>
          <div className="text-2xl font-black text-text-primary">{metrics ? metrics.total_calls : '—'}</div>
          <div className="text-[11px] text-text-muted">
            Avg Latency: {metrics?.average_latency_ms != null ? `${metrics.average_latency_ms}ms` : '—'}
          </div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-border space-y-2">
          <div className="flex items-center justify-between text-text-secondary text-xs">
            <span>Token Usage</span>
            <Zap className="w-4 h-4 text-accent-pink" />
          </div>
          <div className="text-2xl font-black text-text-primary">{metrics ? metrics.tokens_used.toLocaleString() : '—'}</div>
          <div className="text-[11px] text-text-muted">Live provider usage</div>
        </div>

        <div className="glass-card p-4 rounded-xl border border-border space-y-2">
          <div className="flex items-center justify-between text-text-secondary text-xs">
            <span>Estimated Cost</span>
            <Coins className="w-4 h-4 text-accent-amber" />
          </div>
          <div className="text-2xl font-black text-text-primary">{costs ? `$${costs.total_cost.toFixed(2)}` : '—'}</div>
          <div className="text-[11px] text-accent-green">Real provider billing data</div>
        </div>
      </div>

      {/* Projects List Card */}
      <div className="glass-panel p-6 rounded-2xl border border-border space-y-4">
        <h2 className="text-base font-bold text-text-primary">Recent Engineering Projects</h2>
        {projects.length === 0 ? (
          <div className="text-center p-8 text-xs text-text-muted">No projects found. Create one in the workspace to get started.</div>
        ) : (
          <div className="space-y-2">
            {projects.map((p) => (
              <div key={p.id} className="p-3 rounded-xl bg-surface/60 border border-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Folder className="w-5 h-5 text-primary" />
                  <div>
                    <div className="text-xs font-bold text-text-primary">{p.name}</div>
                    <div className="text-[11px] text-text-muted">{p.description || 'No description'}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] bg-accent-green/20 text-accent-green font-semibold">
                    {p.status || 'ready'}
                  </span>
                  <span className="text-[11px] text-text-muted font-mono">{p.branch}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
