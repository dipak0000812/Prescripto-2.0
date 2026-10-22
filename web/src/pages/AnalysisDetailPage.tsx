import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  getAnalysisStatusApi,
  getAnalysisResultApi,
  submitReviewApi,
  getClinicalSummaryApi,
  updateAnalysisMedicationsApi,
  ClinicalSummaryResponse,
} from '../api/analyses';
import { getPrescriptionApi } from '../api/prescriptions';
import {
  AnalysisStatusResponse,
  AnalysisResult,
  PrescriptionDetail,
  ReviewDecision,
  ReviewAction,
} from '../types/api';
import { useAuth } from '../context/AuthContext';
import {
  FieldStateBadge,
  ResolutionStatusBadge,
  FindingStatusBadge,
  AnalysisStatusBadge,
} from '../components/Badges';
import { StageProgressBar } from '../components/StageProgressBar';
import { CoverageDisclaimerCard } from '../components/CoverageDisclaimerCard';
import { PrescriptionImageModal } from '../components/PrescriptionImageModal';
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Eye,
  Send,
  AlertCircle,
  HelpCircle,
  Clock,
  ChevronRight,
  Info,
  Sparkles,
  HeartPulse,
  ShieldCheck,
  Edit3,
  X,
  Save,
} from 'lucide-react';

export const AnalysisDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { session, hasRole } = useAuth();

  const [statusData, setStatusData] = useState<AnalysisStatusResponse | null>(null);
  const [resultData, setResultData] = useState<AnalysisResult | null>(null);
  const [prescriptionDetail, setPrescriptionDetail] = useState<PrescriptionDetail | null>(null);
  const [clinicalSummary, setClinicalSummary] = useState<ClinicalSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Review form state
  const [reviewDecisions, setReviewDecisions] = useState<Record<string, { action: ReviewAction; notes: string }>>({});
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState<string | null>(null);

  // Edit medication state
  const [editingMed, setEditingMed] = useState<{
    line_index: number;
    name: string;
    strength: string;
    dose: string;
    frequency: string;
    route: string;
    duration: string;
    instructions: string;
  } | null>(null);
  const [isSavingMed, setIsSavingMed] = useState<boolean>(false);

  // Image modal state
  const [showImageModal, setShowImageModal] = useState<boolean>(false);

  // Poll analysis status
  const pollStatusAndResult = async () => {
    if (!id) return;
    try {
      const st = await getAnalysisStatusApi(id);
      setStatusData(st);

      // Result gating: only fetch full result if eligible
      const readyStatuses = [
        'COMPLETED',
        'REQUIRES_REVIEW',
        'REVIEWING',
        'REVIEWED_COMPLETE',
        'REVIEWED_ESCALATED',
      ];

      if (readyStatuses.includes(st.status)) {
        try {
          const res = await getAnalysisResultApi(id);
          setResultData(res);

          // Fetch clinical summary concurrently
          try {
            const summary = await getClinicalSummaryApi(id);
            setClinicalSummary(summary);
          } catch (sumErr) {
            console.error('Clinical summary fetch:', sumErr);
          }

          // Initialize review decisions
          if (res.findings && res.findings.length > 0) {
            setReviewDecisions((prev) => {
              const updated = { ...prev };
              res.findings.forEach((f) => {
                if (!updated[f.finding_id]) {
                  updated[f.finding_id] = { action: 'APPROVED', notes: '' };
                }
              });
              return updated;
            });
          }

          // Fetch prescription detail for image URL if available
          if ((st as any).prescription_id) {
            try {
              const presc = await getPrescriptionApi((st as any).prescription_id);
              setPrescriptionDetail(presc);
            } catch (pErr) {
              console.error('Prescription detail fetch:', pErr);
            }
          }
        } catch (resErr: any) {
          console.error('Result fetch error:', resErr);
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to poll analysis status.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    pollStatusAndResult();

    const interval = setInterval(() => {
      if (
        statusData?.status === 'QUEUED' ||
        statusData?.status === 'PROCESSING' ||
        !statusData
      ) {
        pollStatusAndResult();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [id, statusData?.status]);

  // Handle reviewer submission
  const handleSubmitReview = async () => {
    if (!id || !resultData) return;
    setIsSubmittingReview(true);
    setError(null);
    try {
      const decisions: ReviewDecision[] = Object.entries(reviewDecisions).map(
        ([finding_id, d]) => ({
          finding_id,
          action: d.action,
          notes: d.notes || undefined,
        })
      );

      const res = await submitReviewApi(id, { decisions });
      setReviewSuccessMsg(
        `Clinical sign-off recorded successfully! Final Status: ${res.overall_status}`
      );
      pollStatusAndResult();
    } catch (err: any) {
      setError(err?.message || 'Failed to submit clinical review.');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  // Handle doctor medication correction
  const handleSaveMedication = async () => {
    if (!id || !editingMed) return;
    setIsSavingMed(true);
    setError(null);
    try {
      const updated = await updateAnalysisMedicationsApi(id, [
        {
          line_index: editingMed.line_index,
          name: editingMed.name,
          strength: editingMed.strength,
          dose: editingMed.dose,
          frequency: editingMed.frequency,
          route: editingMed.route,
          duration: editingMed.duration,
          instructions: editingMed.instructions,
        },
      ]);
      setResultData(updated);
      setEditingMed(null);
      setReviewSuccessMsg('Medication line updated and clinical safety re-evaluated.');

      // Refresh status and clinical summary
      const st = await getAnalysisStatusApi(id);
      setStatusData(st);
      try {
        const sum = await getClinicalSummaryApi(id);
        setClinicalSummary(sum);
      } catch (sumErr) {}
    } catch (err: any) {
      setError(err?.message || 'Failed to update medication line.');
    } finally {
      setIsSavingMed(false);
    }
  };

  if (!id) return null;

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Breadcrumb & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200 text-xs">
        <div className="flex items-center gap-2 text-slate-500">
          <Link
            to={session?.is_patient ? '/patient-portal' : '/prescriptions'}
            className="hover:text-teal-700 font-medium"
          >
            {session?.is_patient ? 'My Health Portal' : 'Prescriptions'}
          </Link>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-mono text-slate-800 font-semibold truncate max-w-xs">{id}</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={pollStatusAndResult}
            disabled={isLoading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 shadow-2xs transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-teal-600' : ''}`} />
            Refresh Report
          </button>
        </div>
      </div>

      {/* Main Status Header Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Prescription Document Analysis
            </h1>
            {statusData && <AnalysisStatusBadge status={statusData.status} />}
          </div>
          <div className="text-xs text-slate-500 font-mono">
            Analysis ID: <span className="text-slate-700 font-semibold select-all">{id}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowImageModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium rounded-lg border border-slate-300 transition shadow-2xs"
          >
            <Eye className="w-4 h-4 text-slate-500" />
            Inspect Original Scan
          </button>
        </div>
      </div>

      {/* Error notification */}
      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">{error}</div>
        </div>
      )}

      {/* Review Success notification */}
      {reviewSuccessMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed font-semibold">{reviewSuccessMsg}</div>
        </div>
      )}

      {/* 8-Stage Progress Tracker */}
      {statusData && (
        <StageProgressBar
          stages={statusData.stages}
          currentStatus={statusData.status}
        />
      )}

      {/* When processing, show informative live banner */}
      {(statusData?.status === 'QUEUED' || statusData?.status === 'PROCESSING') && (
        <div className="bg-blue-50/70 border border-blue-200 rounded-xl p-6 text-center space-y-3 shadow-2xs">
          <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center mx-auto">
            <RefreshCw className="w-5 h-5 animate-spin" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">
            Prescription Analysis In Progress
          </h3>
          <p className="text-xs text-slate-600 max-w-lg mx-auto leading-relaxed">
            Prescription scanning and safety analysis in progress. Performing handwriting recognition, medication catalog resolution, and multi-layer clinical safety checks. Results will update automatically.
          </p>
        </div>
      )}

      {/* Result Section (when ready) */}
      {resultData && (
        <div className="space-y-6 animate-in fade-in duration-200">
          {/* Metadata chips */}
          <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 text-xs shadow-2xs">
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Analysis Timestamp</span>
                <span className="font-semibold text-slate-800">
                  {new Date(resultData.analysis_timestamp).toLocaleString()}
                </span>
              </div>
              <div className="hidden sm:block h-6 w-px bg-slate-200" />
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Model Engine</span>
                <span className="font-mono text-teal-800 font-medium">
                  {resultData.model_versions.join(', ') || 'RapidOCR + Clinical Safety V2'}
                </span>
              </div>
              <div className="hidden sm:block h-6 w-px bg-slate-200" />
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Safety Databases</span>
                <span className="font-semibold text-slate-800">
                  {resultData.knowledge_snapshots.join(', ') || 'CDSCO Drug Master, OpenFDA'}
                </span>
              </div>
            </div>

            <div className="text-[11px] text-teal-800 font-semibold bg-teal-50 px-2.5 py-1 rounded border border-teal-200">
              Assistive Clinical Verification
            </div>
          </div>

          {/* Clinical AI Summary & Safety Guidance Card */}
          {clinicalSummary && (
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-200">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      Clinical AI Summary & Safety Guidance
                      <span className="text-[10px] font-medium bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full border border-slate-200">
                        {clinicalSummary.engine}
                      </span>
                    </h3>
                    <p className="text-xs text-slate-500">
                      Patient-friendly directions, plain-language explanations, and clinical safeguards
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 text-xs text-emerald-800 font-medium bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  Verified Assistive Engine
                </div>
              </div>

              {/* Executive Summary */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                  Executive Overview
                </div>
                <p className="text-xs leading-relaxed text-slate-800 font-medium">
                  {clinicalSummary.executive_summary}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Patient Instructions */}
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2.5">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900 pb-1.5 border-b border-slate-200">
                    <HeartPulse className="w-4 h-4 text-teal-600" />
                    Patient Dosing Instructions (Plain Language)
                  </div>
                  <ul className="space-y-2 text-xs text-slate-700">
                    {clinicalSummary.patient_instructions.map((inst, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="w-4 h-4 rounded-full bg-teal-100 text-teal-800 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span className="leading-relaxed">{inst}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Clinical Safety Advisories */}
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2.5">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-900 pb-1.5 border-b border-slate-200">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Clinical Safety Advisories & Alerts
                  </div>
                  <ul className="space-y-2 text-xs">
                    {clinicalSummary.clinical_alerts.map((alert, idx) => {
                      const isCritical = alert.includes('CRITICAL') || alert.includes('ALLERGY');
                      return (
                        <li
                          key={idx}
                          className={`p-2.5 rounded-lg border text-xs leading-relaxed ${
                            isCritical
                              ? 'bg-rose-50 border-rose-200 text-rose-900 font-medium'
                              : 'bg-amber-50 border-amber-200 text-amber-900 font-medium'
                          }`}
                        >
                          {alert}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              </div>

              {clinicalSummary.note && (
                <div className="text-[11px] text-slate-600 italic bg-slate-50 p-2.5 rounded-lg border border-slate-200 flex items-center gap-2">
                  <Info className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span>{clinicalSummary.note}</span>
                </div>
              )}
            </div>
          )}

          {/* 1. Structured Medication Lines */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                  Extracted Medication Lines ({resultData.medications.length})
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Handwriting recognition with field-level confidence ratings. Click Edit to correct any transcription errors.
                </p>
              </div>
            </div>

            {resultData.medications.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 italic">
                No medication lines were recognized on this document scan.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px] tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Line</th>
                      <th className="py-3 px-4">Medication Name</th>
                      <th className="py-3 px-4">Strength & Dose</th>
                      <th className="py-3 px-4">Frequency & Route</th>
                      <th className="py-3 px-4">Duration & Instructions</th>
                      <th className="py-3 px-4">Master Resolution</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {resultData.medications.map((m) => (
                      <tr key={m.line_index} className="hover:bg-slate-50/70 transition">
                        <td className="py-3.5 px-4 font-mono font-bold text-slate-400">
                          #{m.line_index + 1}
                        </td>

                        {/* Name */}
                        <td className="py-3.5 px-4">
                          <div className="font-bold text-slate-900 text-sm">
                            {m.name.value || '<Not Present>'}
                          </div>
                          <div className="mt-1">
                            <FieldStateBadge
                              state={m.name.state}
                              confidence={m.name.confidence}
                            />
                          </div>
                        </td>

                        {/* Strength & Dose */}
                        <td className="py-3.5 px-4 space-y-1">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-500 text-[11px]">Strength:</span>
                            <span className="font-medium text-slate-800">
                              {m.strength.value || 'N/A'}
                            </span>
                            <FieldStateBadge state={m.strength.state} confidence={m.strength.confidence} />
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-500 text-[11px]">Dose:</span>
                            <span className="font-medium text-slate-800">
                              {m.dose.value || 'N/A'}
                            </span>
                            <FieldStateBadge state={m.dose.state} confidence={m.dose.confidence} />
                          </div>
                        </td>

                        {/* Frequency & Route */}
                        <td className="py-3.5 px-4 space-y-1">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-500 text-[11px]">Freq:</span>
                            <span className="font-medium text-slate-800">
                              {m.frequency.value || 'N/A'}
                            </span>
                            <FieldStateBadge state={m.frequency.state} confidence={m.frequency.confidence} />
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-500 text-[11px]">Route:</span>
                            <span className="font-medium text-slate-800">
                              {m.route.value || 'N/A'}
                            </span>
                            <FieldStateBadge state={m.route.state} confidence={m.route.confidence} />
                          </div>
                        </td>

                        {/* Duration & Instructions */}
                        <td className="py-3.5 px-4 space-y-1">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-500 text-[11px]">Duration:</span>
                            <span className="font-medium text-slate-800">
                              {m.duration.value || 'N/A'}
                            </span>
                            <FieldStateBadge state={m.duration.state} confidence={m.duration.confidence} />
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-500 text-[11px]">Instr:</span>
                            <span className="font-medium text-slate-800">
                              {m.instructions.value || 'N/A'}
                            </span>
                            <FieldStateBadge state={m.instructions.state} confidence={m.instructions.confidence} />
                          </div>
                        </td>

                        {/* Normalization Status */}
                        <td className="py-3.5 px-4">
                          <ResolutionStatusBadge status={m.resolution_status} />
                          {m.resolved_medication_id && (
                            <div className="text-[10px] font-mono text-slate-500 mt-1 truncate max-w-[130px]" title={m.resolved_medication_id}>
                              ID: {m.resolved_medication_id.substring(0, 8)}...
                            </div>
                          )}
                        </td>

                        {/* Doctor Edit Action */}
                        <td className="py-3.5 px-4 text-right">
                          {hasRole('REVIEWER', 'ADMIN') &&
                            statusData?.status !== 'REVIEWED_COMPLETE' &&
                            statusData?.status !== 'REVIEWED_ESCALATED' && (
                              <button
                                type="button"
                                onClick={() =>
                                  setEditingMed({
                                    line_index: m.line_index,
                                    name: m.name.value || '',
                                    strength: m.strength.value || '',
                                    dose: m.dose.value || '',
                                    frequency: m.frequency.value || '',
                                    route: m.route.value || '',
                                    duration: m.duration.value || '',
                                    instructions: m.instructions.value || '',
                                  })
                                }
                                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-teal-800 bg-teal-50 hover:bg-teal-100 rounded-md border border-teal-200 transition"
                                title="Edit or correct OCR extraction"
                              >
                                <Edit3 className="w-3.5 h-3.5 text-teal-600" />
                                <span>Edit</span>
                              </button>
                            )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* 2. Capability-Aware Risk Findings */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-600" />
                  Clinical Safety Screening & Risk Alerts ({resultData.findings.length})
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Cross-referenced against verified drug safety databases, dosage thresholds, and patient allergies.
                </p>
              </div>
            </div>

            {resultData.findings.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-600 space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                <div className="font-semibold text-slate-900">No Clinical Safety Alerts Flagged</div>
                <p className="text-[11px] text-slate-500 max-w-md mx-auto">
                  No critical contraindications, allergy conflicts, or abnormal dosages were flagged for the recognized medications. Always verify with patient history.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {resultData.findings.map((f) => (
                  <div key={f.finding_id} className="p-6 hover:bg-slate-50/70 transition space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <span className="font-semibold text-xs uppercase tracking-wider text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                          {f.check_type.replace(/_/g, ' ')}
                        </span>
                        <FindingStatusBadge status={f.finding_status} />
                      </div>

                      <div className="text-[11px] text-slate-500 font-medium">
                        Source Reference: <strong className="text-slate-800">{f.source_name}</strong> ({f.source_version})
                      </div>
                    </div>

                    {f.evidence_text && (
                      <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700 leading-relaxed font-sans">
                        <div className="font-semibold text-[11px] text-slate-500 uppercase tracking-wider mb-1">
                          Clinical Evidence & Guidance
                        </div>
                        {f.evidence_text}
                      </div>
                    )}

                    <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                      <span>Evaluated: {new Date(f.check_timestamp).toLocaleString()}</span>
                      {f.confidence_score !== null && (
                        <span>Confidence: {Math.round(f.confidence_score * 100)}%</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 3. Safety Coverage Scope Section */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-blue-600" />
                Safety Coverage Scope & Monitored Checks ({resultData.not_evaluated.length})
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                For clinical transparency, safety checks not covered in the current knowledge tier are clearly listed below.
              </p>
            </div>

            {resultData.not_evaluated.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500 italic">
                All registered check capabilities were evaluated.
              </div>
            ) : (
              <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-3">
                {resultData.not_evaluated.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs flex items-start gap-3"
                  >
                    <Clock className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <div className="font-semibold text-slate-800">
                        Coverage Status:{' '}
                        <span className="text-teal-700 font-semibold">
                          {item.reason === 'PROVIDER_LACKS_CAPABILITY' && 'Specialized Rule Deferred'}
                          {item.reason === 'SOURCE_NOT_COVERING' && 'Drug Monograph Not Available'}
                          {item.reason === 'UNRESOLVED_IDENTITY' && 'Medication Name Unresolved'}
                          {item.reason === 'CHECK_TYPE_DEFERRED' && 'Check Scope Deferred'}
                          {!['PROVIDER_LACKS_CAPABILITY', 'SOURCE_NOT_COVERING', 'UNRESOLVED_IDENTITY', 'CHECK_TYPE_DEFERRED'].includes(item.reason) && item.reason}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 leading-snug">
                        {item.reason === 'PROVIDER_LACKS_CAPABILITY' &&
                          'Specialized check not in current catalog tier. Does not indicate absence of clinical interaction.'}
                        {item.reason === 'SOURCE_NOT_COVERING' &&
                          'Reference monograph not found in current catalog. Clinician review advised.'}
                        {item.reason === 'UNRESOLVED_IDENTITY' &&
                          'Medication name could not be resolved to a canonical CDSCO Master entity.'}
                        {item.reason === 'CHECK_TYPE_DEFERRED' &&
                          'Deferred by design in V1 safety engine architecture.'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 4. Mandatory Clinical Safety Notice */}
          <CoverageDisclaimerCard disclaimer={resultData.coverage_disclaimer} />

          {/* 5. Human-in-the-Loop Clinical Review Section */}
          {(statusData?.status === 'REQUIRES_REVIEW' ||
            statusData?.status === 'REVIEWING' ||
            statusData?.status === 'REVIEWED_COMPLETE' ||
            statusData?.status === 'REVIEWED_ESCALATED') && (
            <div className="bg-white border-2 border-teal-600/30 rounded-xl p-6 shadow-xs space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-teal-600" />
                    Physician & Pharmacist Clinical Sign-off
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Authorized doctors and clinical reviewers must verify safety findings before dispensing or administering medications.
                  </p>
                </div>

                <div className="text-xs">
                  <span className="font-medium text-slate-600">Current Review State: </span>
                  <AnalysisStatusBadge status={statusData.status} />
                </div>
              </div>

              {/* Review decisions inputs */}
              {resultData.findings && resultData.findings.length > 0 ? (
                <div className="space-y-3">
                  <div className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Individual Safety Finding Review
                  </div>

                  {resultData.findings.map((f) => {
                    const currentDecision = reviewDecisions[f.finding_id] || {
                      action: 'APPROVED',
                      notes: '',
                    };

                    const isReviewed =
                      statusData.status === 'REVIEWED_COMPLETE' ||
                      statusData.status === 'REVIEWED_ESCALATED';

                    return (
                      <div
                        key={f.finding_id}
                        className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3 text-xs"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="font-semibold text-slate-800">
                            Finding: <span className="font-mono text-teal-800">{f.check_type}</span> ({f.source_name})
                          </div>

                          {/* Action Selector */}
                          <div className="flex items-center gap-1.5">
                            {(['APPROVED', 'FLAGGED', 'ESCALATED'] as ReviewAction[]).map((act) => (
                              <button
                                key={act}
                                type="button"
                                disabled={isReviewed || !hasRole('REVIEWER', 'ADMIN')}
                                onClick={() =>
                                  setReviewDecisions((prev) => ({
                                    ...prev,
                                    [f.finding_id]: { ...prev[f.finding_id], action: act },
                                  }))
                                }
                                className={`px-2.5 py-1 rounded-md text-xs font-semibold transition ${
                                  currentDecision.action === act
                                    ? act === 'APPROVED'
                                      ? 'bg-teal-600 text-white shadow-2xs'
                                      : act === 'FLAGGED'
                                      ? 'bg-amber-600 text-white shadow-2xs'
                                      : 'bg-rose-600 text-white shadow-2xs'
                                    : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-100'
                                }`}
                              >
                                {act}
                              </button>
                            ))}
                          </div>
                        </div>

                        {/* Reviewer Note */}
                        <div>
                          <input
                            type="text"
                            disabled={isReviewed || !hasRole('REVIEWER', 'ADMIN')}
                            placeholder="Optional clinician notes or pharmacist observation..."
                            value={currentDecision.notes}
                            onChange={(e) =>
                              setReviewDecisions((prev) => ({
                                ...prev,
                                ...prev,
                                [f.finding_id]: { ...prev[f.finding_id], notes: e.target.value },
                              }))
                            }
                            className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-teal-600 disabled:bg-slate-100 disabled:text-slate-400"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-4 bg-slate-50 rounded-lg text-xs text-slate-500 italic border border-slate-200">
                  No active findings flagged. Reviewer can verify extraction quality and confirm completion.
                </div>
              )}

              {/* Submission CTA */}
              {statusData.status === 'REQUIRES_REVIEW' || statusData.status === 'REVIEWING' ? (
                hasRole('REVIEWER', 'ADMIN') ? (
                  <div className="pt-2 flex justify-end">
                    <button
                      type="button"
                      onClick={handleSubmitReview}
                      disabled={isSubmittingReview}
                      className="inline-flex items-center gap-2 px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg shadow-xs transition disabled:opacity-50"
                    >
                      {isSubmittingReview ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Recording Review Decisions...</span>
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          <span>Submit Clinical Review & Sign Off</span>
                        </>
                      )}
                    </button>
                  </div>
                ) : (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                    Your current role (<strong className="uppercase">{session?.role}</strong>) cannot submit clinical reviews. Log in as a Reviewer or Admin to sign off.
                  </div>
                )
              ) : (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-semibold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Clinical review has already been finalized and locked for this analysis.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Doctor Edit Medication Modal */}
      {editingMed && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-7 shadow-xl border border-slate-200 space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 border border-teal-200 flex items-center justify-center">
                  <Edit3 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Correct Medication Line #{editingMed.line_index + 1}
                  </h3>
                  <p className="text-xs text-slate-500">
                    Update OCR transcribed values and recalculate clinical safety
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setEditingMed(null)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Medication Name</label>
                <input
                  type="text"
                  value={editingMed.name}
                  onChange={(e) => setEditingMed({ ...editingMed, name: e.target.value })}
                  placeholder="e.g. Amoxicillin, Paracetamol, Metformin"
                  className="w-full px-3 py-2 border border-slate-300 bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 font-semibold text-slate-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Strength (e.g. 500mg)</label>
                  <input
                    type="text"
                    value={editingMed.strength}
                    onChange={(e) => setEditingMed({ ...editingMed, strength: e.target.value })}
                    placeholder="e.g. 500mg, 650mg"
                    className="w-full px-3 py-2 border border-slate-300 bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 text-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Frequency (e.g. TDS)</label>
                  <input
                    type="text"
                    value={editingMed.frequency}
                    onChange={(e) => setEditingMed({ ...editingMed, frequency: e.target.value })}
                    placeholder="e.g. BD, TDS, Once Daily"
                    className="w-full px-3 py-2 border border-slate-300 bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 text-slate-800"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Duration</label>
                  <input
                    type="text"
                    value={editingMed.duration}
                    onChange={(e) => setEditingMed({ ...editingMed, duration: e.target.value })}
                    placeholder="e.g. 5 days, 1 month"
                    className="w-full px-3 py-2 border border-slate-300 bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 text-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Route</label>
                  <input
                    type="text"
                    value={editingMed.route}
                    onChange={(e) => setEditingMed({ ...editingMed, route: e.target.value })}
                    placeholder="e.g. Oral, Topical"
                    className="w-full px-3 py-2 border border-slate-300 bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 text-slate-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Doctor / Patient Instructions</label>
                <input
                  type="text"
                  value={editingMed.instructions}
                  onChange={(e) => setEditingMed({ ...editingMed, instructions: e.target.value })}
                  placeholder="e.g. Take with warm water after meals"
                  className="w-full px-3 py-2 border border-slate-300 bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 text-slate-800"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setEditingMed(null)}
                className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveMedication}
                disabled={isSavingMed || !editingMed.name.trim()}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-xs transition disabled:opacity-50"
              >
                {isSavingMed ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Re-screening Safety...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Save & Re-screen Safety</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Image Inspector Modal */}
      {showImageModal && (
        <PrescriptionImageModal
          prescriptionId={prescriptionDetail?.prescription_id || id}
          initialImageUrl={prescriptionDetail?.image_url || null}
          isOpen={true}
          onClose={() => setShowImageModal(false)}
        />
      )}
    </div>
  );
};

export default AnalysisDetailPage;
