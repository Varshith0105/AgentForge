import React, { useState, useRef, useEffect } from 'react';
import { api } from '../../services/api';
import { Terminal as TerminalIcon, Play, Trash2, X } from 'lucide-react';

interface TerminalLine {
  text: string;
  type: 'stdout' | 'stderr' | 'command' | 'info';
}

export const TerminalPanel: React.FC<{ onClose?: () => void }> = ({ onClose }) => {
  const [lines, setLines] = useState<TerminalLine[]>([
    { text: 'AgentForge Engineering Terminal v2.0.0', type: 'info' },
    { text: 'Type any shell command to execute against project backend', type: 'info' },
  ]);
  const [input, setInput] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  const handleCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isExecuting) return;

    const cmd = input.trim();
    setInput('');
    setLines((prev) => [...prev, { text: `$ ${cmd}`, type: 'command' }]);

    if (cmd === 'clear') {
      setLines([]);
      return;
    }

    setIsExecuting(true);
    try {
      const res = await api.terminal.execute(cmd);
      if (res.stdout) {
        setLines((prev) => [...prev, { text: res.stdout, type: 'stdout' }]);
      }
      if (res.stderr) {
        setLines((prev) => [...prev, { text: res.stderr, type: 'stderr' }]);
      }
    } catch (err: any) {
      setLines((prev) => [...prev, { text: `Error: ${err.message || 'Execution failed'}`, type: 'stderr' }]);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-background font-mono text-xs border-t border-border">
      {/* Panel Header */}
      <div className="h-8 bg-surface/90 px-3 flex items-center justify-between border-b border-border select-none">
        <div className="flex items-center gap-2 text-text-secondary">
          <TerminalIcon className="w-3.5 h-3.5 text-primary" />
          <span className="font-semibold text-[11px] text-text-primary uppercase tracking-wider">Terminal</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setLines([])} className="p-1 hover:bg-surface-hover rounded text-text-muted hover:text-text-primary" title="Clear">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          {onClose && (
            <button onClick={onClose} className="p-1 hover:bg-surface-hover rounded text-text-muted hover:text-text-primary" title="Close">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Terminal Output */}
      <div className="flex-1 p-3 overflow-y-auto space-y-1 bg-black/40 font-mono text-[12px] leading-relaxed">
        {lines.map((line, idx) => (
          <div
            key={idx}
            className={
              line.type === 'command'
                ? 'text-primary font-bold'
                : line.type === 'stderr'
                ? 'text-red-400'
                : line.type === 'info'
                ? 'text-accent-purple font-medium'
                : 'text-text-primary whitespace-pre-wrap'
            }
          >
            {line.text}
          </div>
        ))}
        {isExecuting && <div className="text-text-muted animate-pulse">Running command...</div>}
        <div ref={bottomRef} />
      </div>

      {/* Input Prompt */}
      <form onSubmit={handleCommand} className="flex items-center px-3 py-1.5 bg-surface/60 border-t border-border">
        <span className="text-primary font-bold mr-2">$</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Execute shell command..."
          className="flex-1 bg-transparent border-none outline-none text-text-primary font-mono text-xs placeholder:text-text-muted"
        />
        <button type="submit" disabled={isExecuting} className="p-1 hover:bg-surface-hover rounded text-primary">
          <Play className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
};
