import React, { useEffect, useState, useCallback } from 'react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import { api, FileTreeNode } from '../../services/api';
import { getErrorMessage } from '../../utils/errors';
import {
  Folder, FolderOpen, File, FileCode, ChevronRight, ChevronDown,
  RefreshCw, Loader2, Search, GitBranch, AlertCircle
} from 'lucide-react';

const FILE_ICONS: Record<string, string> = {
  python: '🐍', typescript: '🔷', javascript: '💛', json: '📋',
  html: '🌐', css: '🎨', markdown: '📝', yaml: '⚙️', sql: '🗄️',
  shell: '💻', go: '🔵', rust: '🦀', java: '☕', cpp: '⚙️',
  ruby: '💎', php: '🐘', swift: '🍎', kotlin: '🎯', plaintext: '📄',
};

interface FileTreeItemProps {
  node: FileTreeNode;
  depth: number;
  onFileClick: (node: FileTreeNode) => void;
  activeFilePath?: string;
}

const FileTreeItem: React.FC<FileTreeItemProps> = ({ node, depth, onFileClick, activeFilePath }) => {
  const [isOpen, setIsOpen] = useState(depth === 0);
  const isActive = node.path === activeFilePath;
  const indent = depth * 12;

  if (node.type === 'directory') {
    return (
      <div>
        <button
          onClick={() => setIsOpen(o => !o)}
          className={`w-full flex items-center gap-1 px-2 py-0.5 text-left text-[11px] hover:bg-surface-hover transition-colors group`}
          style={{ paddingLeft: `${8 + indent}px` }}
        >
          <span className="text-text-muted flex-shrink-0">
            {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </span>
          <span className="flex-shrink-0">
            {isOpen ? <FolderOpen className="w-3.5 h-3.5 text-accent-amber" /> : <Folder className="w-3.5 h-3.5 text-accent-amber" />}
          </span>
          <span className="truncate text-text-secondary group-hover:text-text-primary">{node.name}</span>
        </button>
        {isOpen && node.children && (
          <div>
            {node.children.map(child => (
              <FileTreeItem
                key={child.path}
                node={child}
                depth={depth + 1}
                onFileClick={onFileClick}
                activeFilePath={activeFilePath}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  const icon = FILE_ICONS[node.language || 'plaintext'] || '📄';

  return (
    <button
      onClick={() => onFileClick(node)}
      className={`w-full flex items-center gap-1.5 px-2 py-0.5 text-left text-[11px] transition-colors group ${
        isActive
          ? 'bg-primary/10 border-r-2 border-primary text-primary'
          : 'hover:bg-surface-hover text-text-secondary hover:text-text-primary'
      }`}
      style={{ paddingLeft: `${8 + indent}px` }}
      title={node.path}
    >
      <span className="flex-shrink-0 text-xs">{icon}</span>
      <span className="truncate flex-1">{node.name}</span>
      {node.size !== undefined && (
        <span className="text-[9px] text-text-muted flex-shrink-0 opacity-0 group-hover:opacity-100">
          {node.size < 1024 ? `${node.size}B` : `${(node.size / 1024).toFixed(1)}K`}
        </span>
      )}
    </button>
  );
};

export const FileExplorer: React.FC = () => {
  const { currentProject, openFile, openTabs, activeTabId } = useWorkspace();
  const [tree, setTree] = useState<FileTreeNode[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [totalFiles, setTotalFiles] = useState(0);
  const [loadingFile, setLoadingFile] = useState<string | null>(null);

  const loadTree = useCallback(async () => {
    if (!currentProject) { setTree([]); return; }
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.files.getTree(currentProject.id);
      setTree(res.tree);
      setTotalFiles(res.total_files);
    } catch (err: unknown) {
      const msg = getErrorMessage(err, 'Failed to load file tree');
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [currentProject?.id]);

  useEffect(() => { loadTree(); }, [loadTree]);

  const handleFileClick = async (node: FileTreeNode) => {
    if (!currentProject || node.type === 'directory') return;
    setLoadingFile(node.path);
    try {
      const fileData = await api.files.getContent(currentProject.id, node.path);
      openFile({
        name: fileData.name,
        path: fileData.path,
        content: fileData.content,
        language: fileData.language,
      });
    } catch (err: any) {
      // If file is too large or binary, open with placeholder
      openFile({
        name: node.name,
        path: node.path,
        content: `// Unable to load file: ${getErrorMessage(err, 'Unknown error')}\n// File: ${node.path}`,
        language: node.language || 'plaintext',
      });
    } finally {
      setLoadingFile(null);
    }
  };

  // Get active tab path for highlighting
  const activeTab = openTabs.find(t => t.id === activeTabId);
  const activeFilePath = activeTab?.path;

  // Filter tree for search
  const filterTree = (nodes: FileTreeNode[], query: string): FileTreeNode[] => {
    if (!query) return nodes;
    const q = query.toLowerCase();
    return nodes.reduce<FileTreeNode[]>((acc, node) => {
      if (node.type === 'file' && node.name.toLowerCase().includes(q)) {
        acc.push(node);
      } else if (node.type === 'directory' && node.children) {
        const filtered = filterTree(node.children, query);
        if (filtered.length > 0) acc.push({ ...node, children: filtered });
      }
      return acc;
    }, []);
  };

  const displayTree = searchQuery ? filterTree(tree, searchQuery) : tree;

  return (
    <div className="h-full flex flex-col bg-surface border-r border-border select-none overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2 border-b border-border flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">Explorer</span>
          <button
            onClick={loadTree}
            disabled={isLoading}
            className="p-0.5 hover:bg-surface-hover rounded text-text-muted hover:text-text-primary transition"
            title="Refresh"
          >
            <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search files..."
            className="w-full bg-background border border-border rounded-lg pl-6 pr-2 py-1 text-[10px] text-text-primary placeholder:text-text-muted outline-none focus:border-primary/50 transition"
          />
        </div>
      </div>

      {/* Project name */}
      {currentProject && (
        <div className="px-3 py-1.5 border-b border-border flex-shrink-0">
          <div className="flex items-center gap-1.5">
            <GitBranch className="w-3 h-3 text-accent-green flex-shrink-0" />
            <span className="text-[10px] font-semibold text-text-primary truncate">{currentProject.name}</span>
            {totalFiles > 0 && (
              <span className="ml-auto text-[9px] text-text-muted">{totalFiles} files</span>
            )}
          </div>
          {currentProject.branch && (
            <span className="text-[9px] text-accent-green/70 ml-4">{currentProject.branch}</span>
          )}
        </div>
      )}

      {/* File tree */}
      <div className="flex-1 overflow-y-auto py-1 relative">
        {!currentProject ? (
          <div className="p-4 text-center">
            <Folder className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-30" />
            <p className="text-[10px] text-text-muted">No project selected</p>
            <p className="text-[9px] text-text-muted mt-1">Clone or create a project to browse files</p>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="w-4 h-4 animate-spin text-primary" />
          </div>
        ) : error ? (
          <div className="p-3 m-2 rounded-lg bg-red-500/10 border border-red-500/20">
            <div className="flex items-center gap-1.5 mb-1">
              <AlertCircle className="w-3 h-3 text-red-400" />
              <span className="text-[10px] text-red-400 font-semibold">Load Failed</span>
            </div>
            <p className="text-[10px] text-red-400/70">{error}</p>
            <button onClick={loadTree} className="mt-1.5 text-[10px] text-primary hover:underline">Retry</button>
          </div>
        ) : displayTree.length === 0 ? (
          <div className="p-4 text-center">
            <p className="text-[10px] text-text-muted">
              {searchQuery ? 'No files match your search' : 'No files in repository'}
            </p>
          </div>
        ) : (
          displayTree.map(node => (
            <FileTreeItem
              key={node.path}
              node={node}
              depth={0}
              onFileClick={handleFileClick}
              activeFilePath={activeFilePath}
            />
          ))
        )}
        {loadingFile && (
          <div className="absolute bottom-0 left-0 right-0 bg-surface/90 p-1.5 flex items-center gap-1.5 border-t border-border">
            <Loader2 className="w-3 h-3 animate-spin text-primary" />
            <span className="text-[10px] text-text-muted truncate">{loadingFile}</span>
          </div>
        )}
      </div>
    </div>
  );
};
