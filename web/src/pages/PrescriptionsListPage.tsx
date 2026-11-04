import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listPrescriptionsApi, getPrescriptionApi } from '../api/prescriptions';
import { PrescriptionSummary } from '../types/api';
import { useAuth } from '../context/AuthContext';
import { AnalysisStatusBadge } from '../components/Badges';
import { PrescriptionImageModal } from '../components/PrescriptionImageModal';
import { DeleteConfirmModal } from '../components/DeleteConfirmModal';
import { Button } from '../components/ui/Button';
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

  return (
    <div className="space-y-6 text-left animate-in fade-in duration-150">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-stone-200">
        <div>
          <h1 className="text-2xl font-extrabold text-[#1C252E] tracking-tight flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-[#0F5147]" />
            Prescriptions Ledger
          </h1>
          <p className="text-xs text-stone-500 mt-1">
            Browse and review all digitized patient prescription records, safety alerts, and physician determinations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchPrescriptions}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-[#0F5147]' : ''}`} />}
            className="min-h-[40px]"
          >
            Refresh
          </Button>

          <Link to="/upload">
            <Button
              variant="primary"
              size="sm"
              leftIcon={<UploadCloud className="w-4 h-4 text-white" />}
              className="min-h-[40px] bg-[#0F5147] hover:bg-[#0A3831]"
            >
              Upload Prescription
            </Button>
          </Link>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white border border-stone-200 rounded-2xl p-4 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by Patient Name, ID (PAT-...), or UUID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition"
          />
        </div>

        {/* Status Dropdown */}
        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-stone-400 shrink-0" />
          <span className="text-xs font-semibold text-stone-600 shrink-0">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition text-stone-700 font-medium"
          >
            <option value="ALL">All Statuses</option>
            <option value="REQUIRES_REVIEW">Doctor Review Needed</option>
            <option value="COMPLETED">Extraction complete</option>
            <option value="REVIEWED_COMPLETE">Clinically Approved</option>
            <option value="REVIEWED_ESCALATED">Escalated</option>
            <option value="PROCESSING">Analyzing...</option>
            <option value="QUEUED">Queued</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3.5 bg-[#FFE4E6] border border-[#FDA4AF] rounded-xl text-xs text-[#881337] flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-[#BE123C] shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      {/* Main Table / Data View */}
      {isLoading && items.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-xs">
          <RefreshCw className="w-8 h-8 text-[#0F5147] animate-spin mx-auto mb-3" />
          <div className="text-xs font-semibold text-stone-700">Loading prescriptions...</div>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-xs">
          <FileText className="w-12 h-12 text-stone-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-[#1C252E]">No Prescriptions Found</h3>
          <p className="text-xs text-stone-500 mt-1 mb-6 max-w-sm mx-auto">
            {searchQuery || statusFilter !== 'ALL'
              ? 'No prescriptions matched the specified search criteria.'
              : 'No prescriptions have been uploaded yet. Upload a prescription image to start.'}
          </p>
          <Link to="/upload">
            <Button variant="primary" size="md" className="min-h-[48px]">
              Upload First Prescription
            </Button>
          </Link>
        </div>
      ) : (
        <div className="bg-white border border-stone-200 rounded-2xl shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#FAF9F6] border-b border-stone-200 text-stone-600 font-bold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3.5 px-4">Patient</th>
                  <th className="py-3.5 px-4">Prescription Document</th>
                  <th className="py-3.5 px-4">Uploaded</th>
                  <th className="py-3.5 px-4">Clinical Safety Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {filteredItems.map((item) => (
                  <tr key={item.prescription_id} className="hover:bg-[#FAF9F6]/80 transition">
                    {/* Patient Column */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB] flex items-center justify-center font-bold text-xs shrink-0">
                          <User className="w-4 h-4 text-[#0F5147]" />
                        </div>
                        <div>
                          <div className="font-bold text-[#1C252E] text-xs">
                            {item.patient_name || 'Walk-in Patient'}
                          </div>
                          {item.patient_ref && (
                            <Link
                              to={`/patients/${item.patient_ref}`}
                              className="font-mono text-[11px] text-[#0F5147] hover:underline inline-flex items-center gap-1 mt-0.5"
                              title="View Patient Record & History"
                            >
                              <span>{item.patient_ref}</span>
                              <History className="w-3 h-3 text-[#0F5147]" />
                            </Link>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Document UUID */}
                    <td className="py-3.5 px-4 font-mono text-stone-500 text-[11px] select-all">
                      <div className="truncate max-w-[180px]" title={item.prescription_id}>
                        {item.prescription_id}
                      </div>
                    </td>

                    {/* Upload Date */}
                    <td className="py-3.5 px-4 text-stone-600">
                      <div className="flex items-center gap-1.5 text-xs">
                        <Calendar className="w-3.5 h-3.5 text-stone-400" />
                        <span>{new Date(item.uploaded_at).toLocaleString()}</span>
                      </div>
                    </td>

                    {/* Clinical Status */}
                    <td className="py-3.5 px-4">
                      {item.latest_analysis_status ? (
                        <AnalysisStatusBadge status={item.latest_analysis_status} />
                      ) : (
                        <span className="text-stone-400 italic">No analysis</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right space-x-1.5 whitespace-nowrap">
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
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#E6F0EE] hover:bg-[#D5E7E4] text-[#0F5147] border border-[#9DC1BB] rounded-lg text-xs font-bold transition cursor-pointer"
                        title="View extracted medicines and safety report"
                      >
                        <FileCheck className="w-3.5 h-3.5 text-[#0F5147]" />
                        <span>Report</span>
                      </button>

                      {/* Inspect image scan */}
                      <button
                        onClick={() => handleOpenImageInspector(item.prescription_id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-white hover:bg-[#FAF9F6] text-stone-700 border border-stone-300 rounded-lg text-xs font-semibold transition cursor-pointer"
                        title="Inspect original prescription scan"
                      >
                        <Eye className="w-3.5 h-3.5 text-stone-500" />
                        <span>Scan</span>
                      </button>

                      {/* Deletion (Admins & Owners) */}
                      {hasRole('ADMIN', 'OPERATOR') && item.status !== 'DELETED' && (
                        <button
                          onClick={() => setDeleteDocId(item.prescription_id)}
                          className="inline-flex items-center p-1.5 text-stone-400 hover:text-[#BE123C] hover:bg-[#FFE4E6] rounded-lg transition cursor-pointer"
                          title="Secure patient deletion request"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination controls */}
          <div className="px-4 py-3 bg-[#FAF9F6] border-t border-stone-200 flex items-center justify-between text-xs text-stone-600">
            <div>
              Showing page <span className="font-bold text-[#1C252E]">{page}</span> of{' '}
              <span className="font-bold text-[#1C252E]">{totalPages}</span> ({total} total records)
            </div>

            <div className="flex items-center gap-1.5">
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
