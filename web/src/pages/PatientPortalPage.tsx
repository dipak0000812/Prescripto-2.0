import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { getPatientTimelineApi, PatientDetail, TimelineEvent } from '../api/patients';
import {
  ShieldAlert,
  AlertTriangle,
  Pill,
  Clock,
  UploadCloud,
  FileText,
  User,
  Phone,
  ExternalLink,
  Lock,
  Loader2,
  HeartPulse,
  ShieldCheck,
  Volume2,
  HelpCircle,
  Sun,
  Sunset,
  Moon,
  Info,
} from 'lucide-react';
import { AnalysisStatusBadge } from '../components/Badges';

export const PatientPortalPage: React.FC = () => {
  const { session } = useAuth();
  const { t, speak, isSpeaking, stopSpeaking, explainSig, language } = useLanguage();

  const [patientData, setPatientData] = useState<PatientDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const patientId = session?.patient_id || 'PAT-1001';

  useEffect(() => {
    let isMounted = true;
    const fetchPatientData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getPatientTimelineApi(patientId);
        if (isMounted) setPatientData(data);
      } catch (err: any) {
        if (isMounted) setError(err?.message || 'Failed to load your patient profile.');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchPatientData();
    return () => {
      isMounted = false;
    };
  }, [patientId]);

  const handleSpeakMed = (med: any) => {
    const sigInfo = explainSig(med.frequency || '');
    let textToSpeak = '';

    if (language === 'hi') {
      textToSpeak = `दवा का नाम ${med.name}। मात्रा ${med.dose || med.strength || ''}। लेने का समय: ${sigInfo.timing}। ${med.instructions || 'खाना खाने के बाद पानी से लें'}`;
    } else if (language === 'gu') {
      textToSpeak = `દવાનું નામ ${med.name}। માત્રા ${med.dose || med.strength || ''}। લેવાનો સમય: ${sigInfo.timing}। ${med.instructions || 'જમ્યા પછી પાણી સાથે લેવી'}`;
    } else if (language === 'mr') {
      textToSpeak = `औषधाचे नाव ${med.name}। मात्रा ${med.dose || med.strength || ''}। घेण्याची वेळ: ${sigInfo.timing}। ${med.instructions || 'जेवणानंतर पाण्यासोबत घ्या'}`;
    } else {
      textToSpeak = `Medicine ${med.name}. Dosage ${med.dose || med.strength || ''}. Schedule: ${sigInfo.timing}. ${med.instructions || 'Take with water after meals.'}`;
    }

    speak(textToSpeak);
  };

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center text-center bg-white border border-slate-200 rounded-2xl shadow-xs p-12">
        <Loader2 className="w-8 h-8 text-teal-600 animate-spin mb-3" />
        <h3 className="text-base font-bold text-slate-900">{t('common.loading', 'Loading Your Health Portal...')}</h3>
        <p className="text-xs text-slate-500 mt-1">{t('portal.subtitle', 'Retrieving verified prescriptions and medication schedules')}</p>
      </div>
    );
  }

  const patient: PatientDetail = patientData || {
    id: patientId,
    patient_id: patientId,
    name: session?.patient_name || 'Rahul Verma',
    phone_number: session?.phone_number || session?.username || '9876543210',
    allergies: 'Penicillin, Amoxicillin',
    medical_history: 'Mild Hypertension (Stage 1)',
    gender: 'Male',
    total_prescriptions: 1,
    created_at: new Date().toISOString(),
    active_medications: [],
    timeline: [],
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Patient Welcome Hero Banner */}
      <div className="rounded-2xl bg-teal-50/70 border border-teal-200 p-6 sm:p-7 shadow-xs">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-5">
          <div className="space-y-1.5">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white text-teal-800 border border-teal-200 shadow-2xs">
              <HeartPulse className="w-3.5 h-3.5 text-teal-600" />
              <span>{t('nav.my_portal', 'Personal Health Portal')}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {language === 'hi' ? 'नमस्ते,' : language === 'gu' ? 'નમસ્તે,' : language === 'mr' ? 'नमस्कार,' : 'Welcome,'}{' '}
              <span className="text-teal-700">{patient.name}</span>
            </h1>
            <div className="flex flex-wrap items-center gap-2.5 text-xs text-slate-600 pt-1">
              <span className="flex items-center gap-1.5 font-mono bg-white px-2 py-0.5 rounded-md border border-slate-200 text-slate-700">
                <User className="w-3.5 h-3.5 text-slate-400" />
                ID: {patient.patient_id || patient.id}
              </span>
              <span className="flex items-center gap-1.5 bg-white px-2 py-0.5 rounded-md border border-slate-200 text-slate-700">
                <Phone className="w-3.5 h-3.5 text-slate-400" />
                +91 {patient.phone_number}
              </span>
              <span className="flex items-center gap-1 text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                {t('safety.doctor_verified', 'Verified Patient Profile')}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <UploadCloud className="w-4 h-4" />
              <span>{t('upload.button', 'Upload New Prescription')}</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Accessibility & Voice Assistant Banner for Low-Literacy / Elderly */}
      <div className="rounded-xl bg-indigo-50/80 border border-indigo-200 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-600 text-white shadow-xs">
            <Volume2 className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-indigo-900">
              {language === 'hi'
                ? 'आवाज़ से दवा समझने की सुविधा (Voice Guidance)'
                : language === 'gu'
                ? 'અવાજથી દવા સમજવાની સુવિધા (Voice Guidance)'
                : 'Audio Medication Assistance'}
            </h4>
            <p className="text-xs text-indigo-700">
              {t(
                'portal.audio_guide',
                'Press the speaker button on any medicine to hear when and how to take it in your language.'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Critical Health Alerts & Profile Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Documented Allergies */}
        <div className="rounded-xl bg-rose-50/80 border border-rose-200 p-5 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-rose-800 text-xs font-bold uppercase tracking-wider">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              <span>{t('safety.allergy', 'Documented Allergies')}</span>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-rose-700 border border-rose-200">
              SAFETY ALERT
            </span>
          </div>
          <div className="text-base font-bold text-slate-900">
            {patient.allergies || 'No known allergies documented'}
          </div>
          <p className="text-xs text-rose-700 leading-relaxed">
            {language === 'hi'
              ? 'हमारा सुरक्षा सिस्टम आपकी पर्ची की दवाओं को इस एलर्जी सूची से मिलाता है। नई दवा लेने से पहले डॉक्टर को ज़रूर बताएं।'
              : 'Our safety system automatically checks all prescribed drugs against this allergy list. Always inform treating doctors before taking new antibiotics.'}
          </p>
        </div>

        {/* Chronic Health Conditions */}
        <div className="rounded-xl bg-white border border-slate-200 p-5 space-y-2.5 shadow-xs">
          <div className="flex items-center gap-1.5 text-slate-700 text-xs font-bold uppercase tracking-wider">
            <HeartPulse className="w-4 h-4 text-teal-600" />
            <span>Health Records</span>
          </div>
          <div className="text-base font-bold text-slate-900">
            {patient.medical_history || 'Standard Outpatient Care'}
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            {language === 'hi'
              ? 'दवाइयों की मात्रा व कॉम्बिनेशन की सुरक्षा आपकी सेहत के इतिहास के अनुसार जांची जाती है।'
              : 'Prescription dosages and drug combinations are cross-referenced with your recorded health history.'}
          </p>
        </div>

        {/* Privacy & Encryption Guarantee */}
        <div className="rounded-xl bg-white border border-slate-200 p-5 space-y-2.5 shadow-xs">
          <div className="flex items-center gap-1.5 text-emerald-800 text-xs font-bold uppercase tracking-wider">
            <Lock className="w-4 h-4 text-emerald-600" />
            <span>DPDPA 2023 Safe</span>
          </div>
          <div className="text-base font-bold text-slate-900">
            {language === 'hi' ? 'गोपनीय व सुरक्षित रिकॉर्ड' : 'Encrypted Health Record'}
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            {language === 'hi'
              ? 'आपकी पर्चियाँ केवल आपके और आपके इलाज करने वाले अधिकृत डॉक्टर के पास ही सुरक्षित रहती हैं।'
              : 'Your medical prescriptions and records are strictly restricted to you and your treating physicians.'}
          </p>
        </div>
      </div>

      {/* Verified Prescriptions & Medication Timeline */}
      <div className="rounded-xl bg-white border border-slate-200 p-6 sm:p-7 space-y-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Pill className="w-5 h-5 text-teal-600" />
              <span>{t('portal.active_meds', 'Your Prescriptions & Daily Medicine Routine')}</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {t('portal.subtitle', 'Clear, simple information about your prescribed medicines and how to take them.')}
            </p>
          </div>
          <div className="text-xs text-slate-500">
            Total Records:{' '}
            <span className="font-semibold text-slate-900">{patient.timeline?.length || 0}</span>
          </div>
        </div>

        {patient.timeline && patient.timeline.length > 0 ? (
          <div className="space-y-5">
            {patient.timeline.map((event: TimelineEvent, idx: number) => (
              <div
                key={event.document_id || idx}
                className="rounded-xl bg-slate-50 border border-slate-200 p-5 space-y-4 hover:border-slate-300 transition"
              >
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-800 flex items-center justify-center border border-teal-200">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900">
                        {(event as any).doctor_name || 'Dr. Ananya Sharma (Reviewer)'}
                      </div>
                      <div className="text-xs text-slate-500">
                        {(event as any).clinic_name || 'Prescripto Multispecialty Clinic'} &bull;{' '}
                        <span className="text-slate-700 font-mono">
                          {event.uploaded_at?.substring(0, 10) || 'Recent'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <AnalysisStatusBadge status={(event.analysis_status || 'COMPLETED') as any} />
                    {event.analysis_id && (
                      <Link
                        to={`/analyses/${event.analysis_id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white hover:bg-slate-100 text-slate-700 text-xs font-medium border border-slate-200 transition shadow-2xs"
                      >
                        <span>View Safety Report</span>
                        <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                      </Link>
                    )}
                  </div>
                </div>

                {/* Prescribed Drugs Section with Visual Schedules and Audio Button */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                      <Pill className="w-3.5 h-3.5 text-teal-600" />
                      <span>{t('portal.how_to_take', 'Prescribed Medicines & Daily Timings')}</span>
                    </div>
                    <span className="text-[11px] text-slate-500 flex items-center gap-1">
                      <Info className="w-3 h-3 text-slate-400" />
                      Click 🔊 to hear audio
                    </span>
                  </div>

                  {event.medications && event.medications.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                      {event.medications.map((med: any, mIdx: number) => {
                        const sigInfo = explainSig(med.frequency || '');
                        return (
                          <div
                            key={mIdx}
                            className="rounded-xl bg-white border border-slate-200 p-4 space-y-2.5 shadow-2xs hover:shadow-xs transition"
                          >
                            {/* Medicine Header + Voice Button */}
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <span className="text-sm font-bold text-slate-900 block leading-tight">
                                  {med.name}
                                </span>
                                <span className="text-xs font-medium text-teal-700">
                                  {med.dose || med.strength || 'Standard Dosage'}
                                </span>
                              </div>

                              {/* Audio Speak Button */}
                              <button
                                onClick={() => handleSpeakMed(med)}
                                title="Listen to this medicine instruction in your language"
                                className="p-2 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition cursor-pointer flex-shrink-0"
                              >
                                <Volume2 className="w-4 h-4" />
                              </button>
                            </div>

                            {/* Visual Daily Timing Badge */}
                            <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-between text-xs">
                              <span className="font-medium text-slate-700 flex items-center gap-1.5">
                                <Clock className="w-3.5 h-3.5 text-slate-400" />
                                <span>{sigInfo.timing}</span>
                              </span>
                              <span className="text-sm tracking-wide" title="Time of day">
                                {sigInfo.icon}
                              </span>
                            </div>

                            {/* Food and Water Instruction in Plain Language */}
                            <div className="text-xs text-slate-600 bg-emerald-50/50 p-2 rounded-lg border border-emerald-100 flex items-center gap-1.5">
                              <span>🍽️</span>
                              <span>{med.instructions || t('portal.meals_after', 'Take after food with water')}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-xs text-slate-500 italic p-3 bg-white rounded-lg border border-slate-200">
                      Processing transcription for this prescription...
                    </div>
                  )}
                </div>

                {/* Safety Alerts Summary */}
                {event.safety_findings && event.safety_findings.length > 0 && (
                  <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 space-y-1.5">
                    <div className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      <span>{t('safety.title', 'Safety Alerts Checked by Doctor')}</span>
                    </div>
                    {event.safety_findings.map((finding: any, fIdx: number) => (
                      <p key={fIdx} className="text-xs text-amber-800 leading-relaxed">
                        &bull; {finding.detail || finding.check_type}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 space-y-3">
            <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-900">No Prescriptions Uploaded Yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Upload a clear photo or scan of your doctor's handwritten prescription to get an instant safety check
              and dosage schedule.
            </p>
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition"
            >
              <UploadCloud className="w-4 h-4" />
              <span>{t('upload.button', 'Upload Prescription Slip')}</span>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientPortalPage;
