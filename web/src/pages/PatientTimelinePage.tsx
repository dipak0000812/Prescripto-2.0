import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Calendar,
  AlertTriangle,
  ShieldAlert,
  FileText,
  ArrowLeft,
  UploadCloud,
  AlertCircle,
  ExternalLink,
  Activity,
  RefreshCw,
} from 'lucide-react';
import { getPatientTimelineApi, PatientDetail } from '../api/patients';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

export const PatientTimelinePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { session } = useAuth();
  const { t } = useLanguage();

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Prevent a patient session from navigating to another patient's record.
  const isPatientRestricted = session?.is_patient && session?.patient_id !== id;

  useEffect(() => {
    if (!id || isPatientRestricted) return;
    const fetchTimeline = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getPatientTimelineApi(id);
        setPatient(data);
      } catch (err: any) {
        setError(err?.response?.data?.detail || err?.message || 'Failed to load patient medical history');
      } finally {
        setIsLoading(false);
      }
    };
    fetchTimeline();
  }, [id, isPatientRestricted]);

  if (isPatientRestricted) {
    return (
      <div className="max-w-xl mx-auto my-16 bg-white border border-stone-200 rounded-2xl p-8 text-center shadow-2xs space-y-4">
        <ShieldAlert className="w-12 h-12 text-red-600 mx-auto" />
        <h3 className="text-base font-bold text-ink">Patient record access restricted</h3>
        <p className="text-xs text-ink-muted leading-relaxed">
          This account can only open its linked patient record.
        </p>
        <Link to="/patient-portal">
          <Button variant="primary" size="md" className="mt-2 min-h-[48px]">
            Return to health portal
          </Button>
        </Link>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="py-20 text-center bg-white border border-stone-200 rounded-2xl shadow-2xs">
        <RefreshCw className="w-8 h-8 text-brand animate-spin mx-auto mb-3" />
        <h3 className="text-sm font-bold text-ink">Loading patient medical timeline…</h3>
        <p className="text-xs text-ink-muted mt-1">Loading the record and linked prescription details.</p>
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="max-w-xl mx-auto my-12 bg-white border border-stone-200 rounded-2xl p-8 text-center shadow-2xs space-y-4">
        <AlertCircle className="w-12 h-12 text-red-600 mx-auto" />
        <h3 className="text-base font-bold text-ink">Patient record not found</h3>
        <p className="text-xs text-ink-muted">{error || 'Unable to locate patient record with identifier: ' + id}</p>
        <Button
          variant="outline"
          size="md"
          onClick={() => navigate(session?.is_patient ? '/patient-portal' : '/patients')}
          className="min-h-[48px]"
        >
          Back
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-left animate-in fade-in duration-150">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-stone-200">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(session?.is_patient ? '/patient-portal' : '/patients')}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
            className="min-h-[40px] px-3"
          >
            <span>Back</span>
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-ink-muted">Patient medical record</span>
              <span className="text-stone-300">•</span>
              <span className="text-xs font-mono font-bold text-brand bg-brand-soft px-2 py-0.5 rounded-md border border-brand/20">
                {patient.patient_id}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-ink tracking-tight mt-0.5">
              {patient.name}
            </h1>
          </div>
        </div>

        <Link to={`/upload?patient_ref=${encodeURIComponent(patient.patient_id)}`}>
          <Button
            variant="primary"
            size="md"
            leftIcon={<UploadCloud className="w-4 h-4 text-white" />}
            className="min-h-[48px]"
          >
            Upload prescription for {patient.name.split(' ')[0]}
          </Button>
        </Link>
      </div>

      {/* Patient Profile Header Card */}
      <div className="bg-white border border-stone-200 rounded-2xl p-6 sm:p-7 shadow-2xs">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Col 1: Bio */}
          <div className="md:col-span-1 flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-brand-soft text-brand font-bold text-lg flex items-center justify-center border border-brand/20 shrink-0">
              {patient.name.substring(0, 2).toUpperCase()}
            </div>
            <div>
              <h2 className="text-base font-bold text-ink">{patient.name}</h2>
              <div className="text-xs text-ink-muted mt-0.5 space-y-0.5">
                <div>
                  <strong className="text-ink font-medium">{patient.age || '—'} yrs</strong> • {patient.gender || 'Not specified'}
                </div>
                <div className="font-mono text-ink">
                  +91 {patient.phone_number}
                </div>
              </div>
              {patient.blood_group && (
                <span className="inline-block mt-2 text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-red-50 text-red-800 border border-red-200">
                  Blood group: {patient.blood_group}
                </span>
              )}
            </div>
          </div>

          {/* Col 2: Allergies */}
          <div className="md:col-span-1 bg-red-50/50 border border-red-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-red-800 font-bold text-xs mb-2">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              <span>Drug allergies</span>
            </div>
            {patient.allergies ? (
              <div className="text-xs font-semibold text-red-900 bg-white p-2.5 rounded-lg border border-red-200 leading-snug">
                {patient.allergies}
              </div>
            ) : (
              <span className="text-xs text-ink-muted italic">No known drug allergies reported</span>
            )}
            <p className="text-[11px] text-ink-muted mt-2">
              Checked during automated safety screening against prescribed medications.
            </p>
          </div>

          {/* Col 3: Medical History */}
          <div className="md:col-span-1 bg-paper border border-stone-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-brand font-bold text-xs mb-2">
              <Activity className="w-4 h-4 text-brand" />
              <span>Medical history</span>
            </div>
            <p className="text-xs text-ink leading-relaxed">
              {patient.medical_history || 'No chronic conditions or past surgical history recorded.'}
            </p>
          </div>

          {/* Col 4: Summary Stats */}
          <div className="md:col-span-1 flex flex-col justify-between bg-brand-soft/60 border border-brand/20 rounded-xl p-4 text-xs">
            <div>
              <span className="text-[11px] font-semibold text-brand block">
                Prescription records
              </span>
              <div className="text-2xl font-bold text-brand mt-1">
                {patient.total_prescriptions}
              </div>
              <span className="text-[11px] text-ink-muted">
                Documents on file
              </span>
            </div>
            {patient.emergency_contact && (
              <div className="pt-2 border-t border-brand/20 mt-2 text-[11px] text-ink-muted">
                <span className="text-stone-500 block text-[10px] font-semibold">Emergency contact:</span>
                <span className="font-medium text-ink">{patient.emergency_contact}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Historical Encounter Timeline */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-bold text-ink">Clinical timeline & historical visits</h3>
          <p className="text-xs text-ink-muted">Chronological history of all prescriptions, extractions, and doctor reviews</p>
        </div>

        {patient.timeline.length === 0 ? (
          <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-2xs">
            <FileText className="w-12 h-12 text-stone-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-ink">No prescriptions on record</h3>
            <p className="text-xs text-ink-muted mt-1 max-w-sm mx-auto">
              This patient has no scanned prescription reports yet. Upload a prescription image to start their medical record timeline.
            </p>
            <Link to={`/upload?patient_ref=${encodeURIComponent(patient.patient_id)}`}>
              <Button variant="primary" size="md" className="mt-4 min-h-[48px]">
                Upload first prescription
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {patient.timeline.map((event, index) => {
              const isCompleted = event.analysis_status === 'COMPLETED' || event.analysis_status === 'REVIEWED_COMPLETE';

              return (
                <article
                  key={event.document_id}
                  className="bg-white border border-stone-200 rounded-2xl p-6 shadow-2xs hover:border-stone-300 transition"
                >
                  {/* Event Top Bar */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-stone-100">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-brand-soft border border-brand/20 text-brand flex items-center justify-center font-bold text-xs">
                        #{patient.timeline.length - index}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-ink">
                            Prescription encounter
                          </span>
                          <Badge variant={isCompleted ? 'success' : 'warning'} dot>
                            {isCompleted ? 'Completed' : 'Needs check'}
                          </Badge>
                        </div>
                        <div className="text-xs text-ink-muted mt-0.5 flex items-center gap-2">
                          <Calendar className="w-3.5 h-3.5 text-stone-400" />
                          <span>
                            {new Date(event.uploaded_at).toLocaleDateString('en-IN', {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                          {event.file_name && (
                            <>
                              <span>•</span>
                              <span className="font-mono text-stone-400">{event.file_name}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {event.analysis_id && (
                      <Link to={`/analyses/${event.analysis_id}`}>
                        <Button
                          variant="outline"
                          size="sm"
                          rightIcon={<ExternalLink className="w-3.5 h-3.5 text-brand" />}
                          className="min-h-[40px] text-xs font-semibold text-brand"
                        >
                          View medicines & schedule
                        </Button>
                      </Link>
                    )}
                  </div>

                  {/* Event Content: Medications Grid */}
                  {event.medications.length > 0 && (
                    <div className="mt-4 space-y-2">
                      <span className="text-[11px] font-semibold text-ink-muted block">
                        Prescribed medications ({event.medications.length}):
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                        {event.medications.map((m, mIdx) => (
                          <div
                            key={mIdx}
                            className="p-3 bg-paper border border-stone-200 rounded-xl text-xs space-y-1"
                          >
                            <div className="flex items-start justify-between gap-1">
                              <span className="font-bold text-ink truncate">{m.name}</span>
                              {m.strength && (
                                <span className="font-mono text-[11px] font-semibold text-brand bg-white px-1.5 py-0.5 rounded border border-stone-200 shrink-0">
                                  {m.strength}
                                </span>
                              )}
                            </div>
                            <div className="text-ink-muted text-[11px]">
                              {m.dose || ''} {m.frequency ? `(${m.frequency})` : ''}
                            </div>
                            {m.instructions && (
                              <div className="text-[10px] text-stone-400 italic">
                                {m.instructions}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Safety Warnings if any */}
                  {event.safety_findings.length > 0 && (
                    <div className="mt-4 p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl text-xs space-y-2">
                      <span className="text-[11px] font-bold text-amber-900 flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4 text-amber-700" />
                        Safety notices ({event.safety_findings.length}):
                      </span>
                      <div className="space-y-1">
                        {event.safety_findings.map((f, fIdx) => (
                          <div key={fIdx} className="text-ink bg-white p-2 rounded-lg border border-amber-200">
                            <strong>{f.check_type.replace(/_/g, ' ')}:</strong> {f.detail}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientTimelinePage;
