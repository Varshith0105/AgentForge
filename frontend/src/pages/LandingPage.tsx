import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Bot, Code2, Network, ShieldCheck, Terminal, ArrowRight, Play } from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col font-sans selection:bg-primary/30">
      {/* Landing Header */}
      <header className="h-16 px-8 border-b border-border/50 flex items-center justify-between glass-panel sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent-purple flex items-center justify-center shadow-glow">
            <Zap className="w-5 h-5 text-black font-bold" />
          </div>
          <span className="font-extrabold text-xl bg-gradient-to-r from-text-primary via-primary to-accent-purple bg-clip-text text-transparent">
            AgentForge
          </span>
        </div>

        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/login')} className="px-4 py-2 text-xs font-semibold text-text-secondary hover:text-text-primary transition">
            Sign In
          </button>
          <button
            onClick={() => navigate('/register')}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-primary to-accent-purple text-black text-xs font-bold hover:shadow-glow transition flex items-center gap-1.5"
          >
            <span>Get Started Free</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-24 px-6 max-w-6xl mx-auto text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary-muted border border-primary/30 text-xs font-semibold text-primary">
          <Zap className="w-3.5 h-3.5" />
          <span>Next-Gen Autonomous AI Engineering Platform</span>
        </div>

        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight leading-tight">
          Your Autonomous <br />
          <span className="bg-gradient-to-r from-primary via-accent-purple to-accent-pink bg-clip-text text-transparent">
            Software Engineering
          </span>{' '}
          Co-Pilot
        </h1>

        <p className="text-base md:text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          AgentForge automates repository scanning, bug detection, test generation, security reviews, and architectural optimization using collaborating AI agents.
        </p>

        <div className="flex items-center justify-center gap-4 pt-4">
          <button
            onClick={() => navigate('/register')}
            className="px-6 py-3.5 rounded-xl bg-primary text-black font-bold text-sm hover:bg-primary-hover shadow-glow transition flex items-center gap-2"
          >
            <span>Launch Workspace</span>
            <Play className="w-4 h-4 fill-current" />
          </button>
          <button
            onClick={() => navigate('/app')}
            className="px-6 py-3.5 rounded-xl glass-card text-text-primary font-semibold text-sm hover:bg-surface-hover transition border border-border"
          >
            Open Workspace
          </button>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-16 px-6 max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            icon: Bot,
            title: 'Collaborating Multi-Agent Architecture',
            desc: 'Specialized agents for planning, security, testing, architecture, and bug resolution working in unison.',
          },
          {
            icon: Network,
            title: 'Deep Knowledge Engine',
            desc: 'AST graph parsing and vector memory index code dependencies and semantic structures in real time.',
          },
          {
            icon: Terminal,
            title: 'Execution & Tool Engine',
            desc: 'Workspace-scoped repository tools, with terminal execution disabled by default.',
          },
        ].map((feat, idx) => {
          const Icon = feat.icon;
          return (
            <div key={idx} className="glass-card p-6 rounded-2xl border border-border space-y-3">
              <div className="w-10 h-10 rounded-xl bg-primary-muted border border-primary/30 flex items-center justify-center text-primary">
                <Icon className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-text-primary">{feat.title}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">{feat.desc}</p>
            </div>
          );
        })}
      </section>

      {/* Footer */}
      <footer className="mt-auto py-6 text-center text-xs text-text-muted border-t border-border/50">
        AgentForge &copy; 2026. Local-first AI software engineering workspace.
      </footer>
    </div>
  );
};
