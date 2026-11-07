import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getAnalyticsDashboardApi } from '../api/analytics';
import type { DateRangeParams } from '../api/analytics';
import {
  AnalyticsDashboardResponse,
  PrescriptionVolume,
  SafetyMetrics,
  DoctorWorkload,
  SystemHealthMetrics,
} from '../types/analytics';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { AlertBanner } from '../components/ui/AlertBanner';
import { Select } from '../components/ui/Select';
import { Input } from '../components/ui/Input';
import { useToast } from '../components/ui/Toast';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  ShieldCheck,
  AlertTriangle,
  Users,
  Clock,
  Server,
  Database,
  Download,
  RefreshCw,
  Calendar,
  ChevronLeft,
  ChevronRight,
  BarChart2,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { formatLocaleDate } from '../utils/dateUtils';

export const AnalyticsDashboardPage: React.FC = () => {
  const { session } = useAuth();
  const { showToast } = useToast();

  const [dashboardData, setDashboardData] = useState<AnalyticsDashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Date range state
  const [dateRange, setDateRange] = useState<DateRangeParams>({
    granularity: 'day',
  });
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Default to last 30 days
  useEffect(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(end.toISOString().split('T')[0]);
  }, []);

  const fetchDashboard = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: DateRangeParams = {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        granularity: dateRange.granularity,
      };
      const data = await getAnalyticsDashboardApi(params);
      setDashboardData(data);
    } catch (err: any) {
      const msg = err?.message || 'Failed to load analytics dashboard.';
      setError(msg);
      showToast({ type: 'error', title: 'Dashboard Error', message: msg });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [startDate, endDate, dateRange.granularity]);

  const handleDateChange = (field: 'start' | 'end', value: string) => {
    if (field === 'start') setStartDate(value);
    else setEndDate(value);
  };

  const handleGranularityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setDateRange((prev: DateRangeParams) => ({ ...prev, granularity: e.target.value as 'day' | 'week' | 'month' }));
  };

  const handleExport = async () => {
    if (!dashboardData) return;
    try {
      const csv = convertToCSV(dashboardData);
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `prescripto-analytics-${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      showToast({ type: 'success', title: 'Exported', message: 'Dashboard data downloaded as CSV' });
    } catch {
      showToast({ type: 'error', title: 'Export Failed', message: 'Could not generate CSV' });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-in fade-in duration-150">
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-2xs">
          <Activity className="w-8 h-8 text-brand animate-spin mx-auto mb-3" />
          <div className="text-xs font-semibold text-ink-muted">Loading analytics dashboard…</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6 animate-in fade-in duration-150">
        <AlertBanner type="error" title="Dashboard unavailable" badgeLabel="Error">
          {error}
          <Button variant="outline" size="sm" onClick={fetchDashboard} className="mt-3 min-h-[40px]">
            Try again
          </Button>
        </AlertBanner>
      </div>
    );
  }

  if (!dashboardData) return null;

  const { prescription_volume, safety_metrics, doctor_workload, system_health } = dashboardData;

  // Calculate summary stats
  const totalPrescriptions = prescription_volume.reduce((sum, d) => sum + d.count, 0);
  const totalCompleted = prescription_volume.reduce((sum, d) => sum + d.completed, 0);
  const totalPending = prescription_volume.reduce((sum, d) => sum + d.pending_review, 0);
  const completionRate = totalPrescriptions > 0 ? Math.round((totalCompleted / totalPrescriptions) * 100) : 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-150 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-stone-200">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight flex items-center gap-2.5">
            <BarChart2 className="w-6 h-6 text-brand" />
            Clinical Analytics Dashboard
          </h1>
          <p className="text-xs text-ink-muted mt-1">
            Prescription volume, safety screening metrics, clinician workload, and system health.
            Generated: {formatLocaleDate(dashboardData.generated_at, 'en')}
          </p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <Button variant="ghost" size="sm" onClick={fetchDashboard} disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-brand' : ''}`} />}
            className="min-h-[40px]">Refresh</Button>
          <Button variant="outline" size="sm" onClick={handleExport}
            leftIcon={<Download className="w-3.5 h-3.5 text-brand" />}
            className="min-h-[40px]">Export CSV</Button>
        </div>
      </div>

      {/* Date Range Controls */}
      <Card className="p-4 bg-white border-stone-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-stone-400 shrink-0" />
              <span className="text-xs font-semibold text-ink-muted">From:</span>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => handleDateChange('start', e.target.value)}
                className="w-36 text-xs min-h-[40px]"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-ink-muted">To:</span>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => handleDateChange('end', e.target.value)}
                className="w-36 text-xs min-h-[40px]"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-ink-muted">Granularity:</span>
              <Select
                value={dateRange.granularity}
                onChange={handleGranularityChange}
                options={[
                  { value: 'day', label: 'Daily' },
                  { value: 'week', label: 'Weekly' },
                  { value: 'month', label: 'Monthly' },
                ]}
                className="w-32 text-xs min-h-[40px]"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-5 bg-white border-stone-200 space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-ink-muted">
              <Activity className="w-4 h-4 text-brand" />
              <span>Total Prescriptions</span>
            </div>
            <div className="p-1.5 rounded-lg bg-brand-soft text-brand">
              <BarChart2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-ink">{totalPrescriptions}</div>
          <div className="text-xs text-ink-muted">
            {totalPrescriptions > 0 ? `+${totalPrescriptions - (totalPrescriptions - totalCompleted)} this period` : 'No data'}
          </div>
        </Card>

        <Card className="p-5 bg-white border-stone-200 space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-ink-muted">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Completed & Signed</span>
            </div>
            <div className="p-1.5 rounded-lg bg-emerald-100 text-emerald-600">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-ink">{totalCompleted}</div>
          <div className="text-xs text-ink-muted">
            {completionRate}% completion rate
          </div>
        </Card>

        <Card className="p-5 bg-white border-stone-200 space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-ink-muted">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Pending Review</span>
            </div>
            <div className="p-1.5 rounded-lg bg-amber-100 text-amber-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-ink">{totalPending}</div>
          <div className="text-xs text-ink-muted">
            Awaiting clinician sign-off
          </div>
        </Card>

        <Card className="p-5 bg-white border-stone-200 space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-ink-muted">
              <Server className="w-4 h-4 text-brand" />
              <span>System Uptime</span>
            </div>
            <div className="p-1.5 rounded-lg bg-brand-soft text-brand">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-ink">{system_health.api_uptime_pct.toFixed(1)}%</div>
          <div className="text-xs text-ink-muted">
            Avg response: {system_health.avg_response_time_ms.toFixed(0)}ms
          </div>
        </Card>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Prescription Volume Chart */}
        <Card className="lg:col-span-2 p-5 bg-white border-stone-200">
          <CardHeader>
            <CardTitle>Prescription Volume Trends</CardTitle>
            <CardDescription>Upload volume and review status over selected period</CardDescription>
          </CardHeader>
          <div className="h-64 relative">
            <PrescriptionVolumeChart data={prescription_volume} />
          </div>
        </Card>

        {/* Safety Metrics Summary */}
        <Card className="p-5 bg-white border-stone-200 space-y-4">
          <CardHeader>
            <CardTitle>Safety Screening Summary</CardTitle>
            <CardDescription>Automated finding classification across all analyses</CardDescription>
          </CardHeader>
          <SafetyMetricsChart data={safety_metrics} />
        </Card>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Doctor Workload */}
        <Card className="p-5 bg-white border-stone-200">
          <CardHeader>
            <CardTitle>Clinician Workload</CardTitle>
            <CardDescription>Assigned patients and review completion by doctor</CardDescription>
          </CardHeader>
          <DoctorWorkloadTable data={doctor_workload} />
        </Card>

        {/* System Health */}
        <Card className="p-5 bg-white border-stone-200 space-y-4">
          <CardHeader>
            <CardTitle>System Health</CardTitle>
            <CardDescription>Real-time infrastructure and API performance</CardDescription>
          </CardHeader>
          <SystemHealthPanel data={system_health} />
        </Card>
      </div>
    </div>
  );
};

// Simple chart component using inline SVG
const PrescriptionVolumeChart: React.FC<{ data: PrescriptionVolume[] }> = ({ data }) => {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-stone-400 text-xs">
        No volume data for selected period
      </div>
    );
  }

  const maxCount = Math.max(...data.map(d => d.count), 1);
  const width = '100%';
  const height = 256;
  const padding = { top: 20, right: 10, bottom: 40, left: 50 };
  const chartWidth = 100; // percentage
  const chartHeight = 100; // percentage

  return (
    <svg viewBox={`0 0 100 100`} className="w-full h-full" preserveAspectRatio="none">
      {/* Y-axis grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
        <line
          key={ratio}
          x1={10}
          y1={90 - ratio * 70}
          x2={95}
          y2={90 - ratio * 70}
          stroke="#E5E7EB"
          strokeWidth={0.5}
        />
      ))}
      {/* X-axis labels */}
      {data.map((d, i) => (
        <text
          key={d.date}
          x={10 + (i / Math.max(1, data.length - 1)) * 85}
          y={96}
          fontSize={4}
          fill="#6B7280"
          textAnchor="middle"
          dominantBaseline="hanging"
        >
          {new Date(d.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
        </text>
      ))}
      {/* Volume bars */}
      <g>
        {data.map((d, i) => {
          const barHeight = (d.count / maxCount) * 70;
          const x = 10 + (i / Math.max(1, data.length - 1)) * 85 - 2;
          const y = 90 - barHeight;
          return (
            <rect
              key={d.date}
              x={x}
              y={y}
              width={4}
              height={barHeight}
              fill="#0F5147"
              rx={0.5}
            />
          );
        })}
      </g>
      {/* Pending review overlay */}
      <g>
        {data.map((d, i) => {
          if (d.pending_review === 0) return null;
          const pendingRatio = Math.min(d.pending_review / Math.max(d.count, 1), 1);
          const barHeight = (d.count / maxCount) * 70;
          const pendingHeight = barHeight * pendingRatio;
          const x = 10 + (i / Math.max(1, data.length - 1)) * 85 - 2;
          const y = 90 - pendingHeight;
          return (
            <rect
              key={d.date + '-pending'}
              x={x}
              y={y}
              width={4}
              height={pendingHeight}
              fill="#FEF3C7"
              rx={0.5}
            />
          );
        })}
      </g>
    </svg>
  );
};

const SafetyMetricsChart: React.FC<{ data: SafetyMetrics }> = ({ data }) => {
  const statuses = [
    { key: 'confirmed_by_source', label: 'Confirmed', color: '#047857', bg: '#ECFDF5', count: data.confirmed_by_source },
    { key: 'potential', label: 'Potential', color: '#B45309', bg: '#FEF3C7', count: data.potential },
    { key: 'requires_review', label: 'Requires Review', color: '#BE123C', bg: '#FFE4E6', count: data.requires_review },
    { key: 'insufficient_evidence', label: 'Insufficient Evidence', color: '#6B7280', bg: '#F3F4F6', count: data.insufficient_evidence },
    { key: 'not_evaluated', label: 'Not Evaluated', color: '#9CA3AF', bg: '#F9FAFB', count: data.not_evaluated },
  ].filter(s => s.count > 0);

  const total = statuses.reduce((sum, s) => sum + s.count, 0);

  if (total === 0) {
    return (
      <div className="text-center py-8 text-stone-400 text-xs">
        No safety findings in selected period
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {statuses.map((s) => (
        <div key={s.key} className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-stone-700 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded" style={{ backgroundColor: s.color }} />
              {s.label}
            </span>
            <span className="font-bold text-stone-900">
              {s.count} ({(s.count / total * 100).toFixed(1)}%)
            </span>
          </div>
          <div className="h-2 bg-stone-200 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${(s.count / total) * 100}%`, backgroundColor: s.color }}
            />
          </div>
        </div>
      ))}
      <div className="pt-2 border-t border-stone-100 text-xs text-stone-500">
        Total findings: <span className="font-bold text-stone-900">{data.total_findings}</span>
        | Top check: <span className="font-medium text-brand">{data.top_check_types[0]?.check_type || 'N/A'}</span>
      </div>
    </div>
  );
};

const DoctorWorkloadTable: React.FC<{ data: DoctorWorkload[] }> = ({ data }) => {
  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-stone-400 text-xs">
        No clinician workload data
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead className="bg-paper border-b border-stone-200 text-ink-muted font-semibold text-[10px]">
          <tr>
            <th className="py-2 px-3 text-left">Clinician</th>
            <th className="py-2 px-3 text-right">Patients</th>
            <th className="py-2 px-3 text-right">Reviews</th>
            <th className="py-2 px-3 text-right">Avg Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-stone-100">
          {data.map((d) => (
            <tr key={d.doctor_id} className="hover:bg-paper/50">
              <td className="py-2 px-3 font-medium text-ink truncate max-w-[120px]">
                {d.doctor_name}
              </td>
              <td className="py-2 px-3 text-right text-stone-600">{d.assigned_patients}</td>
              <td className="py-2 px-3 text-right">
                <Badge variant="success" size="sm">{d.completed_reviews}</Badge>
              </td>
              <td className="py-2 px-3 text-right text-stone-600 font-mono">
                {d.avg_review_time_hours.toFixed(1)}h
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const SystemHealthPanel: React.FC<{ data: SystemHealthMetrics }> = ({ data }) => {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <MetricCard
          label="API Uptime"
          value={`${data.api_uptime_pct.toFixed(1)}%`}
          icon={<Server className="w-5 h-5" />}
          color="brand"
        />
        <MetricCard
          label="Avg Response"
          value={`${data.avg_response_time_ms.toFixed(0)}ms`}
          icon={<Clock className="w-5 h-5" />}
          color="emerald"
        />
        <MetricCard
          label="Error Rate"
          value={`${data.error_rate_pct.toFixed(1)}%`}
          icon={<AlertTriangle className="w-5 h-5" />}
          color="amber"
        />
        <MetricCard
          label="Queue Depth"
          value={data.queue_depth.toString()}
          icon={<Database className="w-5 h-5" />}
          color="brand"
        />
      </div>
      <div className="p-3 bg-paper border border-stone-200 rounded-xl text-[11px] text-stone-600">
        <div className="font-semibold text-stone-900 mb-1">Active Workers: {data.active_workers}</div>
        <div>Storage Used: {data.storage_used_gb.toFixed(2)} GB</div>
      </div>
    </div>
  );
};

const MetricCard: React.FC<{
  label: string;
  value: string;
  icon: React.ReactNode;
  color: 'brand' | 'emerald' | 'amber' | 'rose';
}> = ({ label, value, icon, color }) => {
  const colors = {
    brand: { bg: '#E6F0EE', text: '#0F5147', icon: '#0F5147' },
    emerald: { bg: '#ECFDF5', text: '#047857', icon: '#047857' },
    amber: { bg: '#FEF3C7', text: '#B45309', icon: '#B45309' },
    rose: { bg: '#FFE4E6', text: '#BE123C', icon: '#BE123C' },
  };
  const c = colors[color];

  return (
    <div className="p-4 bg-white border border-stone-200 rounded-xl space-y-1">
      <div className="flex items-center justify-between">
        <div style={{ color: c.icon }}>{icon}</div>
        <span className="text-[10px] font-semibold text-stone-500">{label}</span>
      </div>
      <div className="text-2xl font-extrabold" style={{ color: c.text }}>{value}</div>
    </div>
  );
};

const convertToCSV = (data: AnalyticsDashboardResponse): string => {
  const rows: string[] = [];
  rows.push('Metric,Value');
  rows.push(`Total Prescriptions,${data.prescription_volume.reduce((s, d) => s + d.count, 0)}`);
  rows.push(`Completed,${data.prescription_volume.reduce((s, d) => s + d.completed, 0)}`);
  rows.push(`Pending Review,${data.prescription_volume.reduce((s, d) => s + d.pending_review, 0)}`);
  rows.push(`Safety Findings,${data.safety_metrics.total_findings}`);
  rows.push(`Confirmed,${data.safety_metrics.confirmed_by_source}`);
  rows.push(`Potential,${data.safety_metrics.potential}`);
  rows.push(`Requires Review,${data.safety_metrics.requires_review}`);
  rows.push(`API Uptime,${data.system_health.api_uptime_pct}%`);
  rows.push(`Avg Response (ms),${data.system_health.avg_response_time_ms}`);
  rows.push(`Error Rate,${data.system_health.error_rate_pct}%`);
  rows.push(`Queue Depth,${data.system_health.queue_depth}`);
  return rows.join('\n');
};

export default AnalyticsDashboardPage;