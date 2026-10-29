import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Settings as SettingsIcon, Save, Cpu, Key, CheckCircle2, AlertCircle, RefreshCw, ExternalLink } from 'lucide-react';

interface ProviderStatus {
  name: string;
  label: string;
  configured: boolean;
  color: string;
}

export const SettingsPage: React.FC = () => {
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('auto');
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [providers, setProviders] = useState<ProviderStatus[]>([]);

  useEffect(() => {
    Promise.all([
      api.settings.getConfig().catch(() => ({ provider: 'ollama', model: 'auto' })),
      api.settings.getProviders().catch(() => ({ configured: { ollama: true, groq: true, openrouter: true, nvidia: true } })),
    ]).then(([cfg, provData]) => {
      if (cfg.provider) setProvider(cfg.provider);
      if (cfg.model) setModel(cfg.model);

      const conf: Record<string, boolean> = (provData as any)?.configured || {};
      const providerList: ProviderStatus[] = [
        { name: 'ollama', label: 'Ollama (Local CPU)', configured: conf.ollama ?? true, color: 'text-accent-green' },
        { name: 'groq', label: 'Groq (Fast Cloud)', configured: conf.groq ?? false, color: 'text-accent-purple' },
        { name: 'openrouter', label: 'OpenRouter (Multi-Model)', configured: conf.openrouter ?? false, color: 'text-primary' },
        { name: 'nvidia', label: 'NVIDIA NIM', configured: conf.nvidia ?? false, color: 'text-accent-amber' },
        { name: 'google', label: 'Google Gemini', configured: conf.google ?? false, color: 'text-blue-400' },
        { name: 'openai', label: 'OpenAI', configured: conf.openai ?? false, color: 'text-green-400' },
      ];
      setProviders(providerList);
    });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveError('');
    try {
      await api.settings.updateConfig({ provider, model });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setSaveError(err?.response?.data?.detail || 'Failed to save configuration.');
    } finally {
      setIsSaving(false);
    }
  };

  const modelOptions: Record<string, { value: string; label: string }[]> = {
    ollama: [
      { value: 'auto', label: 'Auto (Smart per-task routing)' },
      { value: 'qwen2.5-coder:7b', label: 'Qwen2.5-Coder 7B (Code)' },
      { value: 'qwen2.5:7b', label: 'Qwen2.5 7B (Chat)' },
      { value: 'deepseek-r1:7b', label: 'DeepSeek-R1 7B (Reasoning)' },
      { value: 'gemma3:4b', label: 'Gemma3 4B (Fast)' },
      { value: 'llama3.2:3b', label: 'Llama3.2 3B (Quick)' },
    ],
    groq: [
      { value: 'llama-3.3-70b-versatile', label: 'Llama 3.3 70B Versatile' },
      { value: 'llama-3.1-8b-instant', label: 'Llama 3.1 8B Instant' },
      { value: 'mixtral-8x7b-32768', label: 'Mixtral 8x7B' },
      { value: 'gemma2-9b-it', label: 'Gemma2 9B' },
    ],
    openrouter: [
      { value: 'auto', label: 'Auto-select best model' },
      { value: 'openai/gpt-4o', label: 'GPT-4o' },
      { value: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
      { value: 'google/gemini-2.0-flash-001', label: 'Gemini 2.0 Flash' },
      { value: 'meta-llama/llama-3.3-70b-instruct', label: 'Llama 3.3 70B' },
      { value: 'deepseek/deepseek-r1', label: 'DeepSeek R1' },
    ],
    nvidia: [
      { value: 'meta/llama-3.3-70b-instruct', label: 'Llama 3.3 70B' },
      { value: 'nvidia/llama-3.1-nemotron-70b-instruct', label: 'Nemotron 70B' },
    ],
    google: [
      { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
      { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
      { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
    ],
    openai: [
      { value: 'gpt-4o', label: 'GPT-4o' },
      { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
      { value: 'o1-mini', label: 'o1-mini' },
    ],
  };

  const currentModels = modelOptions[provider] || modelOptions.ollama;

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 bg-background">
      <div>
        <h1 className="text-2xl font-extrabold text-text-primary">AI OS & Platform Settings</h1>
        <p className="text-xs text-text-secondary">Configure LLM providers, model routing, and platform preferences</p>
      </div>

      {saved && (
        <div className="p-3 rounded-xl bg-accent-green/10 border border-accent-green/30 text-accent-green text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          Configuration saved successfully!
        </div>
      )}
      {saveError && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {saveError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Provider Config */}
        <form onSubmit={handleSave} className="glass-panel p-6 rounded-2xl border border-border space-y-5">
          <h2 className="text-sm font-bold text-text-primary flex items-center gap-2">
            <Cpu className="w-4 h-4 text-primary" />
            AI Provider Configuration
          </h2>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-text-secondary">Primary AI Provider</label>
            <select
              value={provider}
              onChange={(e) => { setProvider(e.target.value); setModel('auto'); }}
              className="w-full bg-surface border border-border rounded-xl px-3 py-2.5 text-xs text-text-primary outline-none focus:border-primary cursor-pointer"
            >
              <option value="ollama" className="bg-surface">Ollama (Local CPU — Free, Private)</option>
              <option value="groq" className="bg-surface">Groq (Ultra-Fast Cloud)</option>
              <option value="openrouter" className="bg-surface">OpenRouter (Multi-Model Gateway)</option>
              <option value="nvidia" className="bg-surface">NVIDIA NIM</option>
              <option value="google" className="bg-surface">Google Gemini</option>
              <option value="openai" className="bg-surface">OpenAI</option>
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-text-secondary">Default Model</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl px-3 py-2.5 text-xs text-text-primary outline-none focus:border-primary cursor-pointer"
            >
              {currentModels.map((m) => (
                <option key={m.value} value={m.value} className="bg-surface">{m.label}</option>
              ))}
            </select>
          </div>

          {provider === 'ollama' && (
            <div className="p-3 rounded-xl bg-accent-green/5 border border-accent-green/20 text-xs text-accent-green/80 space-y-1">
              <p className="font-semibold text-accent-green">✓ Local CPU Inference Active</p>
              <p>Optimised for Intel i5-1035G1 with 12 GB RAM. No API key required.</p>
              <p className="text-text-muted">Smart per-task routing: coding → qwen2.5-coder:7b | reasoning → deepseek-r1:7b | chat → qwen2.5:7b</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isSaving}
            className="w-full py-2.5 rounded-xl bg-primary text-black font-bold text-xs hover:bg-primary-hover shadow-glow transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            {isSaving ? 'Saving...' : 'Save Configuration'}
          </button>
        </form>

        {/* Provider Status */}
        <div className="glass-panel p-6 rounded-2xl border border-border space-y-4">
          <h2 className="text-sm font-bold text-text-primary flex items-center gap-2">
            <Key className="w-4 h-4 text-accent-purple" />
            Provider Status
          </h2>
          <div className="space-y-2">
            {providers.map((p) => (
              <div key={p.name} className="flex items-center justify-between p-3 rounded-xl bg-surface/60 border border-border">
                <div className="flex items-center gap-2.5">
                  <div className={`w-2 h-2 rounded-full ${p.configured ? 'bg-accent-green' : 'bg-border'}`} />
                  <span className="text-xs font-medium text-text-primary">{p.label}</span>
                </div>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  p.configured
                    ? 'bg-accent-green/20 text-accent-green'
                    : 'bg-surface text-text-muted border border-border'
                }`}>
                  {p.configured ? 'CONFIGURED' : 'NOT SET'}
                </span>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-text-muted">
            Configure API keys in <code className="bg-surface px-1 rounded">backend/.env</code> to enable additional providers.
          </p>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-primary hover:underline"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            API Documentation
          </a>
        </div>
      </div>
    </div>
  );
};
