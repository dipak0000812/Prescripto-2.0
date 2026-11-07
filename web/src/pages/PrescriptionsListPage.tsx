import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listPrescriptionsApi, getPrescriptionApi } from '../api/prescriptions';
import { retryAnalysisApi } from '../api/analyses';
import { PrescriptionSummary } from '../types/api';
import { useAuth } from '../context/AuthContext';
import { PrescriptionImageModal } from '../components/PrescriptionImageModal';
import { DeleteConfirmModal } from '../components/DeleteConfirmModal';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import {
  FileText,
  UploadCloud,
  RefreshCw,
  Search,
  Filter,
  Eye,
  Trash2,
  Calendar,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  User,
  History,
  FileCheck,
  CheckCircle2,
  Clock,
  AlertTriangle,
} from 'lucide-react';

export const PrescriptionsListPage: React.FC = () => {
  const { session, hasRole } = useAuth();
  const navigate = useNavigate();

  const [items, setItems] = useState<PrescriptionSummary[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & search
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Modals state
  const [inspectImageId, setInspectImageId] = useState<string | null>(null);
  const [inspectImageUrl, setInspectImageUrl] = useState<string | null>(null);
  const [deleteDocId, setDeleteDocId] = useState<string | null>(null);

  // If patient somehow accesses, redirect immediately to their own patient portal
  useEffect(() => {
    if (session?.is_patient) {
      navigate('/patient-portal', { replace: true });
    }
  }, [session, navigate]);

  const fetchPrescriptions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listPrescriptionsApi(page, pageSize);
      setItems(data.items);
      setTotal(data.total);
    } catch (err: any) {
      setError(err?.message || 'Failed to load prescription documents.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPrescriptions();
  }, [page]);

  const handleOpenImageInspector = async (docId: string) => {
    try {
      const detail = await getPrescriptionApi(docId);
      setInspectImageId(docId);
      setInspectImageUrl(detail.image_url);
    } catch (err: any) {
      alert(`Could not fetch prescription scan: ${err?.message || 'Error'}`);
    }
  };

  const filteredItems = items.filter((item) => {
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      q === '' ||
      item.prescription_id.toLowerCase().includes(q) ||
      (item.patient_ref || '').toLowerCase().includes(q) ||
      (item.patient_name || '').toLowerCase().includes(q);

    const matchesStatus =
      statusFilter === 'ALL' || item.latest_analysis_status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  // Render plain human status badge
  const renderStatusBadge = (status?: string | null) => {
    if (!status) return <span className="text-stone-400 italic text-xs">No analysis</span>;

    switch (status) {
      case 'REVIEWED_COMPLETE':
        return (
          <Badge variant="success" dot>
            Doctor checked
          </Badge>
        );
      case 'COMPLETED':
        return (
          <Badge variant="brand" dot>
            Ready
          </Badge>
        );
      case 'REQUIRES_REVIEW':
        return (
          <Badge variant="warning" dot>
            Doctor checking
          </Badge>
        );
      case 'REVIEWED_ESCALATED':
        return (
          <Badge variant="danger" dot>
            Escalated
          </Badge>
        );
      case 'FAILED':
        return (
          <Badge variant="danger" dot>
            Scan error
          </Badge>
        );
      case 'PROCESSING':
      case 'QUEUED':
      default:
        return (
          <Badge variant="neutral" dot>
            Analyzing…
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-6 text-left animate-in fade-in duration-150">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-stone-200">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-brand" />
            Prescriptions ledger
          </h1>
          <p className="text-xs text-ink-muted mt-1">
            Browse and review all digitized patient prescription records, safety alerts, and physician determinations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchPrescriptions}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-brand' : ''}`} />}
            className="min-h-[40px]"
          >
            Refresh
          </Button>

          <Link to="/upload">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<UploadCloud className="w-4 h-4 text-white" />}
              className="min-h-[40px]"
            >
              Upload prescription
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white border border-stone-200 rounded-2xl p-4 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by patient name, ID (PAT-…), or record ID"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 text-xs bg-paper border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand focus:bg-white transition"
          />
        </div>

        {/* Status Dropdown */}
        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-stone-400 shrink-0" />
          <span className="text-xs font-semibold text-ink-muted shrink-0">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 text-xs bg-paper border border-stone-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand transition text-ink font-medium"
          >
            <option value="ALL">All statuses</option>
            <option value="REQUIRES_REVIEW">Doctor checking</option>
            <option value="COMPLETED">Ready</option>
            <option value="REVIEWED_COMPLETE">Doctor checked</option>
            <option value="REVIEWED_ESCALATED">Escalated</option>
            <option value="PROCESSING">Analyzing…</option>
            <option value="FAILED">Scan error</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      {/* Main Table / Data View */}
      {isLoading && items.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-2xs">
          <RefreshCw className="w-8 h-8 text-brand animate-spin mx-auto mb-3" />
          <div className="text-xs font-semibold text-ink-muted">Loading prescriptions…</div>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-2xs">
          <FileText className="w-12 h-12 text-stone-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-ink">No prescriptions found</h3>
          <p className="text-xs text-ink-muted mt-1 mb-6 max-w-sm mx-auto">
            {searchQuery || statusFilter !== 'ALL'
              ? 'No prescriptions matched the specified search criteria.'
              : 'No prescriptions have been uploaded yet. Upload a prescription image to start.'}
          </p>
          <Link to="/upload">
            <Button variant="primary" size="md" className="min-h-[48px]">
              Upload prescription
            </Button>
          </Link>
        </div>
      ) : (
        <div className="bg-white border border-stone-200 rounded-2xl shadow-2xs overflow-hidden">
          {/* Mobile Card View (< 768px) */}
          <div className="md:hidden divide-y divide-stone-100">
            {filteredItems.map((item) => (
              <div key={item.prescription_id} className="p-4 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-brand-soft text-brand flex items-center justify-center font-bold text-xs shrink-0">
                      <User className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-bold text-ink text-sm">
                        {item.patient_name || (item.patient_ref ? `Patient (${item.patient_ref})` : 'Walk-in Patient')}
                      </div>
                      {item.patient_ref && (
                        <Link
                          to={`/patients/${item.patient_ref}`}
                          className="font-mono text-xs text-brand hover:underline inline-flex items-center gap-1"
                        >
                          <span>{item.patient_ref}</span>
                          <History className="w-3 h-3" />
                        </Link>
                      )}
                    </div>
                  </div>
                  <div>{renderStatusBadge(item.latest_analysis_status)}</div>
                </div>

                <div className="flex items-center justify-between text-xs text-ink-muted">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-stone-400" />
                    {new Date(item.uploaded_at).toLocaleDateString()}
                  </span>
                  <span className="font-mono text-[11px] text-stone-400">
                    ID: {item.prescription_id.slice(0, 8)}…
                  </span>
                </div>

                <div className="flex items-center gap-2 pt-2 border-t border-stone-100">
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
                          alert('No analysis job found for this document.');
                        }
                      } catch (err: any) {
                        alert(err?.message || 'Failed to open document detail');
                      }
                    }}
                    className="flex-1 inline-flex items-center justify-center gap-1 px-3 py-2 bg-brand text-white rounded-xl text-xs font-semibold min-h-[44px] transition cursor-pointer"
                  >
                    <FileCheck className="w-4 h-4" />
                    <span>View report</span>
                  </button>

                  <button
                    onClick={() => handleOpenImageInspector(item.prescription_id)}
                    className="inline-flex items-center justify-center gap-1 px-3 py-2 bg-paper text-ink border border-stone-200 rounded-xl text-xs font-semibold min-h-[44px] transition cursor-pointer"
                  >
                    <Eye className="w-4 h-4 text-ink-muted" />
                    <span>Scan</span>
                  </button>

                  {item.latest_analysis_status === 'FAILED' && item.latest_analysis_id && (
                    <button
                      onClick={async () => {
                        try {
                          await retryAnalysisApi(item.latest_analysis_id!);
                          fetchPrescriptions();
                        } catch (err: any) {
                          alert(err?.message || 'Failed to retry scan');
                        }
                      }}
                      className="inline-flex items-center justify-center gap-1 px-3 py-2 bg-amber-50 text-amber-800 border border-amber-300 rounded-xl text-xs font-semibold min-h-[44px] transition cursor-pointer"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Retry</span>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Desktop Table View (>= 768px) */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-paper border-b border-stone-200 text-ink-muted font-semibold text-[11px]">
                <tr>
                  <th className="py-3.5 px-5">Patient</th>
                  <th className="py-3.5 px-4">Uploaded</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Record ID</th>
                  <th className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {filteredItems.map((item) => (
                  <tr key={item.prescription_id} className="hover:bg-paper/80 transition">
                    {/* Patient Column */}
                    <td className="py-4 px-5">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-brand-soft text-brand flex items-center justify-center font-bold text-xs shrink-0">
                          <User className="w-4 h-4 text-brand" />
                        </div>
                        <div>
                          <div className="font-bold text-ink text-sm">
                            {item.patient_name || (item.patient_ref ? `Patient (${item.patient_ref})` : 'Walk-in Patient')}
                          </div>
                          {item.patient_ref && (
                            <Link
                              to={`/patients/${item.patient_ref}`}
                              className="font-mono text-xs text-brand hover:underline inline-flex items-center gap-1 mt-0.5"
                              title="View Patient Record & History"
                            >
                              <span>{item.patient_ref}</span>
                              <History className="w-3 h-3 text-brand" />
                            </Link>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Upload Date */}
                    <td className="py-4 px-4 text-ink-muted">
                      <div className="flex items-center gap-1.5 text-xs">
                        <Calendar className="w-3.5 h-3.5 text-stone-400" />
                        <span>{new Date(item.uploaded_at).toLocaleString()}</span>
                      </div>
                    </td>

                    {/* Clinical Status */}
                    <td className="py-4 px-4">
                      {renderStatusBadge(item.latest_analysis_status)}
                    </td>

                    {/* Document UUID */}
                    <td className="py-4 px-4 font-mono text-stone-400 text-xs select-all">
                      <div className="truncate max-w-[140px]" title={item.prescription_id}>
                        {item.prescription_id}
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="py-4 px-5 text-right space-x-2 whitespace-nowrap">
                      {/* View document detail & findings */}
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
                              alert('No analysis job found for this document.');
                            }
                          } catch (err: any) {
                            alert(err?.message || 'Failed to open document detail');
                          }
                        }}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-brand-soft hover:bg-brand-soft/80 text-brand border border-brand/20 rounded-xl text-xs font-bold transition cursor-pointer min-h-[36px]"
                        title="View extracted medicines and safety report"
                      >
                        <FileCheck className="w-3.5 h-3.5 text-brand" />
                        <span>Report</span>
                      </button>

                      {/* Inspect image scan */}
                      <button
                        onClick={() => handleOpenImageInspector(item.prescription_id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-white hover:bg-paper text-ink border border-stone-300 rounded-xl text-xs font-semibold transition cursor-pointer min-h-[36px]"
                        title="Inspect original prescription scan"
                      >
                        <Eye className="w-3.5 h-3.5 text-ink-muted" />
                        <span>Scan</span>
                      </button>

                      {/* Quick retry for failed scans */}
                      {item.latest_analysis_status === 'FAILED' && item.latest_analysis_id && (
                        <button
                          onClick={async () => {
                            try {
                              await retryAnalysisApi(item.latest_analysis_id!);
                              fetchPrescriptions();
                            } catch (err: any) {
                              alert(err?.message || 'Failed to retry scan');
                            }
                          }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded-xl text-xs font-semibold transition cursor-pointer min-h-[36px]"
                          title="Retry failed prescription scan"
                        >
                          <RefreshCw className="w-3.5 h-3.5 text-amber-700" />
                          <span>Retry</span>
                        </button>
                      )}

                      {/* Deletion (Admins & Operators) */}
                      {hasRole('ADMIN', 'OPERATOR') && item.status !== 'DELETED' && (
                        <button
                          onClick={() => setDeleteDocId(item.prescription_id)}
                          className="inline-flex items-center p-2 text-stone-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition cursor-pointer"
                          title="Secure patient deletion request"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination controls */}
          <div className="px-5 py-3.5 bg-paper border-t border-stone-200 flex items-center justify-between text-xs text-ink-muted">
            <div>
              Page <span className="font-bold text-ink">{page}</span> of{' '}
              <span className="font-bold text-ink">{totalPages}</span> ({total} total records)
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
                className="text-xs"
              >
                Previous
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                className="text-xs"
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Image Inspector Modal */}
      {inspectImageId && (
        <PrescriptionImageModal
          prescriptionId={inspectImageId}
          initialImageUrl={inspectImageUrl}
          isOpen={true}
          onClose={() => {
            setInspectImageId(null);
            setInspectImageUrl(null);
          }}
        />
      )}

      {/* Deletion Confirmation Modal */}
      {deleteDocId && (
        <DeleteConfirmModal
          prescriptionId={deleteDocId}
          isOpen={true}
          onClose={() => setDeleteDocId(null)}
          onDeleted={() => {
            fetchPrescriptions();
          }}
        />
      )}
    </div>
  );
};

export default PrescriptionsListPage;
