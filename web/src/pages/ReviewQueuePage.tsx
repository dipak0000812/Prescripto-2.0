import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listPrescriptionsApi, getPrescriptionApi } from '../api/prescriptions';
import { PrescriptionSummary } from '../types/api';
import { AnalysisStatusBadge } from '../components/Badges';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
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
} from 'lucide-react';

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
    <div className="space-y-6 text-left animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-stone-200">
        <div>
          <h1 className="text-2xl font-extrabold text-[#1C252E] tracking-tight flex items-center gap-2.5">
            <CheckSquare className="w-6 h-6 text-[#0F5147]" />
            Clinical Review Queue
            <span className="text-xs font-semibold bg-[#FEF3C7] text-[#78350F] px-2.5 py-0.5 rounded-full border border-[#FCD34D]">
              {queueItems.length} Awaiting Review
            </span>
          </h1>
          <p className="text-xs text-stone-500 mt-1">
            Prescriptions flagged with safety alerts, ambiguous text, or drug contraindications requiring physician verification and sign-off.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchQueue}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-[#0F5147]' : ''}`} />}
            className="min-h-[40px]"
          >
            Refresh Queue
          </Button>
        </div>
      </div>

      {/* Reviewer guidance banner */}
      <div className="bg-[#E6F0EE]/60 border border-[#9DC1BB] rounded-2xl p-4 text-xs text-[#0F5147] flex items-start gap-3 shadow-2xs">
        <ShieldCheck className="w-5 h-5 text-[#0F5147] shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-[#0F5147] uppercase text-[11px] tracking-wider">
            Licensed Medical Professional Sign-Off Protocol
          </div>
          <p className="leading-relaxed text-[#0F5147]">
            Active Clinician: <strong className="font-bold text-[#1C252E]">{session?.username}</strong> ({session?.role}). Inspect safety findings, verify medication dosages, and submit clinical sign-off to finalize reports for dispensing.
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          placeholder="Filter queue by Patient Name, Patient ID (PAT-...), or Document UUID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] shadow-2xs transition"
        />
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3.5 bg-[#FFE4E6] border border-[#FDA4AF] rounded-2xl text-xs text-[#881337] flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-[#BE123C] shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      {/* Queue Content */}
      {isLoading ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-xs">
          <RefreshCw className="w-8 h-8 text-[#0F5147] animate-spin mx-auto mb-3" />
          <div className="text-xs font-semibold text-stone-700">Checking review queue...</div>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-xs">
          <CheckCircle2 className="w-12 h-12 text-[#047857] mx-auto mb-3" />
          <h3 className="text-base font-bold text-[#1C252E]">
            {searchQuery ? 'No Matching Prescriptions Found' : 'Clinical Queue is Clear'}
          </h3>
          <p className="text-xs text-stone-500 mt-1 mb-4 max-w-md mx-auto">
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
              Clear Filter
            </Button>
          ) : (
            <Link to="/prescriptions">
              <Button variant="outline" size="sm" className="min-h-[40px]">
                View All Prescriptions
              </Button>
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredItems.map((item) => (
            <div
              key={item.prescription_id}
              className="bg-white border border-stone-200 rounded-2xl p-5 shadow-xs hover:border-stone-300 transition space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="w-10 h-10 rounded-xl bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB] flex items-center justify-center font-bold text-sm shrink-0">
                      <User className="w-5 h-5 text-[#0F5147]" />
                    </div>
                    <div>
                      <div className="font-bold text-sm text-[#1C252E]">
                        {item.patient_name || 'Unassigned / Walk-in Patient'}
                      </div>
                      <div className="text-[11px] text-stone-500 flex items-center gap-1.5 mt-0.5">
                        {item.patient_ref ? (
                          <span className="font-mono bg-stone-100 px-1.5 py-0.5 rounded text-stone-700 border border-stone-200">
                            {item.patient_ref}
                          </span>
                        ) : (
                          <span className="text-stone-400 italic">No Patient ID</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {item.latest_analysis_status && (
                    <AnalysisStatusBadge status={item.latest_analysis_status} />
                  )}
                </div>

                <div className="p-3 bg-[#FAF9F6] border border-stone-200 rounded-xl space-y-1.5 text-xs text-stone-600">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-stone-500">Document UUID:</span>
                    <span className="font-mono text-stone-700 select-all truncate max-w-[180px]">
                      {item.prescription_id}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-stone-500 flex items-center gap-1">
                      <Calendar className="w-3 h-3 text-stone-400" />
                      Uploaded:
                    </span>
                    <span className="text-stone-700 font-medium">
                      {new Date(item.uploaded_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-stone-100 flex items-center justify-between gap-2">
                {item.patient_ref ? (
                  <Link
                    to={`/patients/${item.patient_ref}`}
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-stone-600 hover:text-[#0F5147] hover:bg-[#E6F0EE] rounded-xl transition"
                    title="View complete patient history"
                  >
                    <History className="w-3.5 h-3.5" />
                    <span>Patient History</span>
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
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-[#0F5147] hover:bg-[#0A3831] text-white text-xs font-semibold rounded-xl shadow-2xs transition"
                >
                  <FileCheck className="w-3.5 h-3.5" />
                  <span>Review & Sign Off</span>
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
