import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listPrescriptionsApi, getPrescriptionApi } from '../api/prescriptions';
import { PrescriptionSummary, DocumentStatus } from '../types/api';
import { useAuth } from '../context/AuthContext';
import { AnalysisStatusBadge } from '../components/Badges';
import { PrescriptionImageModal } from '../components/PrescriptionImageModal';
import { DeleteConfirmModal } from '../components/DeleteConfirmModal';
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
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-teal-600" />
            Prescriptions Ledger
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Browse and review all digitized patient prescription records, safety alerts, and physician determinations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchPrescriptions}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 shadow-2xs transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-teal-600' : ''}`} />
            Refresh
          </button>

          <Link
            to="/upload"
            className="inline-flex items-center gap-2 px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg shadow-xs transition"
          >
            <UploadCloud className="w-4 h-4" />
            Upload Prescription
          </Link>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by Patient Name, ID (PAT-...), or UUID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 transition"
          />
        </div>

        {/* Status Dropdown */}
        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <span className="text-xs font-medium text-slate-600 shrink-0">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 transition text-slate-700 font-medium"
          >
            <option value="ALL">All Statuses</option>
            <option value="REQUIRES_REVIEW">Doctor Review Needed</option>
            <option value="COMPLETED">Safety Verified</option>
            <option value="REVIEWED_COMPLETE">Clinically Approved</option>
            <option value="REVIEWED_ESCALATED">Escalated</option>
            <option value="PROCESSING">Analyzing...</option>
            <option value="QUEUED">Queued</option>
          </select>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      {/* Main Table / Data View */}
      {isLoading && items.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-xs">
          <RefreshCw className="w-8 h-8 text-teal-600 animate-spin mx-auto mb-3" />
          <div className="text-xs font-semibold text-slate-700">Loading prescriptions...</div>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-xs">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-900">No Prescriptions Found</h3>
          <p className="text-xs text-slate-500 mt-1 mb-6 max-w-sm mx-auto">
            {searchQuery || statusFilter !== 'ALL'
              ? 'No prescriptions matched the specified search criteria.'
              : 'No prescriptions have been uploaded yet. Upload a prescription image to start.'}
          </p>
          <Link
            to="/upload"
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg shadow-xs transition"
          >
            <UploadCloud className="w-4 h-4" />
            Upload First Prescription
          </Link>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Patient</th>
                  <th className="py-3 px-4">Prescription Document</th>
                  <th className="py-3 px-4">Uploaded</th>
                  <th className="py-3 px-4">Clinical Safety Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredItems.map((item) => (
                  <tr key={item.prescription_id} className="hover:bg-slate-50/80 transition">
                    {/* Patient Column */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-800 border border-teal-200 flex items-center justify-center font-bold text-xs shrink-0">
                          <User className="w-4 h-4 text-teal-700" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 text-xs">
                            {item.patient_name || 'Walk-in Patient'}
                          </div>
                          {item.patient_ref && (
                            <Link
                              to={`/patients/${item.patient_ref}`}
                              className="font-mono text-[11px] text-teal-700 hover:underline inline-flex items-center gap-1 mt-0.5"
                              title="View Patient Record & History"
                            >
                              <span>{item.patient_ref}</span>
                              <History className="w-3 h-3 text-teal-600" />
                            </Link>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Document UUID */}
                    <td className="py-3 px-4 font-mono text-slate-500 text-[11px] select-all">
                      <div className="truncate max-w-[180px]" title={item.prescription_id}>
                        {item.prescription_id}
                      </div>
                    </td>

                    {/* Upload Date */}
                    <td className="py-3 px-4 text-slate-600">
                      <div className="flex items-center gap-1.5 text-xs">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{new Date(item.uploaded_at).toLocaleString()}</span>
                      </div>
                    </td>

                    {/* Clinical Status */}
                    <td className="py-3 px-4">
                      {item.latest_analysis_status ? (
                        <AnalysisStatusBadge status={item.latest_analysis_status} />
                      ) : (
                        <span className="text-slate-400 italic">No analysis</span>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-right space-x-1.5 whitespace-nowrap">
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
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 rounded-lg text-xs font-medium transition"
                        title="View extracted medications and safety report"
                      >
                        <FileCheck className="w-3.5 h-3.5 text-teal-600" />
                        <span>Report</span>
                      </button>

                      {/* Inspect image scan */}
                      <button
                        onClick={() => handleOpenImageInspector(item.prescription_id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-xs font-medium transition"
                        title="Inspect original prescription scan"
                      >
                        <Eye className="w-3.5 h-3.5 text-slate-500" />
                        <span>Scan</span>
                      </button>

                      {/* Deletion (Admins & Owners) */}
                      {hasRole('ADMIN', 'OPERATOR') && item.status !== 'DELETED' && (
                        <button
                          onClick={() => setDeleteDocId(item.prescription_id)}
                          className="inline-flex items-center p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
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
          <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
            <div>
              Showing page <span className="font-semibold text-slate-900">{page}</span> of{' '}
              <span className="font-semibold text-slate-900">{totalPages}</span> ({total} total records)
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 text-slate-700 font-medium transition shadow-2xs"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                Previous
              </button>

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40 text-slate-700 font-medium transition shadow-2xs"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
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
