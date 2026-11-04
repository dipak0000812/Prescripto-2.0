import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { getPatientTimelineApi, PatientDetail, TimelineEvent } from '../api/patients';
import {
  FileText,
  UploadCloud,
  Volume2,
  Square,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Clock,
  User,
  HeartPulse,
  Pill,
  RefreshCw,
  AlertCircle,
  Eye,
  CheckCircle2,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { StatusChip } from '../components/ui/StatusChip';
import { AlertBanner } from '../components/ui/AlertBanner';
import { EmptyState } from '../components/ui/EmptyState';
import { parseMedicationSchedule, buildMedicationSpokenText } from '../utils/medicationSchedule';

type MedicationRecord = TimelineEvent['medications'][number];

export const PatientPortalPage: React.FC = () => {
  const { session } = useAuth();
  const { t, language, speak, stopSpeaking, isSpeaking } = useLanguage();

  const [patientData, setPatientData] = useState<PatientDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState<number>(0);
  const [speakingId, setSpeakingId] = useState<string | null>(null);

  const patientId = session?.patient_id;

  useEffect(() => {
    let isMounted = true;

    const fetchPatientData = async () => {
      setIsLoading(true);
      setError(null);

      if (!patientId) {
        setError(
          'This account is not linked to a patient record. Contact your care team to link the correct record.'
        );
        setIsLoading(false);
        return;
      }

      try {
        const data = await getPatientTimelineApi(patientId);
        if (isMounted) setPatientData(data);
      } catch {
        if (isMounted)
          setError(
            'We could not load your prescription records. Please check your connection and try again.'
          );
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    void fetchPatientData();
    return () => {
      isMounted = false;
    };
  }, [patientId, retryCount]);

  const handleSpeakSingleMed = (med: MedicationRecord, idKey: string) => {
    if (isSpeaking && speakingId === idKey) {
      stopSpeaking();
      setSpeakingId(null);
      return;
    }

    setSpeakingId(idKey);
    const schedule = parseMedicationSchedule(
      med.name || 'Medicine',
      med.frequency,
      med.instructions,
      med.dose,
      med.strength,
      med.duration,
      undefined,
      med.state !== 'CLEAR'
    );
    const spokenText = buildMedicationSpokenText(schedule, language);
    speak(spokenText);
  };

  if (isLoading) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="min-h-[50vh] flex flex-col items-center justify-center text-center bg-white border border-stone-200 rounded-2xl p-12"
      >
        <RefreshCw className="w-8 h-8 text-[#0F5147] animate-spin mb-3" aria-hidden="true" />
        <h2 className="text-base font-bold text-[#1C252E]">
          {t('common.loading', 'Loading your prescriptions…')}
        </h2>
      </div>
    );
  }

  if (error || !patientData) {
    return (
      <div className="max-w-xl mx-auto my-10 bg-white border border-stone-200 rounded-2xl p-6 sm:p-8 text-center shadow-2xs space-y-4">
        <AlertCircle className="w-10 h-10 text-[#BE123C] mx-auto" aria-hidden="true" />
        <h2 className="text-lg font-bold text-[#1C252E]">Prescription records not available</h2>
        <p className="text-sm text-stone-600 leading-relaxed">
          {error || 'No patient record is currently linked to this mobile number.'}
        </p>

        {patientId ? (
          <Button
            variant="primary"
            size="md"
            onClick={() => setRetryCount((c) => c + 1)}
            className="mt-2 min-h-[48px]"
          >
            {t('upload.try_again_btn', 'Try again')}
          </Button>
        ) : (
          <Link to="/upload">
            <Button variant="primary" size="md" className="min-h-[48px]">
              {t('portal.upload_new', 'Upload New Prescription')}
            </Button>
          </Link>
        )}
      </div>
    );
  }

  const patient = patientData;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16 text-left animate-in fade-in duration-150">
      {/* 1. WELCOME & PATIENT DOSSIER CARD */}
      <section className="bg-white border border-stone-200 rounded-2xl p-6 sm:p-7 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-stone-100">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
              <HeartPulse className="w-3.5 h-3.5 text-[#0F5147]" aria-hidden="true" />
              <span>{t('portal.my_prescriptions', 'My Prescriptions')}</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1C252E] tracking-tight">
              {patient.name || session?.patient_name || 'My Health Guide'}
            </h1>

            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-stone-600">
              {patient.patient_id && (
                <span className="inline-flex items-center gap-1 bg-[#F4F2EC] px-2.5 py-1 rounded-lg border border-stone-200 font-mono">
                  <User className="w-3.5 h-3.5 text-stone-500" />
                  ID: {patient.patient_id}
                </span>
              )}
              {patient.phone_number && (
                <span className="bg-[#F4F2EC] px-2.5 py-1 rounded-lg border border-stone-200 font-semibold">
                  +91 {patient.phone_number}
                </span>
              )}
            </div>
          </div>

          {/* Primary Action Button: Upload New Prescription */}
          <Link to="/upload" className="shrink-0">
            <Button
              variant="primary"
              size="lg"
              className="w-full sm:w-auto min-h-[52px] text-base font-bold bg-[#0F5147] hover:bg-[#0A3831]"
              rightIcon={<UploadCloud className="w-5 h-5 text-white" />}
            >
              {t('portal.upload_new', 'Upload New Prescription')}
            </Button>
          </Link>
        </div>

        {/* Calm, Always-Visible Safety Reminder */}
        <div className="p-3.5 rounded-xl bg-[#FAF9F6] border border-stone-200 text-xs sm:text-sm text-stone-700 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-[#0F5147] shrink-0 mt-0.5" aria-hidden="true" />
          <span className="leading-relaxed">
            <strong>{t('safety.title', 'Safety reminder')}: </strong>
            {t(
              'portal.safety_reminder',
              'Always talk to your doctor or chemist before taking medicines.'
            )}
          </span>
        </div>
      </section>

      {/* 2. PRESCRIPTION DOSSIER LIST */}
      <section className="space-y-4" aria-label="Prescriptions list">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-base sm:text-lg font-bold text-[#1C252E] flex items-center gap-2">
            <FileText className="w-5 h-5 text-[#0F5147]" />
            <span>Prescription Records ({patient.timeline.length})</span>
          </h2>
          <span className="text-xs text-stone-500 font-medium">Sorted by newest first</span>
        </div>

        {patient.timeline.length > 0 ? (
          <div className="space-y-4">
            {patient.timeline.map((event, eventIdx) => {
              const formattedDate = event.uploaded_at
                ? new Date(event.uploaded_at).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                  })
                : 'Date unavailable';

              const isCompleted =
                event.analysis_status === 'COMPLETED' ||
                event.analysis_status === 'REVIEWED_COMPLETE';

              return (
                <article
                  key={event.document_id || eventIdx}
                  className="bg-white border border-stone-200 rounded-2xl p-5 sm:p-6 shadow-2xs space-y-4 hover:border-stone-300 transition"
                >
                  {/* Prescription Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-stone-100">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-base text-[#1C252E]">
                          {event.file_name || `Prescription #${eventIdx + 1}`}
                        </span>
                        <StatusChip
                          variant={isCompleted ? 'success' : 'warning'}
                          label={
                            isCompleted
                              ? t('common.completed', 'Ready')
                              : t('common.pending', 'Needs Check')
                          }
                        />
                      </div>
                      <p className="text-xs text-stone-500 flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5 text-stone-400" />
                        <span>Uploaded on {formattedDate}</span>
                        <span>•</span>
                        <span className="font-semibold text-stone-700">
                          {event.medications.length} {t('portal.medicines_count', 'medicines identified')}
                        </span>
                      </p>
                    </div>

                    {/* Primary Button: View Medicines & Timings */}
                    {event.analysis_id && (
                      <Link to={`/analyses/${event.analysis_id}`}>
                        <Button
                          variant="primary"
                          size="md"
                          className="w-full sm:w-auto min-h-[48px] text-sm font-bold bg-[#0F5147] hover:bg-[#0A3831]"
                          rightIcon={<ArrowRight className="w-4 h-4 text-white" />}
                        >
                          {t('portal.view_medicines', 'View Medicines & Timings')}
                        </Button>
                      </Link>
                    )}
                  </div>

                  {/* Medicines Summary Chips */}
                  {event.medications.length > 0 ? (
                    <div className="space-y-2.5">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {event.medications.map((med, medIdx) => {
                          const medIdKey = `${event.document_id}-${med.line_index || medIdx}`;
                          const isSpeakingThis = isSpeaking && speakingId === medIdKey;

                          const schedule = parseMedicationSchedule(
                            med.name || 'Medicine',
                            med.frequency,
                            med.instructions,
                            med.dose,
                            med.strength,
                            med.duration,
                            undefined,
                            med.state !== 'CLEAR'
                          );

                          return (
                            <div
                              key={medIdKey}
                              className="p-3.5 bg-[#FAF9F6] border border-stone-200 rounded-xl flex items-start justify-between gap-3 text-left"
                            >
                              <div className="min-w-0">
                                <div className="flex items-center gap-1.5">
                                  <Pill className="w-4 h-4 text-[#0F5147] shrink-0" />
                                  <span className="font-bold text-sm text-[#1C252E] truncate">
                                    {schedule.cleanName}
                                  </span>
                                </div>

                                <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-stone-600">
                                  {schedule.strength && (
                                    <span className="font-semibold text-stone-800">
                                      {schedule.strength}
                                    </span>
                                  )}
                                  <span>•</span>
                                  <span>
                                    {schedule.isOnlyIfNeeded
                                      ? 'If needed'
                                      : `M: ${schedule.morning} | A: ${schedule.afternoon} | N: ${schedule.night}`}
                                  </span>
                                </div>

                                {schedule.foodTiming !== 'unspecified' && (
                                  <span className="inline-block mt-1 text-[11px] font-semibold text-[#0F5147]">
                                    {schedule.foodTiming.replace('_', ' ')}
                                  </span>
                                )}
                              </div>

                              {/* Voice Button per medicine */}
                              <button
                                type="button"
                                onClick={() => handleSpeakSingleMed(med, medIdKey)}
                                className={`p-2 rounded-lg border transition shrink-0 cursor-pointer min-h-[40px] min-w-[40px] flex items-center justify-center ${
                                  isSpeakingThis
                                    ? 'bg-[#FFE4E6] text-[#BE123C] border-[#FDA4AF]'
                                    : 'bg-white text-[#0F5147] border-stone-200 hover:bg-[#E6F0EE]'
                                }`}
                                aria-label={`Listen to ${med.name || 'medicine'} directions`}
                                title="Listen in your language"
                              >
                                {isSpeakingThis ? (
                                  <Square className="w-4 h-4 animate-pulse" />
                                ) : (
                                  <Volume2 className="w-4 h-4" />
                                )}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-stone-500 italic p-3 bg-stone-50 rounded-xl">
                      No medication lines recorded on this prescription document.
                    </p>
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          /* Empty State: Warm, encouraging */
          <div className="bg-white border border-stone-200 rounded-2xl p-8 sm:p-12 text-center space-y-4 shadow-2xs">
            <div className="w-14 h-14 rounded-2xl bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center mx-auto">
              <FileText className="w-7 h-7" aria-hidden="true" />
            </div>

            <h3 className="text-lg font-bold text-[#1C252E]">
              {t('portal.no_prescriptions', 'No prescriptions uploaded yet')}
            </h3>

            <p className="text-sm text-stone-600 max-w-md mx-auto leading-relaxed">
              {t(
                'portal.no_prescriptions_sub',
                'Take a clear photo of your doctor slip to organize timings simply.'
              )}
            </p>

            <div className="pt-2">
              <Link to="/upload">
                <Button variant="primary" size="lg" className="min-h-[52px]">
                  {t('portal.upload_new', 'Upload New Prescription')}
                </Button>
              </Link>
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default PatientPortalPage;
