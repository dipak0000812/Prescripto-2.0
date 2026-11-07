import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listPrescriptionsApi, getPrescriptionApi } from '../api/prescriptions';
import { PrescriptionSummary } from '../types/api';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import {
  CheckSquare,
  RefreshCw,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  User,
  Search,
  History,
  FileCheck,
  Clock,
  AlertTriangle,
} from 'lucide-react';

function getWaitTimeText(isoString: string): string {
  try {
    const uploaded = new Date(isoString).getTime();
    const now = Date.now();
    const diffMins = Math.max(1, Math.round((now - uploaded) / (1000 * 60)));

    if (diffMins < 60) return `Waiting ${diffMins}m`;
    const diffHours = Math.round(diffMins / 60);
    if (diffHours < 24) return `Waiting ${diffHours}h`;
    const diffDays = Math.round(diffHours / 24);
    return `Waiting ${diffDays}d`;
  } catch {
    return 'Pending review';
  }
}

export const ReviewQueuePage: React.FC = () => {
  const { session } = useAuth();
  const navigate = useNavigate();

  const [queueItems, setQueueItems] = useState<PrescriptionSummary[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueue = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listPrescriptionsApi(1, 100);
      const needingReview = data.items.filter(
        (item) =>
          item.latest_analysis_status === 'REQUIRES_REVIEW' ||
          item.latest_analysis_status === 'REVIEWING'
      );
      setQueueItems(needingReview);
    } catch (err: any) {
      setError(err?.message || 'Failed to load review queue.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const filteredItems = queueItems.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const pid = item.prescription_id.toLowerCase();
    const pref = (item.patient_ref || '').toLowerCase();
    const pname = (item.patient_name || '').toLowerCase();
    return pid.includes(q) || pref.includes(q) || pname.includes(q);
  });

  return (
    <div className="space-y-6 text-left animate-in fade-in duration-150 max-w-full overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-stone-200">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight flex items-center gap-2.5">
            <CheckSquare className="w-6 h-6 text-brand" />
            Clinical review queue
            <Badge variant="warning" dot>
              {queueItems.length} awaiting review
            </Badge>
          </h1>
          <p className="text-xs text-ink-muted mt-1">
            Prescriptions flagged with safety alerts, ambiguous text, or drug contraindications requiring physician verification and sign-off.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchQueue}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-brand' : ''}`} />}
            className="min-h-[40px]"
          >
            Refresh queue
          </Button>
        </div>
      </div>

      {/* Reviewer guidance banner */}
      <div className="bg-brand-soft/70 border border-brand/20 rounded-2xl p-4 text-xs text-brand-dark flex items-start gap-3 shadow-2xs">
        <ShieldCheck className="w-5 h-5 text-brand shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-brand uppercase text-[11px] tracking-wider">
            Licensed clinician sign-off protocol
          </div>
          <p className="leading-relaxed text-ink-muted">
            Signed in as <strong className="font-bold text-ink">{session?.username}</strong> ({session?.role}). Inspect safety findings, verify medication dosages, and sign off to finalize reports for patient dispensing.
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          placeholder="Filter queue by patient name, ID (PAT-…), or record ID"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 text-xs bg-paper border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand focus:bg-white transition"
        />
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      {/* Queue Content */}
      {isLoading ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-2xs">
          <RefreshCw className="w-8 h-8 text-brand animate-spin mx-auto mb-3" />
          <div className="text-xs font-semibold text-ink-muted">Checking review queue…</div>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-2xs">
          <CheckCircle2 className="w-12 h-12 text-brand mx-auto mb-3" />
          <h3 className="text-base font-bold text-ink">
            {searchQuery ? 'No matching prescriptions found' : 'Review queue is clear'}
          </h3>
          <p className="text-xs text-ink-muted mt-1 mb-4 max-w-md mx-auto leading-relaxed">
            {searchQuery
              ? `No prescriptions in the queue matched "${searchQuery}". Clear your search query to see all items.`
              : 'All prescriptions have been evaluated and signed off. No items are currently awaiting doctor determination.'}
          </p>
          {searchQuery ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSearchQuery('')}
              className="min-h-[40px]"
            >
              Clear filter
            </Button>
          ) : (
            <Link to="/prescriptions">
              <Button variant="outline" size="sm" className="min-h-[40px]">
                View all prescriptions
              </Button>
            </Link>
          )}
        </div>
      ) : (
        /* Responsive Grid: min-w-0 on items prevents overflow on 13" laptop screens */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 w-full">
          {filteredItems.map((item) => (
            <div
              key={item.prescription_id}
              className="min-w-0 w-full bg-white border border-stone-200 rounded-2xl p-5 shadow-2xs hover:border-stone-300 transition space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand border border-brand/20 flex items-center justify-center font-bold text-sm shrink-0">
                      <User className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="font-bold text-sm text-ink truncate">
                        {item.patient_name || (item.patient_ref ? `Patient (${item.patient_ref})` : 'Walk-in Patient')}
                      </div>
                      <div className="text-[11px] text-ink-muted flex items-center gap-1.5 mt-0.5">
                        {item.patient_ref ? (
                          <span className="font-mono bg-stone-100 px-1.5 py-0.5 rounded text-ink border border-stone-200">
                            {item.patient_ref}
                          </span>
                        ) : (
                          <span className="text-stone-400 italic">No Patient ID</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="shrink-0 flex flex-col items-end gap-1">
                    <Badge variant="warning" dot>
                      Needs review
                    </Badge>
                    <span className="text-[10px] text-stone-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {getWaitTimeText(item.uploaded_at)}
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-paper border border-stone-200 rounded-xl space-y-1.5 text-xs text-ink-muted min-w-0">
                  <div className="flex items-center justify-between text-[11px] gap-2 min-w-0">
                    <span className="text-stone-500 shrink-0">Record ID:</span>
                    <span className="font-mono text-ink select-all truncate">
                      {item.prescription_id}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] gap-2 min-w-0">
                    <span className="text-stone-500 flex items-center gap-1 shrink-0">
                      <Calendar className="w-3 h-3 text-stone-400" />
                      Uploaded:
                    </span>
                    <span className="text-ink truncate">
                      {new Date(item.uploaded_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-stone-100 flex items-center justify-between gap-2 min-w-0">
                {item.patient_ref ? (
                  <Link
                    to={`/patients/${item.patient_ref}`}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-ink-muted hover:text-brand hover:bg-brand-soft rounded-xl transition shrink-0"
                    title="View complete patient history"
                  >
                    <History className="w-3.5 h-3.5" />
                    <span>Patient history</span>
                  </Link>
                ) : (
                  <div />
                )}

                <button
                  onClick={async () => {
                    if (item.latest_analysis_id) {
                      navigate(`/analyses/${item.latest_analysis_id}`);
                      return;
                    }
                    try {
                      const detail = await getPrescriptionApi(item.prescription_id);
                      if (detail.analyses && detail.analyses.length > 0) {
                        navigate(`/analyses/${detail.analyses[0].analysis_id}`);
                      } else {
                        alert('No analysis found for this prescription.');
                      }
                    } catch (err: any) {
                      alert(err?.message || 'Failed to open analysis.');
                    }
                  }}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-brand hover:bg-brand-dark text-white text-xs font-semibold rounded-xl shadow-2xs transition cursor-pointer min-h-[40px] shrink-0"
                >
                  <FileCheck className="w-3.5 h-3.5" />
                  <span>Review & sign off</span>
                  <ExternalLink className="w-3.5 h-3.5 opacity-70" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReviewQueuePage;
