import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  User,
  Phone,
  Calendar,
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  FileText,
  Pill,
  ArrowLeft,
  UploadCloud,
  Loader2,
  AlertCircle,
  ExternalLink,
  Activity,
  Check,
} from 'lucide-react';
import { getPatientTimelineApi, PatientDetail } from '../api/patients';
import { AnalysisStatusBadge } from '../components/Badges';
import { useAuth } from '../context/AuthContext';

export const PatientTimelinePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { session } = useAuth();

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Security & Privacy Guard (DPDPA 2023)
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
      <div className="max-w-xl mx-auto my-16 bg-white border border-rose-200 rounded-2xl p-8 text-center shadow-xs space-y-4">
        <ShieldAlert className="w-12 h-12 text-rose-500 mx-auto" />
        <h3 className="text-base font-bold text-slate-900">Confidential Medical Dossier</h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          In strict compliance with India DPDPA 2023 healthcare privacy regulations, patient accounts are restricted
          from viewing records of other individuals.
        </p>
        <button
          onClick={() => navigate('/patient-portal')}
          className="mt-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold transition"
        >
          Return to My Health Portal
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="py-20 text-center bg-white border border-slate-200 rounded-xl shadow-xs">
        <Loader2 className="w-8 h-8 text-teal-600 animate-spin mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-slate-900">Loading Patient Medical Timeline...</h3>
        <p className="text-xs text-slate-500 mt-1">Aggregating historical prescriptions, normalized medications, and safety checks</p>
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="max-w-xl mx-auto my-12 bg-white border border-rose-200 rounded-2xl p-8 text-center shadow-xs space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h3 className="text-base font-bold text-slate-900">Patient Record Not Found</h3>
        <p className="text-xs text-slate-500">{error || 'Unable to locate patient record with identifier: ' + id}</p>
        <button
          onClick={() => navigate(session?.is_patient ? '/patient-portal' : '/patients')}
          className="px-4 py-2 bg-slate-100 text-slate-700 border border-slate-300 rounded-lg text-xs font-medium hover:bg-slate-200 transition"
        >
          Back
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(session?.is_patient ? '/patient-portal' : '/patients')}
            className="p-2 rounded-lg bg-white border border-slate-300 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition shadow-2xs"
            title="Back"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500">Patient Medical Record</span>
              <span className="text-slate-300">•</span>
              <span className="text-xs font-mono font-semibold text-teal-800 bg-teal-50 px-2 py-0.5 rounded-md border border-teal-200">
                {patient.patient_id}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-0.5">
              {patient.name}
            </h1>
          </div>
        </div>

        <button
          onClick={() => navigate(`/upload?patient_ref=${encodeURIComponent(patient.patient_id)}`)}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload Prescription for {patient.name.split(' ')[0]}</span>
        </button>
      </div>

      {/* Patient Profile Header Card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 sm:p-7 shadow-xs">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Col 1: Bio */}
          <div className="md:col-span-1 flex items-start gap-4">
            <div className="w-14 h-14 rounded-xl bg-teal-50 text-teal-800 font-bold text-lg flex items-center justify-center border border-teal-200 shrink-0">
              {patient.name.substring(0, 2).toUpperCase()}
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">{patient.name}</h2>
              <div className="text-xs text-slate-500 mt-0.5 space-y-0.5">
                <div>
                  <strong className="text-slate-800 font-medium">{patient.age || '—'} yrs</strong> • {patient.gender || 'Not specified'}
                </div>
                <div className="font-mono text-slate-600">
                  +91 {patient.phone_number}
                </div>
              </div>
              {patient.blood_group && (
                <span className="inline-block mt-2 text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-rose-50 text-rose-800 border border-rose-200">
                  Blood Group: {patient.blood_group}
                </span>
              )}
            </div>
          </div>

          {/* Col 2: Clinical Allergies & Critical Flags */}
          <div className="md:col-span-1 bg-rose-50/70 border border-rose-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-rose-800 font-bold text-xs uppercase tracking-wider mb-2">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              <span>Drug Allergies</span>
            </div>
            {patient.allergies ? (
              <div className="text-xs font-semibold text-rose-900 bg-white p-2.5 rounded-lg border border-rose-200 leading-snug">
                {patient.allergies}
              </div>
            ) : (
              <span className="text-xs text-slate-500 italic">No known drug allergies reported</span>
            )}
            <p className="text-[11px] text-rose-700 mt-2 font-medium">
              Checked during automated safety screening against prescribed medications.
            </p>
          </div>

          {/* Col 3: Medical History */}
          <div className="md:col-span-1 bg-slate-50 border border-slate-200 rounded-xl p-4">
            <div className="flex items-center gap-2 text-teal-800 font-bold text-xs uppercase tracking-wider mb-2">
              <Activity className="w-4 h-4 text-teal-600" />
              <span>Medical History</span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed font-medium">
              {patient.medical_history || 'No chronic conditions or past surgical history recorded.'}
            </p>
          </div>

          {/* Col 4: Summary Stats */}
          <div className="md:col-span-1 flex flex-col justify-between bg-teal-50/60 border border-teal-200 rounded-xl p-4 text-xs">
            <div>
              <span className="text-[11px] font-bold text-teal-800 uppercase tracking-wider block">
                Prescription Records
              </span>
              <div className="text-2xl font-bold text-teal-900 mt-1">
                {patient.total_prescriptions}
              </div>
              <span className="text-[11px] text-teal-700 font-medium">
                Encounter documents analyzed
              </span>
            </div>
            {patient.emergency_contact && (
              <div className="pt-2 border-t border-teal-200 mt-2 text-[11px] text-slate-600">
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Emergency Contact:</span>
                <span className="font-medium text-slate-800">{patient.emergency_contact}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Active Medications Shelf */}
      {patient.active_medications.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-200">
                <Pill className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">Active Regimen & Medications</h3>
                <p className="text-[11px] text-slate-500">Extracted and normalized from recent prescription intake</p>
              </div>
            </div>
            <span className="text-xs font-semibold text-teal-800 bg-teal-50 px-2.5 py-1 rounded-lg border border-teal-200">
              {patient.active_medications.length} Prescribed
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-1">
            {patient.active_medications.map((med, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-slate-300 transition"
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-bold text-slate-900">{med.name}</h4>
                  {med.strength && (
                    <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-white text-teal-800 border border-slate-200">
                      {med.strength}
                    </span>
                  )}
                </div>

                <div className="mt-2 text-xs text-slate-600 space-y-1">
                  {med.frequency && (
                    <div>
                      <span className="text-slate-500">Frequency:</span> <strong className="text-slate-800 font-medium">{med.frequency}</strong>
                    </div>
                  )}
                  {med.duration && (
                    <div>
                      <span className="text-slate-500">Duration:</span> <strong className="text-slate-800 font-medium">{med.duration}</strong>
                    </div>
                  )}
                  {med.instructions && (
                    <div>
                      <span className="text-slate-500">Instructions:</span> <span className="text-slate-700 font-medium">{med.instructions}</span>
                    </div>
                  )}
                </div>

                {med.prescribed_date && (
                  <div className="mt-3 pt-2 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
                    <span>Prescribed: {med.prescribed_date}</span>
                    {med.analysis_id && (
                      <Link
                        to={`/analyses/${med.analysis_id}`}
                        className="text-teal-700 hover:text-teal-800 font-semibold inline-flex items-center gap-1"
                      >
                        View Report <ExternalLink className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Historical Encounter Timeline */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">Clinical Timeline & Historical Encounters</h3>
          <p className="text-xs text-slate-500">Chronological history of all prescriptions, extractions, and physician reviews</p>
        </div>

        {patient.timeline.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-12 text-center shadow-xs">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-slate-900">No Prescriptions On Record</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              This patient has no scanned prescription reports yet. Upload a prescription image to start their medical record timeline.
            </p>
            <button
              onClick={() => navigate(`/upload?patient_ref=${encodeURIComponent(patient.patient_id)}`)}
              className="mt-4 inline-flex items-center gap-2 px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Upload First Prescription</span>
            </button>
          </div>
        ) : (
          <div className="space-y-5">
            {patient.timeline.map((event, index) => (
              <div
                key={event.document_id}
                className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs hover:border-slate-300 transition"
              >
                {/* Event Top Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-teal-50 border border-teal-200 text-teal-800 flex items-center justify-center font-bold text-xs">
                      #{patient.timeline.length - index}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-slate-900">
                          Prescription Encounter
                        </span>
                        <AnalysisStatusBadge status={(event.analysis_status || 'PENDING') as any} />
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
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
                            <span className="font-mono text-slate-500">{event.file_name}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {event.analysis_id && (
                    <Link
                      to={`/analyses/${event.analysis_id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium rounded-lg border border-slate-200 transition"
                    >
                      <span>Open Full Analysis Report</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  )}
                </div>

                {/* Event Content: Medications Grid */}
                {event.medications.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                      Prescribed Medications Extracted ({event.medications.length}):
                    </span>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border border-slate-200 rounded-lg overflow-hidden">
                        <thead className="bg-slate-50 text-slate-600 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                          <tr>
                            <th className="py-2 px-3">Medication Name</th>
                            <th className="py-2 px-3">Strength</th>
                            <th className="py-2 px-3">Dose / Frequency</th>
                            <th className="py-2 px-3">Duration</th>
                            <th className="py-2 px-3">Instructions</th>
                            <th className="py-2 px-3">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {event.medications.map((m, mIdx) => (
                            <tr key={mIdx} className="hover:bg-slate-50/70">
                              <td className="py-2 px-3 font-semibold text-slate-900">{m.name}</td>
                              <td className="py-2 px-3 font-mono text-teal-700">{m.strength || '—'}</td>
                              <td className="py-2 px-3 text-slate-700">
                                {m.dose || ''} {m.frequency ? `(${m.frequency})` : ''}
                              </td>
                              <td className="py-2 px-3 text-slate-500">{m.duration || '—'}</td>
                              <td className="py-2 px-3 text-slate-500">{m.instructions || '—'}</td>
                              <td className="py-2 px-3">
                                {m.resolution_status === 'RESOLVED' ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                                    <Check className="w-3 h-3 text-emerald-600" /> Verified
                                  </span>
                                ) : (
                                  <span className="text-[10px] font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                                    {m.resolution_status || 'OCR Extracted'}
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Safety Screening Findings */}
                {event.safety_findings.length > 0 && (
                  <div className="mt-4 p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs space-y-2">
                    <span className="text-[11px] font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      Safety Warnings Detected ({event.safety_findings.length}):
                    </span>
                    <div className="space-y-1.5">
                      {event.safety_findings.map((f, fIdx) => (
                        <div key={fIdx} className="text-amber-900 font-medium bg-white p-2.5 rounded-lg border border-amber-200">
                          <strong>{f.check_type.replace(/_/g, ' ')}:</strong> {f.detail}
                          {f.recommendation && (
                            <div className="text-[11px] text-amber-800 mt-0.5">
                              <em>Action: {f.recommendation}</em>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Clinical Review History */}
                {event.clinical_reviews.length > 0 && (
                  <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span className="font-semibold text-emerald-900">
                        Clinically Reviewed & Approved by Doctor
                      </span>
                    </div>
                    <span className="text-[11px] text-emerald-800 font-medium">
                      {new Date(event.clinical_reviews[0].reviewed_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientTimelinePage;
