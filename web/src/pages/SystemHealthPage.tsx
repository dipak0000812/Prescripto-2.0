import React, { useState, useEffect } from 'react';
import { getHealthApi } from '../api/health';
import { HealthStatus } from '../types/api';
import {
  Activity,
  Database,
  HardDrive,
  Cpu,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

export const SystemHealthPage: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastCheckTime, setLastCheckTime] = useState<Date | null>(null);

  const fetchHealth = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getHealthApi();
      setHealth(data);
      setLastCheckTime(new Date());
    } catch (err: any) {
      setError(err?.message || 'Failed to query system health probe.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const renderProbeStatus = (status: string | undefined) => {
    if (!status) return null;
    if (status === 'ok') {
      return (
        <Badge variant="success" dot>
          Operational
        </Badge>
      );
    }
    if (status === 'degraded' || status === 'stale') {
      return (
        <Badge variant="warning" dot>
          {status}
        </Badge>
      );
    }
    return (
      <Badge variant="danger" dot>
        Down ({status})
      </Badge>
    );
  };

  return (
    <div className="space-y-6 text-left animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-stone-200">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-brand" />
            System health & diagnostics
          </h1>
          <p className="text-xs text-ink-muted mt-1">
            Current probe results for the database, image storage, and background worker queues.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchHealth}
          disabled={isLoading}
          leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-brand' : ''}`} />}
          className="min-h-[40px]"
        >
          Run check
        </Button>
      </div>

      {error && (
        <div role="alert" className="p-3.5 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      {/* Probes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5">
        {/* Database Probe */}
        <div className="bg-white border border-stone-200 rounded-2xl p-5 shadow-2xs space-y-3">
          <div className="flex items-start justify-between">
            <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand border border-brand/20 flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            {renderProbeStatus(health?.database)}
          </div>
          <div>
            <h3 className="text-sm font-bold text-ink">Database</h3>
            <p className="text-xs text-ink-muted mt-0.5 leading-relaxed">
              Reports whether the application can connect to and query the primary database.
            </p>
          </div>
        </div>

        {/* Object Storage Probe */}
        <div className="bg-white border border-stone-200 rounded-2xl p-5 shadow-2xs space-y-3">
          <div className="flex items-start justify-between">
            <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand border border-brand/20 flex items-center justify-center">
              <HardDrive className="w-5 h-5" />
            </div>
            {renderProbeStatus(health?.object_storage)}
          </div>
          <div>
            <h3 className="text-sm font-bold text-ink">Prescription storage</h3>
            <p className="text-xs text-ink-muted mt-0.5 leading-relaxed">
              Reports whether prescription image storage is accessible.
            </p>
          </div>
        </div>

        {/* Worker Engine Probe */}
        <div className="bg-white border border-stone-200 rounded-2xl p-5 shadow-2xs space-y-3">
          <div className="flex items-start justify-between">
            <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand border border-brand/20 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            {renderProbeStatus(health?.worker_heartbeat)}
          </div>
          <div>
            <h3 className="text-sm font-bold text-ink">Worker heartbeat</h3>
            <p className="text-xs text-ink-muted mt-0.5 leading-relaxed">
              Reports the latest background queue processing worker status.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-stone-200 bg-white p-5 text-xs text-ink-muted shadow-2xs space-y-1.5">
        <p className="font-semibold text-ink">Operational scope notice</p>
        <p className="leading-relaxed">
          These probes report infrastructure service availability only. They do not assess prescription extraction accuracy, clinical safety determinations, or patient record retention.
        </p>
        <p className="pt-1 text-[11px] font-mono text-stone-400">
          {lastCheckTime ? `Last successful probe: ${lastCheckTime.toLocaleTimeString()}` : 'No successful probe recorded.'}
        </p>
      </div>
    </div>
  );
};

export default SystemHealthPage;
