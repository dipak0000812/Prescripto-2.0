import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useLocation, Link, useNavigate } from 'react-router-dom';
import {
  getAnalysisStatusApi,
  getAnalysisResultApi,
  submitReviewApi,
  getClinicalSummaryApi,
  updateAnalysisMedicationsApi,
  retryAnalysisApi,
  ClinicalSummaryResponse,
} from '../api/analyses';
import { getPrescriptionApi, listPrescriptionsApi } from '../api/prescriptions';
import {
  AnalysisStatusResponse,
  AnalysisResult,
  PrescriptionDetail,
  ReviewDecision,
  ReviewAction,
} from '../types/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { PrescriptionImageModal } from '../components/PrescriptionImageModal';
import { MedicineHeroCard } from '../components/MedicineHeroCard';
import { EditMedicineModal } from '../components/EditMedicineModal';
import { SetRemindersModal } from '../components/SetRemindersModal';
import { StageProgressBar } from '../components/StageProgressBar';
import { Button } from '../components/ui/Button';
import { AlertBanner } from '../components/ui/AlertBanner';
import { BottomSheet } from '../components/ui/BottomSheet';
import { Badge } from '../components/ui/Badge';
import { formatLocaleDate } from '../utils/dateUtils';
import {
  parseMedicationSchedule,
  buildMedicationSpokenText,
  buildWhatsAppShareText,
  DerivedSchedule,
} from '../utils/medicationSchedule';
import {
  ShieldSafetyIcon,
  AlertAmberIcon,
  CheckmarkIcon,
  ListenIcon,
} from '../components/icons/HealthcareIcons';
import {
  Eye,
  EyeOff,
  Printer,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  Stethoscope,
  Square,
  Share2,
  Clock,
  User,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
} from 'lucide-react';

export const AnalysisDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { session } = useAuth();
  const { t, language, speak, stopSpeaking, isSpeaking } = useLanguage();

  const [statusData, setStatusData] = useState<AnalysisStatusResponse | null>(null);
  const [resultData, setResultData] = useState<AnalysisResult | null>(null);
  const [prescriptionDetail, setPrescriptionDetail] = useState<PrescriptionDetail | null>(null);
  const [clinicalSummary, setClinicalSummary] = useState<ClinicalSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Hero screen view state
  const [showMobilePhotoSheet, setShowMobilePhotoSheet] = useState<boolean>(false);
  const [showDesktopSplitPhoto, setShowDesktopSplitPhoto] = useState<boolean>(true);
  const [showImageModal, setShowImageModal] = useState<boolean>(false);
  const [selectedPhotoItem, setSelectedPhotoItem] = useState<{
    name: string;
    originalText: string;
    box?: [number, number, number, number] | null;
  } | null>(null);
  const [speakingMedIndex, setSpeakingMedIndex] = useState<number | null>(null);
  const [confirmedByUser, setConfirmedByUser] = useState<boolean>(false);
  const [somethingWrongNotice, setSomethingWrongNotice] = useState<boolean>(false);
  const [saveSuccessNotice, setSaveSuccessNotice] = useState<boolean>(false);
  const [showRemindersModal, setShowRemindersModal] = useState<boolean>(false);
  const [expandedSafetyIndex, setExpandedSafetyIndex] = useState<number | null>(null);

  // Editing state
  const [editingMedIndex, setEditingMedIndex] = useState<number | null>(null);
  const [isSavingMed, setIsSavingMed] = useState<boolean>(false);
  const [isRetrying, setIsRetrying] = useState<boolean>(false);

  // Clinician / Staff review state
  const [showClinicianDetails, setShowClinicianDetails] = useState<boolean>(false);
  const [reviewDecisions, setReviewDecisions] = useState<Record<string, { action: ReviewAction; notes: string }>>({});
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [reviewSuccessMsg, setReviewSuccessMsg] = useState<string | null>(null);

  // Poll analysis status & fetch results
  const pollStatusAndResult = async () => {
    if (!id) return;
    try {
      const st = await getAnalysisStatusApi(id);
      setStatusData(st);

      // Fetch prescription document metadata so image preview works
      const passedPrescId =
        (st as any).prescription_id ||
        (location.state as any)?.prescriptionId;

      if (passedPrescId) {
        try {
          const presc = await getPrescriptionApi(passedPrescId);
          setPrescriptionDetail(presc);
        } catch {
          setPrescriptionDetail(null);
        }
      } else {
        try {
          const prescList = await listPrescriptionsApi(1, 20);
          const matched = prescList.items.find(
            (p) => p.latest_analysis_id === id
          );
          if (matched) {
            const presc = await getPrescriptionApi(matched.prescription_id);
            setPrescriptionDetail(presc);
          }
        } catch {}
      }

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

          try {
            const summary = await getClinicalSummaryApi(id);
            setClinicalSummary(summary);
          } catch {}

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
        } catch {
          setError('Unable to load prescription details. Please refresh or try again.');
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to check analysis status.');
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

  // Derived structured medication list
  const derivedMedications = useMemo(() => {
    if (!resultData) return [];

    const sourceList =
      clinicalSummary?.medicines_and_treatments &&
      clinicalSummary.medicines_and_treatments.length > 0
        ? clinicalSummary.medicines_and_treatments.map((m, idx) => ({
            lineIndex: idx,
            name: m.name || m.original_text,
            originalText: m.original_text,
            strength: m.strength || null,
            dose: m.dose || null,
            frequency: m.frequency || null,
            route: m.route || null,
            duration: m.duration || null,
            instructions: m.instructions || null,
            needsReview: Boolean(m.needs_confirmation),
          }))
        : resultData.medications && resultData.medications.length > 0
        ? resultData.medications.map((m) => ({
            lineIndex: m.line_index,
            name: m.name.value || `Medicine #${m.line_index + 1}`,
            originalText: m.name.value || '',
            strength: m.strength.value,
            dose: m.dose.value,
            frequency: m.frequency.value,
            route: m.route.value,
            duration: m.duration.value,
            instructions: m.instructions.value,
            needsReview: m.name.state !== 'CLEAR' || m.resolution_status !== 'RESOLVED',
          }))
        : (resultData.document_extraction?.medication_orders || []).map((m, idx) => ({
            lineIndex: idx,
            name: m.name || m.original_text,
            originalText: m.original_text,
            strength: m.strength,
            dose: m.dose,
            frequency: m.frequency,
            route: m.route,
            duration: m.duration,
            instructions: m.instructions,
            needsReview: Boolean(m.needs_review),
          }));

    return sourceList.map((item) => ({
      ...item,
      schedule: parseMedicationSchedule(
        item.name,
        item.frequency,
        item.instructions,
        item.dose,
        item.strength,
        item.duration,
        item.route,
        item.needsReview
      ),
    }));
  }, [resultData, clinicalSummary]);

  // Calculate One-Line Plain Summary
  const summaryLine = useMemo(() => {
    const medCount = derivedMedications.length;
    if (medCount === 0) return 'No medicines identified yet';

    const maxDays = derivedMedications.reduce((max, m) => {
      const d = parseInt(m.schedule.durationDays || '0', 10);
      return !isNaN(d) && d > max ? d : max;
    }, 0);

    const medWord = medCount === 1 ? '1 medicine' : `${medCount} medicines`;
    const durWord = maxDays > 0 ? `longest ${maxDays} days` : 'as directed';
    return `${medWord}, ${durWord}`;
  }, [derivedMedications]);

  // Sort Safety Findings: CONFIRMED/REQUIRES_REVIEW first, then check_type
  const sortedSafetyFindings = useMemo(() => {
    if (!resultData?.findings) return [];
    return [...resultData.findings].sort((a, b) => {
      const isUrgentA = a.finding_status === 'CONFIRMED_BY_SOURCE' || a.finding_status === 'REQUIRES_REVIEW';
      const isUrgentB = b.finding_status === 'CONFIRMED_BY_SOURCE' || b.finding_status === 'REQUIRES_REVIEW';
      if (isUrgentA && !isUrgentB) return -1;
      if (!isUrgentA && isUrgentB) return 1;
      return a.check_type.localeCompare(b.check_type);
    });
  }, [resultData?.findings]);

  // Handle single medicine speak
  const handleListenMedicine = (schedule: DerivedSchedule, index: number) => {
    if (isSpeaking && speakingMedIndex === index) {
      stopSpeaking();
      setSpeakingMedIndex(null);
      return;
    }
    setSpeakingMedIndex(index);
    const text = buildMedicationSpokenText(schedule, language);
    speak(text);
  };

  // Handle listen to ALL medicines
  const handleListenAll = () => {
    if (isSpeaking) {
      stopSpeaking();
      setSpeakingMedIndex(null);
      return;
    }

    if (derivedMedications.length === 0) return;

    setSpeakingMedIndex(-1);
    const allTexts = derivedMedications.map(
      (m, idx) =>
        `Medicine ${idx + 1}: ${buildMedicationSpokenText(m.schedule, language)}`
    );
    const preamble =
      language === 'hi'
        ? 'आपके पर्चे की सभी दवाइयाँ:'
        : language === 'gu'
        ? 'તમારા પ્રિસ્ક્રિપ્શનની બધી દવાઓ:'
        : language === 'mr'
        ? 'तुमच्या प्रिस्क्रिप्शनमधील सर्व औषधे:'
        : 'All medicines on your prescription:';

    speak(`${preamble} ${allTexts.join(' ')}`);
  };

  // Handle WhatsApp Share
  const handleShareWhatsApp = () => {
    if (derivedMedications.length === 0) return;
    const date = resultData?.document_extraction?.date || prescriptionDetail?.uploaded_at;
    const text = buildWhatsAppShareText(
      derivedMedications.map((m) => m.schedule),
      date
    );
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
  };

  // Handle Save Medication from Edit Modal
  const handleSaveMedicationEdit = async (updated: {
    line_index: number;
    name: string;
    strength: string;
    frequency: string;
    instructions: string;
    duration: string;
  }) => {
    if (!id) return;
    setIsSavingMed(true);
    setError(null);
    try {
      const result = await updateAnalysisMedicationsApi(id, [
        {
          line_index: updated.line_index,
          name: updated.name,
          strength: updated.strength,
          frequency: updated.frequency,
          instructions: updated.instructions,
          duration: updated.duration,
        },
      ]);
      setResultData(result);
      setEditingMedIndex(null);
      setReviewSuccessMsg('Medicine details updated and schedule refreshed.');
      getClinicalSummaryApi(id).then(setClinicalSummary).catch(() => {});
      pollStatusAndResult();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Could not update medicine. Please try again.';
      setError(msg);
      throw new Error(msg);
    } finally {
      setIsSavingMed(false);
    }
  };

  // Handle Retry Scan
  const handleRetryScan = async () => {
    if (!id) return;
    setIsRetrying(true);
    setError(null);
    try {
      const res = await retryAnalysisApi(id);
      setStatusData(res);
      setReviewSuccessMsg('Prescription scan re-queued. Processing will begin shortly...');
      pollStatusAndResult();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to retry prescription analysis.');
    } finally {
      setIsRetrying(false);
    }
  };

  // Handle Reviewer submission
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
        `Clinical sign-off recorded successfully. Status: ${res.overall_status.replace(/_/g, ' ')}`
      );
      pollStatusAndResult();
    } catch (err: any) {
      setError(err?.message || 'Failed to submit clinical sign-off.');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  if (!id) return null;

  const isProcessing =
    statusData?.status === 'QUEUED' || statusData?.status === 'PROCESSING';

  // Resolved metadata for header
  const patientDisplayName =
    prescriptionDetail?.patient_name ||
    session?.patient_name ||
    'Walk-in Patient';
  const patientIdDisplay =
    prescriptionDetail?.patient_ref ||
    session?.patient_id ||
    null;
  const doctorNameDisplay =
    resultData?.document_extraction?.hospital_details?.[0] ||
    'Prescribing Clinic / Doctor';
  const dateDisplay = formatLocaleDate(
    resultData?.document_extraction?.date || prescriptionDetail?.uploaded_at,
    language
  );

  return (
    <div className="space-y-6 pb-28 text-left animate-in fade-in duration-150">
      {/* Print-Only Header */}
      <div className="print-only mb-6 border-b-2 border-stone-900 pb-4 text-left">
        <h1 className="text-xl font-bold text-stone-900">
          Prescripto 2.0 — Prescription Medication Schedule
        </h1>
        <p className="text-xs text-stone-600 mt-1">
          Printed on {new Date().toLocaleDateString()} · Patient: {patientDisplayName} · Doctor: {doctorNameDisplay}
        </p>
        <p className="text-xs text-stone-700 mt-2 font-medium">
          {t(
            'hero.safety_disclaimer',
            'This is a computer reading of your prescription. Please check it with your doctor or chemist before taking any medicine.'
          )}
        </p>
      </div>

      {/* Breadcrumb Navigation & Top Action Bar */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-200 text-xs">
        <div className="flex items-center gap-2 text-stone-500">
          <Link
            to={session?.is_patient ? '/patient-portal' : '/prescriptions'}
            className="hover:text-[#0F5147] font-semibold"
          >
            {session?.is_patient ? t('nav.my_portal', 'My Health Portal') : t('nav.prescriptions', 'Prescriptions')}
          </Link>
          <ChevronRight className="w-3.5 h-3.5 text-stone-400" />
          <span className="font-bold text-[#1C252E]">
            {t('hero.title', 'Your Prescribed Medicines')}
          </span>
        </div>

        {/* Top Quick Actions */}
        <div className="flex items-center gap-2">
          {prescriptionDetail?.image_url && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowImageModal(true)}
              leftIcon={<Eye className="w-3.5 h-3.5 text-[#0F5147]" />}
            >
              {t('hero.see_photo', 'See original photo')}
            </Button>
          )}

          <Button
            size="sm"
            variant="ghost"
            onClick={pollStatusAndResult}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-[#0F5147]' : ''}`} />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* PROCESSING STATE: Reading Prescription */}
      {/* ========================================================================= */}
      {isProcessing && (
        <div className="bg-white border border-stone-200 rounded-2xl p-8 sm:p-12 text-center space-y-6 shadow-xs max-w-xl mx-auto my-8">
          <div className="w-16 h-16 rounded-2xl bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center mx-auto">
            <RefreshCw className="w-8 h-8 animate-spin" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-[#1C252E]">
              {t('upload.waiting_title', 'Reading your prescription… about 20 seconds')}
            </h2>
            <p className="text-sm text-stone-600 max-w-md mx-auto leading-relaxed">
              {t('upload.waiting_sub', 'Please keep this screen open. We are organizing your medicines.')}
            </p>
          </div>
          {statusData && (
            <div className="pt-2">
              <StageProgressBar stages={statusData.stages} currentStatus={statusData.status} />
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* FAILED STATE: Scan Error with Retry Button */}
      {/* ========================================================================= */}
      {statusData?.status === 'FAILED' && (
        <div className="bg-white border border-stone-200 rounded-2xl p-8 sm:p-12 text-center space-y-6 shadow-xs max-w-xl mx-auto my-8">
          <div className="w-16 h-16 rounded-2xl bg-[#FFE4E6] text-[#BE123C] flex items-center justify-center mx-auto border border-[#FDA4AF]">
            <AlertCircle className="w-8 h-8" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-[#1C252E]">
              {t('analysis.scan_error_title', 'Prescription Scan Error')}
            </h2>
            <p className="text-sm text-stone-600 max-w-md mx-auto leading-relaxed">
              {statusData.error_message ||
                'The analysis encountered an error reading the prescription image. Please try again or re-upload a clearer photo.'}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Button
              variant="primary"
              onClick={handleRetryScan}
              isLoading={isRetrying}
              leftIcon={<RefreshCw className="w-4 h-4" />}
              className="w-full sm:w-auto min-h-[44px]"
            >
              {t('analysis.try_again', 'Try again')}
            </Button>

            {prescriptionDetail?.image_url && (
              <Button
                variant="outline"
                onClick={() => {
                  setSelectedPhotoItem(null);
                  setShowImageModal(true);
                }}
                leftIcon={<Eye className="w-4 h-4 text-[#0F5147]" />}
                className="w-full sm:w-auto min-h-[44px]"
              >
                {t('analysis.inspect_scan', 'Inspect scan photo')}
              </Button>
            )}

            <Link to="/upload" className="w-full sm:w-auto">
              <Button variant="ghost" className="w-full sm:w-auto min-h-[44px]">
                {t('analysis.upload_new', 'Upload another photo')}
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* Notifications / Feedback Banners */}
      {error && (
        <AlertBanner type="error" title="Notice">
          {error}
        </AlertBanner>
      )}

      {reviewSuccessMsg && (
        <AlertBanner type="success" title="Saved">
          {reviewSuccessMsg}
        </AlertBanner>
      )}

      {confirmedByUser && (
        <div className="p-4 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-[#047857] shrink-0" />
          <span className="text-sm font-bold">
            {t('hero.confirmed_toast', 'Marked as reviewed and confirmed!')}
          </span>
        </div>
      )}

      {somethingWrongNotice && (
        <div className="p-4 rounded-xl bg-[#FEF3C7] border border-[#FCD34D] text-[#78350F] flex items-start gap-3">
          <AlertAmberIcon className="text-[#B45309] shrink-0 mt-0.5" size={20} />
          <div className="text-xs sm:text-sm">
            <p className="font-bold">Notice something that needs fixing?</p>
            <p className="mt-0.5 text-stone-700">
              Tap the <strong>Edit</strong> button on any medicine card below to adjust names, doses, or timings. You can also view the original prescription photo to double-check handwriting.
            </p>
          </div>
        </div>
      )}

      {saveSuccessNotice && (
        <div className="p-4 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] flex items-center gap-3">
          <CheckmarkIcon className="text-[#047857] shrink-0" size={20} />
          <span className="text-sm font-bold">
            Prescription saved to your medical records!
          </span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* THE HERO SCREEN: HEADER WITH PATIENT, DOCTOR, DATE & 1-LINE SUMMARY */}
      {/* ========================================================================= */}
      {resultData && !isProcessing && (
        <div className="space-y-6">
          <section className="bg-white border border-stone-200 rounded-2xl p-6 sm:p-7 shadow-xs space-y-4 text-left">
            {/* Header: Patient, Doctor, Date (No raw UUIDs) */}
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4 border-b border-stone-100">
              <div className="space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xl sm:text-2xl font-extrabold text-[#1C252E] tracking-tight">
                    {patientDisplayName}
                  </span>
                  {patientIdDisplay && (
                    <span className="font-mono text-xs px-2 py-0.5 rounded-md bg-[#F4F2EC] text-stone-700 border border-stone-200">
                      {patientIdDisplay}
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2 pt-0.5 text-xs sm:text-sm text-stone-600">
                  <span className="font-medium text-stone-700 flex items-center gap-1">
                    <Stethoscope className="w-3.5 h-3.5 text-[#0F5147]" />
                    {doctorNameDisplay}
                  </span>
                  <span>•</span>
                  <span>{dateDisplay}</span>
                </div>

                {/* Plain 1-line summary */}
                <p className="text-sm font-semibold text-[#0F5147] pt-1">
                  {summaryLine}
                </p>
              </div>

              {/* Big Voice Button: Listen to all medicines */}
              <div className="flex flex-wrap items-center gap-2.5 shrink-0">
                <Button
                  type="button"
                  variant="primary"
                  size="md"
                  onClick={handleListenAll}
                  leftIcon={
                    isSpeaking && speakingMedIndex === -1 ? (
                      <Square className="w-4 h-4 animate-pulse text-white" />
                    ) : (
                      <ListenIcon size={18} className="text-white" />
                    )
                  }
                  className={`min-h-[48px] text-sm font-bold shadow-2xs ${
                    isSpeaking && speakingMedIndex === -1
                      ? 'bg-[#BE123C] hover:bg-[#9F1239]'
                      : 'bg-[#0F5147] hover:bg-[#0A3831]'
                  }`}
                  aria-label="Listen to all prescribed medicines"
                >
                  <span>
                    {isSpeaking && speakingMedIndex === -1
                      ? t('hero.stop_voice', 'Stop listening')
                      : t('hero.listen_all', 'Listen to all medicines')}
                  </span>
                </Button>

                {/* Mobile Photo Trigger */}
                {prescriptionDetail?.image_url && (
                  <Button
                    type="button"
                    variant="outline"
                    size="md"
                    onClick={() => setShowMobilePhotoSheet(true)}
                    leftIcon={<Eye className="w-4 h-4 text-[#0F5147]" />}
                    className="md:hidden min-h-[48px] text-xs font-semibold"
                  >
                    <span>{t('hero.see_photo', 'See photo')}</span>
                  </Button>
                )}
              </div>
            </div>

            {/* Calm, Always-Visible Safety Note */}
            <div className="p-3.5 rounded-xl bg-[#FAF9F6] border border-stone-200 text-xs sm:text-sm text-stone-700 leading-relaxed flex items-start gap-2.5">
              <ShieldSafetyIcon size={18} className="text-[#0F5147] shrink-0 mt-0.5" />
              <span>
                <strong>{t('safety.title', 'Please remember')}: </strong>
                {t(
                  'hero.safety_disclaimer',
                  'This is a computer reading of your prescription. Please check it with your doctor or chemist before taking any medicine.'
                )}
              </span>
            </div>
          </section>

          {/* MAIN GRID: Hero Medicine Cards (Left) + Desktop Side-by-Side Photo (Right) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div
              className={
                prescriptionDetail?.image_url && showDesktopSplitPhoto
                  ? 'lg:col-span-7 space-y-4'
                  : 'lg:col-span-12 space-y-4'
              }
            >
              {derivedMedications.length === 0 ? (
                <div className="p-10 text-center bg-white border border-stone-200 rounded-2xl text-stone-500 italic">
                  No medication orders were identified on this prescription document.
                </div>
              ) : (
                derivedMedications.map((item, idx) => (
                  <MedicineHeroCard
                    key={idx}
                    schedule={item.schedule}
                    originalText={item.originalText}
                    isSpeaking={isSpeaking && speakingMedIndex === idx}
                    onListen={() => handleListenMedicine(item.schedule, idx)}
                    onEdit={() => setEditingMedIndex(idx)}
                    onAsk={() => {
                      // Navigate or jump to assistant
                      window.location.href = `/help?ask=${encodeURIComponent(item.name)}`;
                    }}
                    onShowPhoto={() => {
                      const extractionLines = (resultData as any)?.document_extraction?.lines || [];
                      const matchedLine = extractionLines.find(
                        (l: any) =>
                          l.text &&
                          item.originalText &&
                          (l.text.toLowerCase().includes(item.originalText.toLowerCase()) ||
                            item.originalText.toLowerCase().includes(l.text.toLowerCase()))
                      );
                      setSelectedPhotoItem({
                        name: item.name,
                        originalText: item.originalText || item.name,
                        box: matchedLine?.box || null,
                      });
                      setShowImageModal(true);
                    }}
                  />
                ))
              )}

              {/* ========================================================================= */}
              {/* SAFETY FINDINGS IN THEIR OWN SECTION ORDERED BY SEVERITY */}
              {/* ========================================================================= */}
              {sortedSafetyFindings.length > 0 && (
                <section className="bg-white border border-stone-200 rounded-2xl p-5 sm:p-6 shadow-xs space-y-4 text-left">
                  <div className="flex items-center gap-2 pb-2 border-b border-stone-100">
                    <ShieldSafetyIcon size={20} className="text-[#BE123C]" />
                    <h2 className="text-base sm:text-lg font-bold text-[#1C252E]">
                      Safety Findings ({sortedSafetyFindings.length})
                    </h2>
                  </div>

                  <div className="space-y-3">
                    {sortedSafetyFindings.map((finding, fIdx) => {
                      const isFlagged =
                        finding.finding_status === 'CONFIRMED_BY_SOURCE' ||
                        finding.finding_status === 'REQUIRES_REVIEW' ||
                        finding.finding_status === 'POTENTIAL';
                      const isExpanded = expandedSafetyIndex === fIdx;

                      return (
                        <div
                          key={finding.finding_id || fIdx}
                          className={`rounded-xl border p-4 transition ${
                            isFlagged
                              ? 'bg-[#FFE4E6]/50 border-[#FDA4AF]'
                              : 'bg-[#ECFDF5]/50 border-[#A7F3D0]'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <Badge
                                  variant={isFlagged ? 'danger' : 'success'}
                                  size="sm"
                                  dot
                                >
                                  {isFlagged ? 'Safety Attention' : 'Verified Safe'}
                                </Badge>
                                <span className="font-bold text-sm text-[#1C252E]">
                                  {finding.check_type.replace(/_/g, ' ')}
                                </span>
                              </div>
                              <p className="text-xs sm:text-sm text-stone-700 leading-relaxed">
                                {finding.evidence_text || 'Automated safety screening completed against CDSCO clinical guidelines.'}
                              </p>
                            </div>

                            <button
                              type="button"
                              onClick={() => setExpandedSafetyIndex(isExpanded ? null : fIdx)}
                              className="text-xs font-semibold text-stone-500 hover:text-stone-800 p-1 rounded-md cursor-pointer shrink-0 flex items-center gap-1"
                            >
                              <span>{isExpanded ? 'Less' : 'Details'}</span>
                              <ChevronDown
                                className={`w-3.5 h-3.5 transition-transform ${
                                  isExpanded ? 'rotate-180' : ''
                                }`}
                              />
                            </button>
                          </div>

                          {/* Expandable Technical Clinical Details */}
                          {isExpanded && (
                            <div className="mt-3 pt-3 border-t border-stone-200/60 text-xs text-stone-600 font-mono space-y-1 bg-white/70 p-3 rounded-lg">
                              <div>Check: {finding.check_type}</div>
                              <div>Status: {finding.finding_status}</div>
                              <div>Source: {finding.source_name} ({finding.source_version})</div>
                              {finding.not_evaluated_reason && (
                                <div>Not Evaluated: {finding.not_evaluated_reason}</div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}
            </div>

            {/* Desktop Side-by-Side Photo Viewer */}
            {prescriptionDetail?.image_url && (
              <div
                className={`hidden lg:block ${
                  showDesktopSplitPhoto ? 'lg:col-span-5' : 'hidden'
                } sticky top-20`}
              >
                <div className="bg-white border border-stone-200 rounded-2xl p-5 shadow-xs space-y-3 text-left">
                  <div className="flex items-center justify-between pb-2 border-b border-stone-100">
                    <span className="text-xs font-bold uppercase tracking-wider text-stone-700 flex items-center gap-1.5">
                      <Eye className="w-4 h-4 text-[#0F5147]" />
                      Original Prescription Scan
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setShowImageModal(true)}
                      className="text-xs text-[#0F5147]"
                    >
                      Full Zoom
                    </Button>
                  </div>

                  <div
                    onClick={() => setShowImageModal(true)}
                    className="rounded-xl overflow-hidden border border-stone-200 bg-[#FAF9F6] max-h-[75vh] flex items-center justify-center p-2 cursor-pointer group"
                    title="Click to pinch and zoom"
                  >
                    <img
                      src={prescriptionDetail.image_url}
                      alt="Prescription handwritten document"
                      className="max-h-[70vh] object-contain rounded-lg group-hover:scale-102 transition"
                    />
                  </div>

                  <p className="text-[11px] text-stone-500 text-center leading-relaxed">
                    Compare any medicine name or schedule directly with the handwriting.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Clinician & Audit Console for Doctors & Reviewers */}
          {session && !session.is_patient && (
            <div className="pt-6 border-t border-stone-200 space-y-4">
              <div className="flex items-center justify-between bg-stone-100 p-4 rounded-xl border border-stone-200">
                <div className="flex items-center gap-2">
                  <Stethoscope className="w-5 h-5 text-[#0F5147]" />
                  <span className="font-bold text-sm text-[#1C252E]">
                    Clinician Console & Reviewer Audit Sign-Off
                  </span>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowClinicianDetails(!showClinicianDetails)}
                >
                  {showClinicianDetails ? 'Hide Clinical Audit' : 'Show Clinical Audit & Risk Checks'}
                </Button>
              </div>

              {showClinicianDetails && (
                <div className="bg-white border border-stone-200 rounded-2xl p-6 shadow-xs space-y-6 text-left animate-in fade-in">
                  {(session.role === 'DOCTOR' || session.role === 'REVIEWER' || session.role === 'ADMIN') && (
                    <div className="p-5 rounded-xl bg-[#FAF9F6] border border-stone-200 space-y-4">
                      <h3 className="text-sm font-bold text-[#1C252E]">
                        Reviewer Decision Sign-Off
                      </h3>
                      <p className="text-xs text-stone-600">
                        Record verified clinical approval or flag for escalated pharmacist consultation.
                      </p>

                      <div className="flex flex-wrap items-center gap-3">
                        <Button
                          variant="primary"
                          size="md"
                          isLoading={isSubmittingReview}
                          onClick={handleSubmitReview}
                        >
                          Submit Clinical Sign-Off
                        </Button>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div className="p-3.5 bg-stone-50 rounded-xl border border-stone-200">
                      <span className="font-bold text-stone-700 block mb-1">Extracted Vitals</span>
                      <p className="text-stone-600">
                        {resultData.document_extraction?.vitals?.join(', ') || 'None recorded'}
                      </p>
                    </div>

                    <div className="p-3.5 bg-stone-50 rounded-xl border border-stone-200">
                      <span className="font-bold text-stone-700 block mb-1">Symptoms / Complaints</span>
                      <p className="text-stone-600">
                        {resultData.document_extraction?.symptoms?.join(', ') || 'None recorded'}
                      </p>
                    </div>

                    <div className="p-3.5 bg-stone-50 rounded-xl border border-stone-200">
                      <span className="font-bold text-stone-700 block mb-1">Clinical Impression</span>
                      <p className="text-stone-600">
                        {resultData.document_extraction?.diagnosis?.join(', ') || 'None recorded'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ========================================================================= */}
          {/* STICKY BOTTOM ACTION BAR (SAFE-AREA AWARE) */}
          {/* ========================================================================= */}
          <div className="fixed bottom-0 inset-x-0 z-30 bg-white border-t border-stone-200 shadow-xl px-4 py-3 safe-bottom">
            <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
              {/* Primary "Looks right" + Secondary "Something is wrong" */}
              <div className="flex items-center gap-2.5 w-full sm:w-auto">
                <Button
                  type="button"
                  variant="primary"
                  size="md"
                  onClick={() => {
                    setConfirmedByUser(true);
                    setSomethingWrongNotice(false);
                    setShowRemindersModal(true);
                  }}
                  leftIcon={<CheckCircle2 className="w-4 h-4 text-white" />}
                  className="flex-1 sm:flex-initial min-h-[48px] text-sm font-bold bg-[#0F5147] hover:bg-[#0A3831]"
                >
                  {t('hero.looks_right', 'Looks right')}
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  size="md"
                  onClick={() => {
                    setSomethingWrongNotice(true);
                    setConfirmedByUser(false);
                  }}
                  leftIcon={<AlertAmberIcon size={18} className="text-[#B45309]" />}
                  className="flex-1 sm:flex-initial min-h-[48px] text-sm font-bold text-stone-800 border-stone-300 hover:bg-[#FAF9F6]"
                >
                  {t('hero.something_wrong', 'Something is wrong')}
                </Button>
              </div>

              {/* Overflow: WhatsApp Share + Print */}
              <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleShareWhatsApp}
                  leftIcon={<Share2 className="w-3.5 h-3.5 text-[#047857]" />}
                  className="min-h-[44px] text-xs font-semibold text-[#047857] border-[#A7F3D0] hover:bg-[#ECFDF5]"
                >
                  {t('hero.share_whatsapp', 'Share on WhatsApp')}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => window.print()}
                  leftIcon={<Printer className="w-3.5 h-3.5 text-stone-600" />}
                  className="min-h-[44px] text-xs text-stone-700"
                >
                  {t('hero.download_pdf', 'Print / PDF')}
                </Button>
              </div>
            </div>

            {/* Quiet plain disclaimer line */}
            <div className="text-[11px] text-stone-500 text-center pt-1.5 hidden sm:block">
              {t(
                'hero.safety_disclaimer',
                'This is a computer reading of your prescription. Please check it with your doctor or chemist before taking any medicine.'
              )}
            </div>
          </div>
        </div>
      )}

      {/* Mobile Photo Bottom Sheet */}
      {showMobilePhotoSheet && prescriptionDetail?.image_url && (
        <BottomSheet
          isOpen={showMobilePhotoSheet}
          onClose={() => setShowMobilePhotoSheet(false)}
          title="Original Prescription Photo"
          subtitle="Handwritten clinical doctor slip"
          footer={
            <Button
              variant="primary"
              className="w-full min-h-[48px]"
              onClick={() => {
                setShowMobilePhotoSheet(false);
                setShowImageModal(true);
              }}
            >
              Open Full-Screen Zoom & Pan
            </Button>
          }
        >
          <div className="rounded-xl overflow-hidden border border-stone-200 bg-[#FAF9F6] p-2 flex items-center justify-center">
            <img
              src={prescriptionDetail.image_url}
              alt="Prescription scan"
              className="max-h-[60vh] object-contain rounded-lg"
            />
          </div>
        </BottomSheet>
      )}

      {/* Modal: Edit Medicine Details */}
      {editingMedIndex !== null && derivedMedications[editingMedIndex] && (
        <EditMedicineModal
          isOpen={editingMedIndex !== null}
          onClose={() => setEditingMedIndex(null)}
          onSave={handleSaveMedicationEdit}
          lineIndex={derivedMedications[editingMedIndex].lineIndex}
          initialSchedule={derivedMedications[editingMedIndex].schedule}
          isSaving={isSavingMed}
        />
      )}

      {/* Modal: Daily Medicine Reminders Setup */}
      {showRemindersModal && id && (
        <SetRemindersModal
          isOpen={showRemindersModal}
          onClose={() => setShowRemindersModal(false)}
          analysisId={id}
          medications={derivedMedications.map((m) => ({
            id: resultData?.medications?.[m.lineIndex]?.resolved_medication_id || undefined,
            name: m.name,
            schedule: m.schedule,
            originalText: m.originalText,
          }))}
        />
      )}

      {/* Modal: Fullscreen Zoom Photo Inspector */}
      {showImageModal && prescriptionDetail && (
        <PrescriptionImageModal
          prescriptionId={prescriptionDetail.prescription_id}
          initialImageUrl={prescriptionDetail.image_url}
          mimeType={prescriptionDetail.mime_type}
          isOpen={showImageModal}
          onClose={() => {
            setShowImageModal(false);
            setSelectedPhotoItem(null);
          }}
          highlightBox={selectedPhotoItem?.box}
          quotedText={selectedPhotoItem?.originalText || selectedPhotoItem?.name}
          medicineName={selectedPhotoItem?.name}
        />
      )}
    </div>
  );
};

export default AnalysisDetailPage;
