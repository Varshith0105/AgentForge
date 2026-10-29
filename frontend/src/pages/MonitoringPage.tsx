import React, { useEffect, useState, useRef } from 'react';
import { api } from '../services/api';
import { ObservabilityMetrics, CostSummary } from '../types/api';
import { Activity, Coins, Zap, RefreshCw, Wifi, Server, TrendingUp, Cpu, MemoryStick } from 'lucide-react';


export const MonitoringPage: React.FC = () => {
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [costs, setCosts] = useState<CostSummary | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const [m, c] = await Promise.all([
        api.observability.metrics(),
        api.costs.summary(),
      ]);
      setMetrics(m);
      setCosts(c);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch {
      // silent
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    intervalRef.current = setInterval(loadData, 15000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const statCard = (
    label: string,
    value: string | number | null,
    sub: string,
    Icon: React.ElementType,
    iconClass: string,
  ) => (
    <div className="glass-card p-6 rounded-2xl border border-border space-y-2">
      <div className="flex items-center justify-between text-xs text-text-secondary">
        <span>{label}</span>
        <Icon className={`w-5 h-5 ${iconClass}`} />
      </div>
      <div className="text-3xl font-black text-text-primary">
        {value !== null && value !== undefined ? value : '—'}
      </div>
      <div className="text-xs text-text-muted">{sub}</div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 bg-background">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-text-primary">System Monitoring</h1>
          <p className="text-xs text-text-secondary">Observability metrics, API throughput, and cost analytics</p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-[11px] text-text-muted">Updated: {lastUpdated}</span>
          )}
          <button
            onClick={loadData}
            disabled={isRefreshing}
            className="px-3 py-1.5 rounded-lg bg-surface border border-border text-xs text-text-secondary hover:text-text-primary flex items-center gap-1.5 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Primary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {statCard('Total API Requests', metrics?.total_calls ?? null, 'Live request volume', Activity, 'text-primary')}
        {statCard('Tokens Consumed', metrics ? metrics.tokens_used.toLocaleString() : null, 'Prompt + completion tokens', Zap, 'text-accent-purple')}
        {statCard('Total Cost', costs ? `$${costs.total_cost.toFixed(4)}` : null, `Currency: ${costs?.currency || 'USD'}`, Coins, 'text-accent-amber')}
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {statCard('Avg Latency', metrics?.average_latency_ms != null ? `${metrics.average_latency_ms}ms` : '—', 'Mean response time', TrendingUp, 'text-accent-green')}
        {statCard('Error Rate', metrics ? `${metrics.error_rate.toFixed(1)}%` : null, 'Job failure rate', Server, 'text-red-400')}
        {statCard('WS Connections', metrics?.websocket_connections ?? null, 'Active WebSocket clients', Wifi, 'text-blue-400')}
      </div>

      {/* System Resources */}
      {metrics && (metrics.cpu_usage != null || metrics.memory_usage != null) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {metrics.cpu_usage != null && (() => { const cpu = metrics.cpu_usage as number; return (
            <div className="glass-card p-6 rounded-2xl border border-border space-y-3">
              <div className="flex items-center justify-between text-xs text-text-secondary">
                <span>CPU Usage</span>
                <Cpu className="w-5 h-5 text-primary" />
              </div>
              <div className="text-3xl font-black text-text-primary">{cpu.toFixed(1)}%</div>
              <div className="w-full bg-surface rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    cpu > 80 ? 'bg-red-400' : cpu > 60 ? 'bg-accent-amber' : 'bg-accent-green'
                  }`}
                  style={{ width: `${Math.min(cpu, 100)}%` }}
                />
              </div>
              <div className="text-xs text-text-muted">Intel i5-1035G1 — 6 threads allocated</div>
            </div>
          ); })()}
          {metrics.memory_usage != null && (() => { const mem = metrics.memory_usage as number; return (
            <div className="glass-card p-6 rounded-2xl border border-border space-y-3">
              <div className="flex items-center justify-between text-xs text-text-secondary">
                <span>Memory Usage</span>
                <MemoryStick className="w-5 h-5 text-accent-purple" />
              </div>
              <div className="text-3xl font-black text-text-primary">{mem.toFixed(1)}%</div>
              <div className="w-full bg-surface rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    mem > 85 ? 'bg-red-400' : mem > 70 ? 'bg-accent-amber' : 'bg-accent-purple'
                  }`}
                  style={{ width: `${Math.min(mem, 100)}%` }}
                />
              </div>
              <div className="text-xs text-text-muted">12 GB total RAM</div>
            </div>
          ); })()}
        </div>
      )}

      {/* Provider breakdown */}
      {metrics?.providers && Object.keys(metrics.providers).length > 0 && (
        <div className="glass-panel p-6 rounded-2xl border border-border space-y-4">
          <h2 className="text-sm font-bold text-text-primary flex items-center gap-2">
            <Activity className="w-4 h-4 text-primary" />
            Activity Breakdown
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(metrics.providers).map(([key, val]) => (
              <div key={key} className="p-3 rounded-xl bg-surface/60 border border-border space-y-1">
                <div className="text-[10px] text-text-muted uppercase tracking-wider">{key.replace(/_/g, ' ')}</div>
                <div className="text-xl font-bold text-text-primary">{val as number}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cost by Provider */}
      {costs?.by_provider && Object.keys(costs.by_provider).length > 0 && (
        <div className="glass-panel p-6 rounded-2xl border border-border space-y-4">
          <h2 className="text-sm font-bold text-text-primary flex items-center gap-2">
            <Coins className="w-4 h-4 text-accent-amber" />
            Cost by Provider
          </h2>
          <div className="space-y-2">
            {Object.entries(costs.by_provider).map(([prov, cost]) => (
              <div key={prov} className="flex items-center justify-between p-2 rounded-lg bg-surface/40 border border-border">
                <span className="text-xs font-medium text-text-primary capitalize">{prov}</span>
                <span className="text-xs font-bold text-accent-amber">${(cost as number).toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-center text-[11px] text-text-muted">
        Auto-refreshes every 15 seconds
      </div>
    </div>
  );
};
