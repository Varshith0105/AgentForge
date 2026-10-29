import React, { useEffect, useState, useRef } from 'react';
import { api } from '../services/api';
import { AgentInfo } from '../types/api';
import { Bot, Play, CheckCircle2, X, Loader2, ChevronDown, Zap, Cpu, Shield, Wrench, Activity, TestTube, Bug, BookOpen } from 'lucide-react';
import { useWorkspace } from '../contexts/WorkspaceContext';

const AGENT_ICONS: Record<string, React.ComponentType<any>> = {
  planner: Zap, repository: Cpu, security: Shield, architecture: Wrench,
  performance: Activity, testing: TestTube, bug_detection: Bug, documentation: BookOpen,
};

const AGENT_COLORS: Record<string, string> = {
  planner: 'text-primary bg-primary/10 border-primary/30',
  repository: 'text-accent-purple bg-accent-purple/10 border-accent-purple/30',
  security: 'text-red-400 bg-red-400/10 border-red-400/30',
  architecture: 'text-accent-amber bg-accent-amber/10 border-accent-amber/30',
  performance: 'text-accent-green bg-accent-green/10 border-accent-green/30',
  testing: 'text-blue-400 bg-blue-400/10 border-blue-400/30',
  bug_detection: 'text-orange-400 bg-orange-400/10 border-orange-400/30',
  documentation: 'text-pink-400 bg-pink-400/10 border-pink-400/30',
};

export const AgentsPage: React.FC = () => {
  const { currentProject } = useWorkspace();
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showDispatch, setShowDispatch] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState('planner');
  const [task, setTask] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [streamedOutput, setStreamedOutput] = useState('');
  const [meta, setMeta] = useState<{ provider?: string; model?: string } | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.agents.status()
      .then((res) => setAgents(res.agents))
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [streamedOutput]);

  const handleDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!task.trim() || isRunning) return;
    setIsRunning(true);
    setStreamedOutput('');
    setMeta(null);

    try {
      const response = await api.agents.runStream({
        project_id: currentProject?.id,
        task: task.trim(),
        agent_type: selectedAgent,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const rawChunk = decoder.decode(value, { stream: true });
          for (const line of rawChunk.split('\n')) {
            if (!line.startsWith('data: ')) continue;
            const raw = line.slice(6).trim();
            if (raw === '[DONE]') break;
            try {
              const data = JSON.parse(raw);
              if (data.content) {
                setStreamedOutput(prev => prev + data.content);
              }
              if (data.done || data.provider) {
                setMeta({ provider: data.provider, model: data.model });
              }
              if (data.error) {
                setStreamedOutput(prev => prev + `\n\n⚠️ Error: ${data.error}`);
              }
            } catch {}
          }
        }
      }
    } catch (err: any) {
      setStreamedOutput(`Error: ${err?.message || 'Failed to run agent'}`);
    } finally {
      setIsRunning(false);
    }
  };

  const agentTypeOptions = [
    { value: 'planner', label: 'Planner Agent' },
    { value: 'repository', label: 'Repository Agent' },
    { value: 'security', label: 'Security Agent' },
    { value: 'architecture', label: 'Architecture Agent' },
    { value: 'performance', label: 'Performance Agent' },
    { value: 'testing', label: 'Testing Agent' },
    { value: 'bug_detection', label: 'Bug Detection Agent' },
    { value: 'documentation', label: 'Documentation Agent' },
  ];

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 bg-background">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-text-primary">Multi-Agent System</h1>
          <p className="text-xs text-text-secondary">8 specialized AI engineering agents — powered by real LLMs</p>
        </div>
        <button
          onClick={() => setShowDispatch(true)}
          className="px-4 py-2 rounded-xl bg-primary text-black font-bold text-xs hover:bg-primary-hover shadow-glow transition flex items-center gap-1.5"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Dispatch Agent Task</span>
        </button>
      </div>

      {isLoading ? (
        <div className="p-12 text-center text-xs text-text-muted animate-pulse">Loading AI Agent Swarm...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {agents.map((agent, idx) => {
            const Icon = AGENT_ICONS[agent.type] || Bot;
            const colorClass = AGENT_COLORS[agent.type] || 'text-primary bg-primary/10 border-primary/30';
            return (
              <div key={idx} className="glass-card p-5 rounded-2xl border border-border space-y-3 hover:border-primary/30 transition-all">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-xl border flex items-center justify-center ${colorClass}`}>
                      <Icon className="w-4.5 h-4.5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-text-primary">{agent.name}</h3>
                      <p className="text-[11px] text-text-muted font-mono">type: {agent.type}</p>
                    </div>
                  </div>
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-accent-green/20 text-accent-green font-bold">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{agent.status}</span>
                  </span>
                </div>
                <p className="text-xs text-text-secondary leading-relaxed">{agent.description}</p>
                <button
                  onClick={() => { setSelectedAgent(agent.type); setShowDispatch(true); }}
                  className="w-full py-1.5 rounded-lg bg-surface border border-border text-[11px] text-text-secondary hover:text-primary hover:border-primary/40 transition"
                >
                  Run {agent.name}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Dispatch Modal */}
      {showDispatch && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl glass-panel p-6 rounded-2xl border border-border shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2 font-bold text-sm text-text-primary">
                <Bot className="w-4 h-4 text-accent-purple" />
                <span>Dispatch Agent Task</span>
                {currentProject && (
                  <span className="text-[11px] text-text-muted font-normal">— {currentProject.name}</span>
                )}
              </div>
              <button onClick={() => { setShowDispatch(false); setStreamedOutput(''); }} className="p-1 hover:bg-surface-hover rounded text-text-muted">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleDispatch} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-text-secondary">Agent Type</label>
                <div className="relative">
                  <select
                    value={selectedAgent}
                    onChange={(e) => setSelectedAgent(e.target.value)}
                    className="w-full appearance-none bg-surface border border-border rounded-xl px-3 py-2.5 text-xs text-text-primary outline-none focus:border-primary cursor-pointer"
                  >
                    {agentTypeOptions.map((opt) => (
                      <option key={opt.value} value={opt.value} className="bg-surface">{opt.label}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted pointer-events-none" />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-text-secondary">Task Description</label>
                <textarea
                  value={task}
                  onChange={(e) => setTask(e.target.value)}
                  rows={3}
                  placeholder="Describe what the agent should do..."
                  className="w-full bg-surface border border-border rounded-xl px-3 py-2.5 text-xs text-text-primary outline-none focus:border-primary placeholder:text-text-muted resize-none"
                />
              </div>

              {/* Streaming output */}
              {(streamedOutput || isRunning) && (
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <label className="text-xs font-semibold text-text-secondary">Agent Output</label>
                    {isRunning && <span className="flex items-center gap-1 text-[10px] text-primary animate-pulse"><Activity className="w-3 h-3" /> Streaming...</span>}
                    {meta && !isRunning && (
                      <span className="text-[10px] text-text-muted">{meta.provider} / {meta.model}</span>
                    )}
                  </div>
                  <div
                    ref={outputRef}
                    className="bg-background border border-border rounded-xl p-3 text-xs text-text-secondary font-mono whitespace-pre-wrap max-h-56 overflow-y-auto leading-relaxed"
                  >
                    {streamedOutput || (isRunning ? <span className="text-text-muted animate-pulse">Agent is thinking...</span> : '')}
                    {isRunning && <span className="inline-block w-1.5 h-3.5 bg-primary animate-pulse ml-0.5 align-middle" />}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => { setShowDispatch(false); setStreamedOutput(''); setMeta(null); }}
                  className="px-4 py-2 rounded-xl bg-surface border border-border text-xs text-text-secondary hover:text-text-primary"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={!task.trim() || isRunning}
                  className="px-4 py-2 rounded-xl bg-primary text-black font-bold text-xs hover:bg-primary-hover shadow-glow transition disabled:opacity-50 flex items-center gap-1.5"
                >
                  {isRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                  {isRunning ? 'Running...' : 'Dispatch'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
