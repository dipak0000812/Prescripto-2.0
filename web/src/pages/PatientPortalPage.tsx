import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { getPatientTimelineApi, PatientDetail, TimelineEvent } from '../api/patients';
import {
  FileText,
  Camera,
  ArrowRight,
  Clock,
  User,
  HeartPulse,
  RefreshCw,
  AlertCircle,
  Bell,
  HelpCircle,
  CheckCircle2,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { parseMedicationSchedule } from '../utils/medicationSchedule';
import { formatLocaleDate, getTimeBasedGreeting } from '../utils/dateUtils';
import {
  TabletIcon,
  SunriseIcon,
  MiddaySunIcon,
  MoonIcon,
  getMedicineFormIcon,
} from '../components/icons/HealthcareIcons';

type MedicationRecord = TimelineEvent['medications'][number];

export const PatientPortalPage: React.FC = () => {
  const { session } = useAuth();
  const { t, language } = useLanguage();

  const [patientData, setPatientData] = useState<PatientDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState<number>(0);

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
  const patientDisplayName = patient.name || session?.patient_name || 'Patient';
  const greeting = getTimeBasedGreeting(patientDisplayName, language);

  // Identify next dose due based on time of day
  const hour = new Date().getHours();
  const currentSlot: 'morning' | 'afternoon' | 'night' =
    hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'night';

  // Find medicines from the newest prescription that have a dose in currentSlot
  const latestEvent = patient.timeline && patient.timeline.length > 0 ? patient.timeline[0] : null;
  const activeMedsInCurrentSlot = latestEvent?.medications.filter((med) => {
    const sched = parseMedicationSchedule(
      med.name || '',
      med.frequency,
      med.instructions,
      med.dose,
      med.strength,
      med.duration,
      undefined,
      med.state !== 'CLEAR'
    );
    const countKey = `${currentSlot}Count` as 'morningCount' | 'afternoonCount' | 'nightCount';
    return sched[countKey] > 0;
  }) || [];

  return (
    <div className="space-y-6 text-left animate-in fade-in duration-150">
      {/* 1. Time-Based Greeting Card */}
      <section className="bg-white border border-stone-200 rounded-2xl p-6 sm:p-7 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1C252E] tracking-tight">
              {greeting}
            </h1>
            <p className="text-sm text-stone-600">
              Welcome back to your prescription guide.
            </p>
          </div>

          {/* Big "Scan a prescription" Primary Action */}
          <Link to="/upload" className="shrink-0">
            <Button
              variant="primary"
              size="lg"
              className="w-full sm:w-auto min-h-[52px] text-base font-bold bg-[#0F5147] hover:bg-[#0A3831] shadow-xs"
              leftIcon={<Camera className="w-5 h-5 text-white" />}
            >
              Scan a prescription
            </Button>
          </Link>
        </div>
      </section>

      {/* 2. "Next Medicine" Card if Due */}
      {activeMedsInCurrentSlot.length > 0 && (
        <section className="bg-white border-l-4 border-l-[#0F5147] border border-stone-200 rounded-2xl p-5 sm:p-6 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#E6F0EE] text-[#0F5147]">
                {currentSlot === 'morning' ? (
                  <SunriseIcon size={20} />
                ) : currentSlot === 'afternoon' ? (
                  <MiddaySunIcon size={20} />
                ) : (
                  <MoonIcon size={20} />
                )}
              </span>
              <span className="text-xs uppercase font-bold tracking-wider text-[#0F5147]">
                Due this {currentSlot}
              </span>
            </div>

            <Link
              to="/today"
              className="text-xs font-semibold text-[#0F5147] hover:underline flex items-center gap-1"
            >
              <span>See schedule</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {activeMedsInCurrentSlot.slice(0, 2).map((med, idx) => {
              const sched = parseMedicationSchedule(
                med.name || 'Medicine',
                med.frequency,
                med.instructions,
                med.dose,
                med.strength,
                med.duration,
                undefined,
                med.state !== 'CLEAR'
              );
              const FormIcon = getMedicineFormIcon(sched.form);

              return (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-[#FAF9F6] border border-stone-200 flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-white border border-stone-200 flex items-center justify-center text-[#0F5147] shrink-0">
                      <FormIcon size={20} />
                    </div>
                    <div className="min-w-0">
                      <div className="font-bold text-sm text-[#1C252E] truncate">
                        {sched.cleanName}
                      </div>
                      <div className="text-xs text-stone-500">
                        {sched[currentSlot]} · {sched.foodTiming.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                  <Badge variant="brand" size="sm">
                    {sched[currentSlot]}
                  </Badge>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 3. Recent Prescriptions List (Readable Rows) */}
      <section className="space-y-4" aria-label="Prescriptions list">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-base sm:text-lg font-bold text-[#1C252E] flex items-center gap-2">
            <FileText className="w-5 h-5 text-[#0F5147]" />
            <span>Recent Prescriptions</span>
          </h2>
          {patient.timeline.length > 3 && (
            <Link
              to={`/patients/${patient.id}`}
              className="text-xs font-semibold text-[#0F5147] hover:underline"
            >
              View all ({patient.timeline.length})
            </Link>
          )}
        </div>

        {patient.timeline.length > 0 ? (
          <div className="space-y-3">
            {patient.timeline.slice(0, 3).map((event, eventIdx) => {
              const formattedDate = formatLocaleDate(event.uploaded_at, language);
              const isCompleted =
                event.analysis_status === 'COMPLETED' ||
                event.analysis_status === 'REVIEWED_COMPLETE';

              const medNames = event.medications
                .map((m) => m.name)
                .filter(Boolean)
                .slice(0, 3)
                .join(', ');

              return (
                <div
                  key={event.document_id || eventIdx}
                  className="bg-white border border-stone-200 rounded-xl p-4 sm:p-5 shadow-2xs hover:border-stone-300 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-base text-[#1C252E]">
                        {event.file_name || `Prescription #${eventIdx + 1}`}
                      </span>
                      <Badge variant={isCompleted ? 'success' : 'warning'} size="sm" dot>
                        {isCompleted ? 'Ready' : 'Doctor Checking'}
                      </Badge>
                    </div>

                    <div className="text-xs text-stone-500 flex items-center gap-2 flex-wrap">
                      <span>{formattedDate}</span>
                      <span>•</span>
                      <span className="text-stone-700 font-medium">
                        {event.medications.length} {event.medications.length === 1 ? 'medicine' : 'medicines'}
                      </span>
                    </div>

                    {medNames && (
                      <p className="text-xs text-stone-600 truncate">
                        {medNames}
                        {event.medications.length > 3 ? '...' : ''}
                      </p>
                    )}
                  </div>

                  {event.analysis_id && (
                    <Link to={`/analyses/${event.analysis_id}`} className="shrink-0">
                      <Button
                        variant="secondary"
                        size="md"
                        className="w-full sm:w-auto min-h-[44px] text-xs sm:text-sm font-semibold"
                        rightIcon={<ArrowRight className="w-4 h-4" />}
                      >
                        View Medicines
                      </Button>
                    </Link>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState
            title={t('portal.no_prescriptions', 'No prescriptions uploaded yet')}
            description="Take a clear photo of your doctor's slip to see medicines and daily timings."
            actionLabel="Scan your first prescription"
            onAction={() => {
              window.location.href = '/upload';
            }}
          />
        )}
      </section>

      {/* 4. Quiet "Need help?" Link */}
      <div className="pt-2 text-center">
        <Link
          to="/help"
          className="inline-flex items-center gap-1.5 text-xs text-stone-500 hover:text-[#0F5147] transition py-2 px-3 rounded-lg hover:bg-[#F4F2EC]"
        >
          <HelpCircle className="w-4 h-4 text-stone-400" />
          <span>Need help understanding your prescription? Read our simple guide.</span>
        </Link>
      </div>
    </div>
  );
};

export default PatientPortalPage;
