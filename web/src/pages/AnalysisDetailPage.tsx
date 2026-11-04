import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useParams, useLocation, Link, useNavigate } from 'react-router-dom';
import {
  getAnalysisStatusApi,
  getAnalysisResultApi,
  submitReviewApi,
  getClinicalSummaryApi,
  updateAnalysisMedicationsApi,
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
import { StageProgressBar } from '../components/StageProgressBar';
import { Button } from '../components/ui/Button';
import { AlertBanner } from '../components/ui/AlertBanner';
import {
  parseMedicationSchedule,
  buildMedicationSpokenText,
  buildWhatsAppShareText,
  DerivedSchedule,
} from '../utils/medicationSchedule';
import {
  UploadCloud,
  Eye,
  EyeOff,
  Printer,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ChevronRight,
  ShieldCheck,
  Stethoscope,
  HeartPulse,
  Activity,
  Calendar,
  Building,
  User,
  Volume2,
  Square,
  Share2,
  Save,
  Clock,
  ArrowRight,
  HelpCircle,
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
  const [showMobilePhoto, setShowMobilePhoto] = useState<boolean>(false);
  const [showDesktopSplitPhoto, setShowDesktopSplitPhoto] = useState<boolean>(true);
  const [showImageModal, setShowImageModal] = useState<boolean>(false);
  const [speakingMedIndex, setSpeakingMedIndex] = useState<number | null>(null);
  const [confirmedByUser, setConfirmedByUser] = useState<boolean>(false);
  const [somethingWrongNotice, setSomethingWrongNotice] = useState<boolean>(false);
  const [saveSuccessNotice, setSaveSuccessNotice] = useState<boolean>(false);

  // Editing state
  const [editingMedIndex, setEditingMedIndex] = useState<number | null>(null);
  const [isSavingMed, setIsSavingMed] = useState<boolean>(false);

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

          // Concurrently fetch clinical summary
          try {
            const summary = await getClinicalSummaryApi(id);
            setClinicalSummary(summary);
          } catch {}

          // Initialize clinical review decisions
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

          // Fetch original prescription document image
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
            // Find prescription associated with this analysis
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

  // Derived structured medication list with Class 6 schedule
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

  // Count unsure items
  const unsureCount = useMemo(() => {
    return derivedMedications.filter((m) => m.schedule.isUncertain).length;
  }, [derivedMedications]);

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

    setSpeakingMedIndex(-1); // Special code for all
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
      pollStatusAndResult();
    } catch (err: any) {
      setError(err?.message || 'Could not update medicine. Please try again.');
    } finally {
      setIsSavingMed(false);
    }
  };

  // Handle Reviewer submission (Clinicians)
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

  // Waiting / Processing Screen (Before analysis is ready)
  const isProcessing =
    statusData?.status === 'QUEUED' || statusData?.status === 'PROCESSING';

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-20 animate-in fade-in duration-150">
      {/* Print-Only Header */}
      <div className="print-only mb-6 border-b-2 border-stone-900 pb-4 text-left">
        <h1 className="text-xl font-bold text-stone-900">
          Prescripto 2.0 — Prescription Medication Schedule
        </h1>
        <p className="text-xs text-stone-600 mt-1">
          Printed on {new Date().toLocaleDateString()} · Analysis ID: {id}
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
        <div className="p-4 rounded-2xl bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-[#047857] shrink-0" />
          <span className="text-sm font-bold">
            {t('hero.confirmed_toast', 'Marked as reviewed and confirmed!')}
          </span>
        </div>
      )}

      {somethingWrongNotice && (
        <div className="p-4 rounded-2xl bg-[#FEF3C7] border border-[#FCD34D] text-[#78350F] flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-[#B45309] shrink-0 mt-0.5" />
          <div className="text-xs sm:text-sm">
            <p className="font-bold">Notice something that needs fixing?</p>
            <p className="mt-0.5 text-stone-700">
              Tap the <strong>Edit</strong> button on any medicine card below to adjust names, doses, or timings. You can also view the original prescription photo to double-check handwriting.
            </p>
          </div>
        </div>
      )}

      {saveSuccessNotice && (
        <div className="p-4 rounded-2xl bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] flex items-center gap-3">
          <ShieldCheck className="w-5 h-5 text-[#047857] shrink-0" />
          <span className="text-sm font-bold">
            Prescription saved to your medical records!
          </span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* THE HERO SCREEN: MEDICINE RESULT CARDS */}
      {/* ========================================================================= */}
      {resultData && !isProcessing && (
        <div className="space-y-6">
          {/* HERO HEADER */}
          <section className="bg-white border border-stone-200 rounded-2xl p-6 sm:p-7 shadow-xs space-y-4 text-left">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#0F5147]" aria-hidden="true" />
                  <span>{t('hero.step_badge', 'Step 3 of 3')}</span>
                </div>

                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1C252E] tracking-tight">
                  {t('hero.title', 'Your Prescribed Medicines')}
                </h1>

                <p className="text-sm sm:text-base text-stone-600 leading-relaxed max-w-2xl">
                  {t('hero.subtitle', 'Here is when to take each medicine and for how many days.')}
                </p>
              </div>

              {/* Big Voice Button: Listen to all medicines */}
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="button"
                  variant="primary"
                  size="lg"
                  onClick={handleListenAll}
                  leftIcon={
                    isSpeaking && speakingMedIndex === -1 ? (
                      <Square className="w-5 h-5 animate-pulse text-white" />
                    ) : (
                      <Volume2 className="w-5 h-5 text-white" />
                    )
                  }
                  className={`min-h-[52px] text-base font-bold shadow-xs ${
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

                {/* Mobile Photo Toggle Button */}
                {prescriptionDetail?.image_url && (
                  <Button
                    type="button"
                    variant="outline"
                    size="lg"
                    onClick={() => setShowMobilePhoto(!showMobilePhoto)}
                    leftIcon={
                      showMobilePhoto ? (
                        <EyeOff className="w-5 h-5 text-stone-600" />
                      ) : (
                        <Eye className="w-5 h-5 text-[#0F5147]" />
                      )
                    }
                    className="md:hidden min-h-[52px] text-sm"
                  >
                    <span>
                      {showMobilePhoto
                        ? t('hero.hide_photo', 'Hide photo')
                        : t('hero.see_photo', 'See photo')}
                    </span>
                  </Button>
                )}
              </div>
            </div>

            {/* Calm, Always-Visible Safety Note */}
            <div className="p-4 rounded-xl bg-[#FAF9F6] border border-stone-200 text-xs sm:text-sm text-stone-700 leading-relaxed flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-[#0F5147] shrink-0 mt-0.5" aria-hidden="true" />
              <span>
                <strong>{t('safety.title', 'Please remember')}: </strong>
                {t(
                  'hero.safety_disclaimer',
                  'This is a computer reading of your prescription. Please check it with your doctor or chemist before taking any medicine.'
                )}
              </span>
            </div>
          </section>

          {/* Optional Mobile Inline Photo Drawer */}
          {showMobilePhoto && prescriptionDetail?.image_url && (
            <div className="md:hidden bg-white border border-stone-200 rounded-2xl p-4 shadow-xs space-y-2 text-left">
              <div className="flex items-center justify-between pb-2 border-b border-stone-100">
                <span className="text-xs font-bold text-stone-700 uppercase tracking-wider">
                  Original Prescription Photo
                </span>
                <button
                  type="button"
                  onClick={() => setShowImageModal(true)}
                  className="text-xs font-semibold text-[#0F5147] hover:underline"
                >
                  Tap to Zoom
                </button>
              </div>
              <div
                onClick={() => setShowImageModal(true)}
                className="rounded-xl overflow-hidden border border-stone-200 bg-[#FAF9F6] max-h-72 flex items-center justify-center p-2 cursor-pointer"
              >
                <img
                  src={prescriptionDetail.image_url}
                  alt="Original handwritten prescription scan"
                  className="max-h-64 object-contain rounded-lg"
                />
              </div>
            </div>
          )}

          {/* MAIN GRID: Hero Medicine Cards (Left) + Optional Side-by-Side Photo (Right on Desktop) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* COLUMN 1: Large Medicine Hero Cards */}
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
                    onShowPhoto={() => setShowImageModal(true)}
                  />
                ))
              )}

              {/* BELOW THE CARDS: Primary & Secondary Actions */}
              <div className="bg-white border border-stone-200 rounded-2xl p-5 sm:p-6 shadow-xs space-y-4 text-left">
                {/* 1 Primary Button + 1 Secondary Button */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <Button
                    type="button"
                    variant="primary"
                    size="lg"
                    onClick={() => {
                      setConfirmedByUser(true);
                      setSomethingWrongNotice(false);
                    }}
                    leftIcon={<CheckCircle2 className="w-5 h-5 text-white" />}
                    className="min-h-[52px] text-base font-bold bg-[#0F5147] hover:bg-[#0A3831]"
                  >
                    {t('hero.looks_right', 'Looks right')}
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    size="lg"
                    onClick={() => {
                      setSomethingWrongNotice(true);
                      setConfirmedByUser(false);
                    }}
                    leftIcon={<AlertTriangle className="w-5 h-5 text-[#B45309]" />}
                    className="min-h-[52px] text-base font-bold text-stone-800 border-stone-300 hover:bg-[#FAF9F6]"
                  >
                    {t('hero.something_wrong', 'Something is wrong')}
                  </Button>
                </div>

                {/* Secondary Utility Actions: WhatsApp Share, Print / PDF, Save */}
                <div className="pt-3 border-t border-stone-100 flex flex-wrap items-center justify-between gap-3">
                  {/* Share on WhatsApp */}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleShareWhatsApp}
                    leftIcon={<Share2 className="w-4 h-4 text-[#047857]" />}
                    className="min-h-[44px] text-xs font-semibold text-[#047857] border-[#A7F3D0] hover:bg-[#ECFDF5]"
                  >
                    {t('hero.share_whatsapp', 'Share on WhatsApp')}
                  </Button>

                  <div className="flex items-center gap-2">
                    {/* Print / Download PDF */}
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => window.print()}
                      leftIcon={<Printer className="w-4 h-4 text-stone-600" />}
                      className="min-h-[44px] text-xs text-stone-700"
                    >
                      {t('hero.download_pdf', 'Print / Save PDF')}
                    </Button>

                    {/* Save to My Records */}
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setSaveSuccessNotice(true)}
                      leftIcon={<Save className="w-4 h-4 text-[#0F5147]" />}
                      className="min-h-[44px] text-xs font-semibold text-[#0F5147]"
                    >
                      {t('hero.save_records', 'Save to My Records')}
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* COLUMN 2: Prescription Photo Side-by-Side (Desktop) */}
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

          {/* ========================================================================= */}
          {/* CLINICIAN & AUDIT CONSOLE (Preserved for Doctors, Pharmacists & Admins) */}
          {/* ========================================================================= */}
          {session && !session.is_patient && (
            <div className="pt-8 border-t border-stone-200 space-y-6">
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
                  {/* Doctor/Reviewer Decision Box */}
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

                  {/* Vitals, Symptoms, Impressions */}
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
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: EDIT MEDICINE DETAILS */}
      {/* ========================================================================= */}
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

      {/* ========================================================================= */}
      {/* MODAL: ORIGINAL PRESCRIPTION PHOTO INSPECTION (WITH PINCH-ZOOM) */}
      {/* ========================================================================= */}
      {showImageModal && prescriptionDetail && (
        <PrescriptionImageModal
          prescriptionId={prescriptionDetail.prescription_id}
          initialImageUrl={prescriptionDetail.image_url}
          mimeType={prescriptionDetail.mime_type}
          isOpen={showImageModal}
          onClose={() => setShowImageModal(false)}
        />
      )}
    </div>
  );
};

export default AnalysisDetailPage;
