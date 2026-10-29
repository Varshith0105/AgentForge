import React, { useRef } from 'react';
import MonacoEditor from '@monaco-editor/react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { X, FileCode, Circle } from 'lucide-react';

const LANG_ICON: Record<string, string> = {
  python: '🐍', typescript: '🔷', javascript: '💛', json: '📋',
  html: '🌐', css: '🎨', markdown: '📝', yaml: '⚙️', sql: '🗄️',
  shell: '💻', go: '🔵', rust: '🦀', plaintext: '📄',
};

export const CodeEditor: React.FC = () => {
  const { openTabs, activeTabId, closeTab, setActiveTabId, openTabs: tabs } = useWorkspace();
  const activeTab = openTabs.find(t => t.id === activeTabId);

  if (openTabs.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-background text-center px-8">
        <div className="w-16 h-16 rounded-2xl bg-primary/5 border border-primary/10 flex items-center justify-center mb-4">
          <FileCode className="w-8 h-8 text-primary/30" />
        </div>
        <h3 className="text-sm font-bold text-text-secondary mb-1">No file open</h3>
        <p className="text-[11px] text-text-muted leading-relaxed max-w-xs">
          Select a file from the Explorer to open it here. Files open in tabs for easy switching.
        </p>
        <div className="mt-4 flex flex-wrap gap-1.5 justify-center text-[10px] text-text-muted">
          <span className="px-2 py-0.5 rounded border border-border">← Browse files</span>
          <span className="px-2 py-0.5 rounded border border-border">Clone a repo</span>
          <span className="px-2 py-0.5 rounded border border-border">Ask AI to explain code</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-background overflow-hidden">
      {/* Tab bar */}
      <div className="flex items-end bg-surface border-b border-border overflow-x-auto flex-shrink-0 scrollbar-none">
        {openTabs.map(tab => {
          const isActive = tab.id === activeTabId;
          const icon = LANG_ICON[tab.language] || '📄';
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTabId(tab.id)}
              className={`group flex items-center gap-1.5 px-3 py-1.5 text-[11px] border-r border-border transition-all flex-shrink-0 min-w-0 max-w-[180px] relative ${
                isActive
                  ? 'bg-background text-text-primary border-b-2 border-b-primary -mb-px'
                  : 'bg-surface text-text-muted hover:bg-surface-hover hover:text-text-primary'
              }`}
              title={tab.path}
            >
              <span className="flex-shrink-0 text-xs">{icon}</span>
              <span className="truncate flex-1">{tab.name}</span>
              {tab.isDirty && (
                <Circle className="w-1.5 h-1.5 text-accent-amber fill-current flex-shrink-0" />
              )}
              <span
                onClick={(e) => { e.stopPropagation(); closeTab(tab.id); }}
                className="flex-shrink-0 p-0.5 rounded hover:bg-surface-hover opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
              >
                <X className="w-3 h-3" />
              </span>
            </button>
          );
        })}
      </div>

      {/* File path breadcrumb */}
      {activeTab && (
        <div className="px-3 py-1 bg-background border-b border-border flex items-center gap-1 flex-shrink-0">
          <span className="text-[10px] text-text-muted font-mono truncate">{activeTab.path}</span>
          <span className="ml-auto text-[9px] text-text-muted flex-shrink-0">{activeTab.language}</span>
        </div>
      )}

      {/* Monaco Editor */}
      {activeTab ? (
        <div className="flex-1 min-h-0">
          <MonacoEditor
            height="100%"
            language={activeTab.language}
            value={activeTab.content}
            theme="vs-dark"
            options={{
              readOnly: false,
              minimap: { enabled: true, scale: 0.6 },
              fontSize: 13,
              lineHeight: 20,
              fontFamily: '"JetBrains Mono", "Fira Code", monospace',
              fontLigatures: true,
              scrollBeyondLastLine: false,
              smoothScrolling: true,
              cursorBlinking: 'smooth',
              cursorSmoothCaretAnimation: 'on',
              renderWhitespace: 'boundary',
              bracketPairColorization: { enabled: true },
              guides: { bracketPairs: true },
              wordWrap: 'on',
              padding: { top: 8, bottom: 8 },
              renderLineHighlight: 'gutter',
              formatOnPaste: true,
              formatOnType: false,
              tabSize: 2,
              insertSpaces: true,
            }}
          />
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-text-muted text-xs">
          Select a tab to view file content
        </div>
      )}
    </div>
  );
};
