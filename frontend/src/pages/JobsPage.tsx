import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { JobInfo } from '../types/api';
import { Server, RefreshCw, XCircle } from 'lucide-react';

export const JobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<JobInfo[]>([]);

  const loadJobs = () => {
    api.jobs.list().then(setJobs).catch(() => {});
  };

  useEffect(() => {
    loadJobs();
  }, []);

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 bg-background">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-text-primary">Background Jobs & Tasks</h1>
          <p className="text-xs text-text-secondary">Monitor async Celery & FastAPI background processes</p>
        </div>
        <button onClick={loadJobs} className="px-3 py-1.5 rounded-lg bg-surface border border-border text-xs text-text-secondary hover:text-text-primary flex items-center gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      <div className="glass-panel p-6 rounded-2xl border border-border space-y-4">
        {jobs.length === 0 ? (
          <div className="p-12 text-center text-xs text-text-muted space-y-2">
            <Server className="w-8 h-8 text-text-muted mx-auto" />
            <p>No background jobs running</p>
          </div>
        ) : (
          <div className="space-y-3">
            {jobs.map((job) => (
              <div key={job.id} className="p-4 rounded-xl bg-surface/60 border border-border flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-text-primary">{job.name}</div>
                  <div className="text-[11px] text-text-muted">Type: {job.job_type} | ID: {job.id}</div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-2.5 py-1 rounded-full text-[10px] bg-primary-muted text-primary font-bold">
                    {job.status}
                  </span>
                  <button onClick={() => api.jobs.cancel(job.id).then(loadJobs)} className="p-1 hover:bg-red-500/20 text-red-400 rounded">
                    <XCircle className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
