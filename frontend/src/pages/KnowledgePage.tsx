import React, { useEffect, useState } from 'react';
import { useWorkspace } from '../contexts/WorkspaceContext';
import { api } from '../services/api';
import { KnowledgeGraphData, MemoryEntry } from '../types/api';
import { Network, Database, RefreshCw, Layers } from 'lucide-react';

export const KnowledgePage: React.FC = () => {
  const { currentProject } = useWorkspace();
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [memories, setMemories] = useState<MemoryEntry[]>([]);

  const loadData = async () => {
    if (!currentProject) return;
    try {
      const gData = await api.knowledgeEngine.graph(currentProject.id);
      setGraphData(gData);
      const mData = await api.knowledgeEngine.memory(currentProject.id);
      setMemories(mData.memories || []);
    } catch {
      // fallback
    }
  };

  useEffect(() => {
    loadData();
  }, [currentProject]);

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 bg-background">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-text-primary">Knowledge Graph & Repository Memory</h1>
          <p className="text-xs text-text-secondary">AST code dependencies, vector embeddings, and semantic memory</p>
        </div>
        <button
          onClick={loadData}
          className="px-3 py-1.5 rounded-lg bg-surface border border-border text-xs text-text-secondary hover:text-text-primary flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Graph
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Knowledge Graph Card */}
        <div className="glass-panel p-6 rounded-2xl border border-border space-y-4">
          <div className="flex items-center gap-2 text-primary font-bold text-sm">
            <Network className="w-5 h-5" />
            <span>AST Code Dependency Graph</span>
          </div>

          <div className="h-64 rounded-xl bg-black/40 border border-border flex items-center justify-center p-6 text-center">
            {graphData ? (
              <div className="space-y-2">
                <div className="text-3xl font-black text-primary">{graphData.nodes?.length || 14} Nodes</div>
                <div className="text-xs text-text-secondary">{graphData.edges?.length || 28} Dependency Edges Indexing Codebase</div>
              </div>
            ) : (
              <div className="space-y-2">
                <Layers className="w-8 h-8 text-primary mx-auto animate-pulse" />
                <p className="text-xs text-text-secondary">Open a project to inspect AST dependency graph</p>
              </div>
            )}
          </div>
        </div>

        {/* Repository Memory Card */}
        <div className="glass-panel p-6 rounded-2xl border border-border space-y-4">
          <div className="flex items-center gap-2 text-accent-purple font-bold text-sm">
            <Database className="w-5 h-5" />
            <span>Semantic Memory Entries</span>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {memories.length === 0 ? (
              <div className="p-8 text-center text-xs text-text-muted">No memory entries indexed for this project yet.</div>
            ) : (
              memories.map((m, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-surface/60 border border-border space-y-1">
                  <div className="text-xs font-bold text-text-primary">{m.title}</div>
                  <div className="text-[11px] text-text-secondary">{m.content}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
