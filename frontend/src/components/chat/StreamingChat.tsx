import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useWorkspace } from '../../contexts/WorkspaceContext';
import {
  Send, Bot, User as UserIcon, Sparkles, RefreshCw, Cpu,
  Zap, Cloud, Activity, Clock, Hash, AlertTriangle, ChevronDown, Copy, Check
} from 'lucide-react';
import { ChatMessage } from '../../types/api';
import { api } from '../../services/api';

// ─── Lightweight Markdown Renderer ────────────────────────────────────────────

const MarkdownRenderer: React.FC<{ content: string }> = ({ content }) => {
  const [copiedBlock, setCopiedBlock] = useState<number | null>(null);

  const copyCode = (text: string, idx: number) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedBlock(idx);
      setTimeout(() => setCopiedBlock(null), 2000);
    });
  };

  // Split by code blocks
  const parts = content.split(/(```[\s\S]*?```)/g);
  let codeBlockIdx = 0;

  return (
    <div className="space-y-2">
      {parts.map((part, i) => {
        if (part.startsWith('```')) {
          const match = part.match(/```(\w*)\n?([\s\S]*?)```/);
          const lang = match?.[1] || 'code';
          const code = match?.[2]?.trim() || part.replace(/```/g, '').trim();
          const blockIdx = codeBlockIdx++;
          return (
            <div key={i} className="rounded-xl overflow-hidden border border-border/60 my-1.5">
              <div className="flex items-center justify-between px-3 py-1 bg-surface border-b border-border/60">
                <span className="text-[10px] text-text-muted font-mono">{lang || 'code'}</span>
                <button
                  onClick={() => copyCode(code, blockIdx)}
                  className="flex items-center gap-1 text-[10px] text-text-muted hover:text-text-primary transition-colors"
                >
                  {copiedBlock === blockIdx ? <Check className="w-3 h-3 text-accent-green" /> : <Copy className="w-3 h-3" />}
                  {copiedBlock === blockIdx ? 'copied' : 'copy'}
                </button>
              </div>
              <pre className="p-3 overflow-x-auto text-[11px] leading-relaxed text-text-secondary font-mono bg-background/60 whitespace-pre">
                <code>{code}</code>
              </pre>
            </div>
          );
        }
        // Render inline markdown (bold, italic, inline code)
        const renderInline = (text: string) => {
          const segments = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g);
          return segments.map((seg, j) => {
            if (seg.startsWith('`') && seg.endsWith('`')) {
              return <code key={j} className="px-1 py-0.5 rounded bg-surface border border-border/60 font-mono text-[10px] text-primary">{seg.slice(1, -1)}</code>;
            }
            if (seg.startsWith('**') && seg.endsWith('**')) {
              return <strong key={j} className="font-bold text-text-primary">{seg.slice(2, -2)}</strong>;
            }
            if (seg.startsWith('*') && seg.endsWith('*')) {
              return <em key={j} className="italic">{seg.slice(1, -1)}</em>;
            }
            return <span key={j}>{seg}</span>;
          });
        };
        // Split into lines for paragraph handling
        const lines = part.split('\n');
        return (
          <span key={i} className="whitespace-pre-wrap break-words">
            {lines.map((line, j) => (
              <React.Fragment key={j}>
                {renderInline(line)}
                {j < lines.length - 1 && <br />}
              </React.Fragment>
            ))}
          </span>
        );
      })}
    </div>
  );
};


// ─── Types ────────────────────────────────────────────────────────────────────

interface MessageMeta {
  provider?: string;
  model?: string;
  isLocal?: boolean;
  latencyMs?: number;
  tokens?: number;
}

interface EnrichedMessage extends ChatMessage {
  meta?: MessageMeta;
  isStreaming?: boolean;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const LOCAL_MODELS = [
  { value: 'auto', label: '⚡ Auto (smart route)', group: 'auto' },
  { value: 'qwen2.5-coder:7b', label: '🔧 qwen2.5-coder:7b', group: 'local' },
  { value: 'qwen2.5:7b', label: '💬 qwen2.5:7b', group: 'local' },
  { value: 'gemma3:4b', label: '⚡ gemma3:4b', group: 'local' },
  { value: 'llama3.2:3b', label: '🐦 llama3.2:3b', group: 'local' },
  { value: 'deepseek-r1:7b', label: '🧠 deepseek-r1:7b', group: 'local' },
  { value: 'qwen2.5:3b', label: '🆘 qwen2.5:3b (fallback)', group: 'local' },
];

const CLOUD_MODELS = [
  { value: 'cloud:groq', label: '☁️ Groq / llama-3.3-70b', group: 'cloud' },
  { value: 'cloud:openrouter', label: '☁️ OpenRouter / gpt-4o', group: 'cloud' },
];

const TASK_TYPES = [
  { value: 'chat', label: '💬 Chat', hint: 'General conversation' },
  { value: 'coding', label: '💻 Code', hint: 'Coding & bug fixes → qwen2.5-coder' },
  { value: 'reasoning', label: '🧠 Reason', hint: 'Architecture → deepseek-r1' },
  { value: 'quick', label: '⚡ Quick', hint: 'Short answers → llama3.2:3b' },
];

// ─── Helper: Provider badge ───────────────────────────────────────────────────

const ProviderBadge: React.FC<{ meta?: MessageMeta; isStreaming?: boolean }> = ({ meta, isStreaming }) => {
  if (isStreaming) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 border border-primary/30 text-primary animate-pulse">
        <Activity className="w-2.5 h-2.5" />
        streaming...
      </span>
    );
  }
  if (!meta?.provider) return null;

  const isLocal = meta.isLocal || meta.provider === 'ollama';
  const isError = meta.provider === 'agentforge-error';

  if (isError) {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-red-500/10 border border-red-500/30 text-red-400">
        <AlertTriangle className="w-2.5 h-2.5" />
        all providers failed
      </span>
    );
  }

  return (
    <div className="flex items-center gap-1.5 flex-wrap mt-1.5">
      {/* Local / Cloud badge */}
      <span
        className={`inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full border font-medium ${
          isLocal
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            : 'bg-blue-500/10 border-blue-500/30 text-blue-400'
        }`}
      >
        {isLocal ? <Cpu className="w-2.5 h-2.5" /> : <Cloud className="w-2.5 h-2.5" />}
        {isLocal ? 'Local' : 'Cloud'}
      </span>

      {/* Provider name */}
      <span className="text-[10px] text-text-muted font-mono">
        {meta.provider}
      </span>

      {/* Model name */}
      {meta.model && (
        <span className="text-[10px] text-text-muted/80 font-mono truncate max-w-[120px]" title={meta.model}>
          {meta.model}
        </span>
      )}

      {/* Latency */}
      {meta.latencyMs !== undefined && meta.latencyMs > 0 && (
        <span className="inline-flex items-center gap-0.5 text-[10px] text-text-muted">
          <Clock className="w-2.5 h-2.5" />
          {meta.latencyMs < 1000 ? `${meta.latencyMs}ms` : `${(meta.latencyMs / 1000).toFixed(1)}s`}
        </span>
      )}

      {/* Token count */}
      {meta.tokens !== undefined && meta.tokens > 0 && (
        <span className="inline-flex items-center gap-0.5 text-[10px] text-text-muted">
          <Hash className="w-2.5 h-2.5" />
          {meta.tokens} tok
        </span>
      )}

      {/* Fallback warning */}
      {!isLocal && meta.provider !== 'agentforge-error' && (
        <span className="inline-flex items-center gap-0.5 text-[10px] px-1 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400">
          <AlertTriangle className="w-2.5 h-2.5" />
          cloud fallback
        </span>
      )}
    </div>
  );
};

// ─── Main component ───────────────────────────────────────────────────────────

export const StreamingChat: React.FC = () => {
  const { currentProject } = useWorkspace();
  const [messages, setMessages] = useState<EnrichedMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedModel, setSelectedModel] = useState('auto');
  const [taskType, setTaskType] = useState('chat');
  const [chatId, setChatId] = useState<string | null>(null);
  const [showModelMenu, setShowModelMenu] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Restore chat session when project changes
  useEffect(() => {
    let cancelled = false;
    const restoreChat = async () => {
      if (!currentProject) { setChatId(null); setMessages([]); return; }
      const storageKey = `agentforge_active_chat_${currentProject.id}`;
      const storedChatId = localStorage.getItem(storageKey);
      if (storedChatId) {
        try {
          const history = await api.chats.messages(storedChatId);
          if (!cancelled) { setChatId(storedChatId); setMessages(history); }
          return;
        } catch {
          localStorage.removeItem(storageKey);
        }
      }
      if (!cancelled) { setChatId(null); setMessages([]); }
    };
    restoreChat();
    return () => { cancelled = true; };
  }, [currentProject?.id]);

  // Resolve model + provider from selected value
  const resolveModelProvider = useCallback(() => {
    if (selectedModel === 'auto') return { model: undefined, provider: undefined };
    if (selectedModel.startsWith('cloud:')) {
      const p = selectedModel.replace('cloud:', '');
      const cloudModels: Record<string, string> = {
        groq: 'llama-3.3-70b-versatile',
        openrouter: 'openai/gpt-4o',
      };
      return { model: cloudModels[p], provider: p };
    }
    // Local Ollama model
    return { model: selectedModel, provider: 'ollama' };
  }, [selectedModel]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userText = input.trim();
    setInput('');
    setShowModelMenu(false);

    const userMsg: EnrichedMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: userText,
      created_at: new Date().toISOString(),
    };
    const asstMsgId = `asst_${Date.now()}`;
    const asstMsg: EnrichedMessage = {
      id: asstMsgId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMsg, asstMsg]);
    setIsStreaming(true);

    try {
      let activeChatId = chatId;
      if (!activeChatId) {
        const createdChat = await api.chats.create({
          project_id: currentProject?.id,
          title: currentProject ? `${currentProject.name} chat` : 'Workspace chat',
        });
        activeChatId = createdChat.id;
        setChatId(activeChatId);
        if (currentProject) {
          localStorage.setItem(`agentforge_active_chat_${currentProject.id}`, activeChatId);
        }
      }

      const { model, provider } = resolveModelProvider();

      const response = await fetch(`/api/v1/chats/${activeChatId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('agentforge_token')}`,
        },
        body: JSON.stringify({
          content: userText,
          model,
          provider,
          task_type: taskType,
          stream: true,
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulated = '';
      let lastMeta: MessageMeta = {};

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const rawChunk = decoder.decode(value, { stream: true });
          const lines = rawChunk.split('\n');

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const rawData = line.slice(6).trim();
            if (rawData === '[DONE]') continue;
            try {
              const data = JSON.parse(rawData);

              if (data.meta) {
                // Final metadata sentinel
                lastMeta = {
                  provider: data.provider,
                  model: data.model,
                  isLocal: data.is_local,
                  latencyMs: data.latency_ms,
                  tokens: data.tokens,
                };
              } else if (data.content) {
                accumulated += data.content;
                // Update inline meta on each chunk too
                if (data.provider) lastMeta.provider = data.provider;
                if (data.model) lastMeta.model = data.model;
                if (data.is_local !== undefined) lastMeta.isLocal = data.is_local;

                setMessages(prev =>
                  prev.map(m =>
                    m.id === asstMsgId
                      ? { ...m, content: accumulated, isStreaming: true, meta: { ...lastMeta } }
                      : m
                  )
                );
              } else if (data.error) {
                accumulated += `\n\n⚠️ Error: ${data.error}`;
              }
            } catch {
              // skip malformed line
            }
          }
        }
      }

      // Mark streaming done, attach final meta
      setMessages(prev =>
        prev.map(m =>
          m.id === asstMsgId
            ? { ...m, content: accumulated, isStreaming: false, meta: lastMeta }
            : m
        )
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Streaming failed';
      setMessages(prev =>
        prev.map(m =>
          m.id === asstMsgId
            ? { ...m, content: `⚠️ Error: ${msg}`, isStreaming: false }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
      inputRef.current?.focus();
    }
  };

  const handleNewChat = () => {
    setChatId(null);
    setMessages([]);
    if (currentProject) {
      localStorage.removeItem(`agentforge_active_chat_${currentProject.id}`);
    }
  };

  const currentTaskLabel = TASK_TYPES.find(t => t.value === taskType)?.label ?? '💬 Chat';
  const currentModelLabel =
    [...LOCAL_MODELS, ...CLOUD_MODELS].find(m => m.value === selectedModel)?.label ?? 'auto';

  return (
    <div className="h-full flex flex-col bg-surface/90 border-l border-border text-xs">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="p-2.5 border-b border-border flex items-center justify-between bg-surface/60 select-none shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-primary" />
          <span className="font-bold text-text-primary text-[11px]">AI Assistant</span>
          <span className="text-[9px] text-text-muted bg-background px-1.5 py-0.5 rounded-full border border-border">
            Ollama-first
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Task type pills */}
          <div className="flex items-center gap-1 bg-background px-2 py-1 rounded border border-border text-[11px]">
            <Cpu className="w-3 h-3 text-accent-purple" />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-transparent border-none outline-none text-text-primary text-[11px] cursor-pointer"
            >
              <optgroup label="Auto">
                <option value="auto" className="bg-surface">auto (smart routing)</option>
              </optgroup>
              <optgroup label="Ollama (Local)">
                <option value="qwen2.5-coder:7b" className="bg-surface">qwen2.5-coder:7b</option>
                <option value="qwen2.5:7b" className="bg-surface">qwen2.5:7b</option>
                <option value="deepseek-r1:7b" className="bg-surface">deepseek-r1:7b</option>
                <option value="gemma3:4b" className="bg-surface">gemma3:4b</option>
                <option value="llama3.2:3b" className="bg-surface">llama3.2:3b</option>
              </optgroup>
              <optgroup label="Groq (Cloud)">
                <option value="llama-3.3-70b-versatile" className="bg-surface">llama-3.3-70b</option>
                <option value="gemma2-9b-it" className="bg-surface">gemma2-9b</option>
              </optgroup>
              <optgroup label="OpenRouter">
                <option value="openai/gpt-4o" className="bg-surface">gpt-4o</option>
                <option value="anthropic/claude-3.5-sonnet" className="bg-surface">claude-3.5</option>
                <option value="google/gemini-2.0-flash-001" className="bg-surface">gemini-2.0-flash</option>
              </optgroup>
            </select>
          </div>

          {/* New chat */}
          <button
            onClick={handleNewChat}
            className="p-1 hover:bg-surface-hover rounded text-text-secondary"
            title="New Chat"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* ── Message list ───────────────────────────────────────────────────── */}
      <div className="flex-1 p-3 overflow-y-auto space-y-4 min-h-0">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-6 gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
              <Cpu className="w-5 h-5 text-primary" />
            </div>
            <p className="text-xs text-text-muted leading-relaxed">
              Running locally on your machine.<br />
              <span className="text-primary font-medium">Ollama → Groq → OpenRouter</span>
            </p>
            <div className="flex flex-wrap gap-1 justify-center">
              {['What is AI?', 'Explain FastAPI', 'Write binary search', 'Review this code'].map(s => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="text-[10px] px-2 py-1 rounded-full border border-border hover:border-primary/40 hover:bg-primary/5 text-text-muted hover:text-text-primary transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              {/* Avatar */}
              <div
                className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  msg.role === 'user' ? 'bg-primary text-black' : 'bg-accent-purple text-white'
                }`}
              >
                {msg.role === 'user'
                  ? <UserIcon className="w-2.5 h-2.5" />
                  : <Bot className="w-2.5 h-2.5" />
                }
              </div>

              {/* Bubble */}
              <div className={`max-w-[85%] flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div
                  className={`rounded-xl px-3 py-2 text-xs leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-primary/15 border border-primary/30 text-text-primary'
                      : 'glass-card border border-border text-text-primary'
                  }`}
                >
                  {msg.content ? (
                    <MarkdownRenderer content={msg.content} />
                  ) : (
                    <div className="flex items-center gap-1.5 py-1 text-text-muted">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-accent-purple animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-accent-pink animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  )}
                </div>

                {/* Provider badge below assistant messages */}
                {msg.role === 'assistant' && (
                  <ProviderBadge meta={msg.meta} isStreaming={msg.isStreaming} />
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Model selector bar ─────────────────────────────────────────────── */}
      <div className="px-2 pb-1 shrink-0 relative">
        <button
          onClick={() => setShowModelMenu(p => !p)}
          className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-border hover:border-primary/40 bg-background text-[10px] text-text-muted hover:text-text-primary transition-all"
        >
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3 h-3 text-accent-purple" />
            <span className="truncate max-w-[160px]">{currentModelLabel}</span>
            <span className="text-text-muted/50">·</span>
            <span>{currentTaskLabel}</span>
          </div>
          <ChevronDown className={`w-3 h-3 transition-transform ${showModelMenu ? 'rotate-180' : ''}`} />
        </button>

        {showModelMenu && (
          <div className="absolute bottom-full left-2 right-2 mb-1 bg-surface border border-border rounded-xl shadow-2xl z-50 overflow-hidden">
            <div className="p-1.5">
              <p className="text-[9px] uppercase tracking-wider text-text-muted px-2 py-1">🖥 Local (Ollama)</p>
              {LOCAL_MODELS.map(m => (
                <button
                  key={m.value}
                  onClick={() => { setSelectedModel(m.value); setShowModelMenu(false); }}
                  className={`w-full text-left text-[11px] px-2.5 py-1.5 rounded-lg transition-all ${
                    selectedModel === m.value
                      ? 'bg-primary/15 text-primary font-medium'
                      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                  }`}
                >
                  {m.label}
                </button>
              ))}
              <div className="h-px bg-border my-1" />
              <p className="text-[9px] uppercase tracking-wider text-text-muted px-2 py-1">☁️ Cloud Fallback</p>
              {CLOUD_MODELS.map(m => (
                <button
                  key={m.value}
                  onClick={() => { setSelectedModel(m.value); setShowModelMenu(false); }}
                  className={`w-full text-left text-[11px] px-2.5 py-1.5 rounded-lg transition-all ${
                    selectedModel === m.value
                      ? 'bg-blue-500/15 text-blue-400 font-medium'
                      : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Input ──────────────────────────────────────────────────────────── */}
      <form
        onSubmit={handleSend}
        className="px-2 pb-2 shrink-0 flex items-center gap-1.5"
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder={isStreaming ? 'Waiting for response...' : 'Ask anything about your code...'}
          disabled={isStreaming}
          className="flex-1 bg-surface border border-border rounded-xl px-3 py-2 text-xs text-text-primary outline-none focus:border-primary/60 placeholder:text-text-muted disabled:opacity-50 transition-all"
        />
        <button
          type="submit"
          disabled={isStreaming || !input.trim()}
          className="p-2 rounded-xl bg-gradient-to-r from-primary to-accent-purple hover:opacity-90 disabled:opacity-40 transition-all"
        >
          {isStreaming
            ? <Zap className="w-3.5 h-3.5 text-black animate-pulse" />
            : <Send className="w-3.5 h-3.5 text-black" />
          }
        </button>
      </form>
    </div>
  );
};
