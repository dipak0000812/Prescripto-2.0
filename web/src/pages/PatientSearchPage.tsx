import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Search,
  PlusCircle,
  FileText,
  Phone,
  Calendar,
  ArrowRight,
  AlertCircle,
  UserPlus,
  X,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import { searchPatientsApi, createPatientApi, PatientSummary } from '../api/patients';
import { Button } from '../components/ui/Button';

export const PatientSearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // New Patient Modal State
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newName, setNewName] = useState<string>('');
  const [newPhone, setNewPhone] = useState<string>('');
  const [newAge, setNewAge] = useState<string>('');
  const [newGender, setNewGender] = useState<string>('');
  const [newBloodGroup, setNewBloodGroup] = useState<string>('');
  const [newAllergies, setNewAllergies] = useState<string>('');
  const [newHistory, setNewHistory] = useState<string>('');
  const [isSubmittingNew, setIsSubmittingNew] = useState<boolean>(false);
  const [createSuccessMsg, setCreateSuccessMsg] = useState<string | null>(null);

  const fetchPatients = async (query: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await searchPatientsApi(query);
      setPatients(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to search patients');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchPatients(searchQuery);
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleCreatePatient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || !newPhone.trim()) {
      setError('Please provide at least a Patient Name and Mobile Number.');
      return;
    }
    setIsSubmittingNew(true);
    try {
      const created = await createPatientApi({
        name: newName.trim(),
        phone_number: newPhone.trim(),
        age: newAge ? parseInt(newAge, 10) : undefined,
        gender: newGender || undefined,
        blood_group: newBloodGroup || undefined,
        allergies: newAllergies.trim() || undefined,
        medical_history: newHistory.trim() || undefined,
      });
      setShowCreateModal(false);
      setCreateSuccessMsg(`Registered patient ${created.name} (${created.patient_id}) successfully.`);
      // Reset form
      setNewName('');
      setNewPhone('');
      setNewAge('');
      setNewGender('');
      setNewBloodGroup('');
      setNewAllergies('');
      setNewHistory('');
      fetchPatients('');
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to register patient');
    } finally {
      setIsSubmittingNew(false);
    }
  };

  return (
    <div className="space-y-6 text-left animate-in fade-in duration-150">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand flex items-center justify-center font-bold">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-ink tracking-tight">
                Patient records
              </h1>
              <p className="text-xs text-ink-muted mt-0.5">
                Search patients by name, mobile number, or record ID
              </p>
            </div>
          </div>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() => setShowCreateModal(true)}
          leftIcon={<UserPlus className="w-4 h-4 text-white" />}
          className="min-h-[40px]"
        >
          Register new patient
        </Button>
      </div>

      {/* Success Notification */}
      {createSuccessMsg && (
        <div className="p-3.5 bg-brand-soft border border-brand/20 rounded-2xl text-xs text-brand-dark flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-brand shrink-0" />
            <span className="font-semibold">{createSuccessMsg}</span>
          </div>
          <button
            onClick={() => setCreateSuccessMsg(null)}
            className="text-brand hover:text-brand-dark p-1 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search Bar */}
      <div className="bg-white border border-stone-200 rounded-2xl p-4 shadow-2xs">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-stone-400">
            <Search className="w-4 h-4 text-brand" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search patients"
            placeholder="Search by patient name, mobile number, or ID (PAT-…)"
            className="w-full pl-10 pr-10 py-2.5 text-xs bg-paper border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand focus:bg-white transition"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-stone-400 hover:text-stone-600 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Patient Cards Grid */}
      {isLoading ? (
        <div className="py-20 text-center bg-white border border-stone-200 rounded-2xl shadow-2xs">
          <RefreshCw className="w-8 h-8 text-brand animate-spin mx-auto mb-3" />
          <p className="text-xs font-semibold text-ink-muted">Searching patient records…</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-800 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      ) : patients.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-2xs">
          <Users className="w-12 h-12 text-stone-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-ink">No matching patients found</h3>
          <p className="text-xs text-ink-muted mt-1 max-w-sm mx-auto">
            No patient records match &ldquo;{searchQuery}&rdquo;. You can register this patient directly to track their prescriptions.
          </p>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setNewName(searchQuery);
              setShowCreateModal(true);
            }}
            leftIcon={<PlusCircle className="w-4 h-4 text-white" />}
            className="mt-4 min-h-[44px]"
          >
            Add patient &ldquo;{searchQuery}&rdquo;
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {patients.map((patient) => (
            <div
              key={patient.id}
              className="bg-white border border-stone-200 rounded-2xl p-5 shadow-2xs hover:border-stone-300 transition group flex flex-col justify-between"
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-brand-soft text-brand font-bold flex items-center justify-center text-sm border border-brand/20">
                      {patient.name.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-ink group-hover:text-brand transition leading-snug">
                        {patient.name}
                      </h3>
                      <span className="inline-block text-[11px] font-mono font-semibold text-brand bg-brand-soft px-2 py-0.5 rounded-md border border-brand/20 mt-0.5">
                        {patient.patient_id}
                      </span>
                    </div>
                  </div>

                  {patient.blood_group && (
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-red-50 text-red-800 border border-red-200">
                      {patient.blood_group}
                    </span>
                  )}
                </div>

                {/* Patient Specs */}
                <div className="space-y-2 py-3 border-y border-stone-100 text-xs text-ink-muted">
                  <div className="flex items-center justify-between">
                    <span className="text-stone-500">Age / Gender:</span>
                    <span className="font-semibold text-ink">
                      {patient.age ? `${patient.age} yrs` : 'Not specified'} {patient.gender && `• ${patient.gender}`}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-stone-500 flex items-center gap-1">
                      <Phone className="w-3.5 h-3.5 text-stone-400" /> Mobile:
                    </span>
                    <span className="font-mono font-semibold text-ink">+91 {patient.phone_number}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-stone-500 flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5 text-stone-400" /> Prescriptions:
                    </span>
                    <span className="inline-flex items-center gap-1 font-semibold text-brand bg-brand-soft px-2 py-0.5 rounded-md border border-brand/20">
                      {patient.prescriptions_count} {patient.prescriptions_count === 1 ? 'Report' : 'Reports'}
                    </span>
                  </div>

                  {patient.latest_visit && (
                    <div className="flex items-center justify-between">
                      <span className="text-stone-500 flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-stone-400" /> Last visit:
                      </span>
                      <span className="font-medium text-ink">
                        {new Date(patient.latest_visit).toLocaleDateString('en-IN', {
                          day: 'numeric',
                          month: 'short',
                          year: 'numeric',
                        })}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => navigate(`/patients/${patient.patient_id}`)}
                className="mt-4 w-full py-2.5 px-3 rounded-xl bg-paper hover:bg-brand-soft text-ink hover:text-brand text-xs font-semibold border border-stone-200 hover:border-brand/30 transition flex items-center justify-center gap-1.5 cursor-pointer min-h-[44px]"
              >
                <span>View medical history</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ================= REGISTER PATIENT MODAL ================= */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-stone-900/40 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white rounded-t-3xl sm:rounded-2xl max-w-lg w-full p-6 sm:p-7 shadow-xl border border-stone-200 animate-in zoom-in-95 text-left max-h-[92vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-stone-200">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand flex items-center justify-center border border-brand/20">
                  <UserPlus className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-ink">Register new patient</h3>
                  <p className="text-xs text-ink-muted">Create a clinical record for prescription linking</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-xl text-stone-400 hover:bg-stone-100 hover:text-stone-700 min-h-[40px] min-w-[40px] flex items-center justify-center cursor-pointer"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePatient} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-ink-muted mb-1">
                  Full name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Enter patient full name"
                  className="w-full px-3.5 py-2.5 text-xs bg-white border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand transition min-h-[44px]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-ink-muted mb-1">
                    Mobile number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    required
                    maxLength={10}
                    value={newPhone}
                    onChange={(e) => setNewPhone(e.target.value.replace(/\D/g, ''))}
                    placeholder="10-digit mobile"
                    className="w-full px-3.5 py-2.5 text-xs bg-white border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand transition font-mono min-h-[44px]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-muted mb-1">
                    Age
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={newAge}
                    onChange={(e) => setNewAge(e.target.value)}
                    placeholder="e.g. 45"
                    className="w-full px-3.5 py-2.5 text-xs bg-white border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand transition min-h-[44px]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-ink-muted mb-1">
                    Gender
                  </label>
                  <select
                    value={newGender}
                    onChange={(e) => setNewGender(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl text-ink focus:outline-none focus:ring-2 focus:ring-brand transition font-medium min-h-[44px]"
                  >
                    <option value="">Not provided</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-ink-muted mb-1">
                    Blood group
                  </label>
                  <select
                    value={newBloodGroup}
                    onChange={(e) => setNewBloodGroup(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl text-ink focus:outline-none focus:ring-2 focus:ring-brand transition font-medium min-h-[44px]"
                  >
                    <option value="">Not provided</option>
                    {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((bg) => (
                      <option key={bg} value={bg}>{bg}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink-muted mb-1">
                  Known drug allergies
                </label>
                <input
                  type="text"
                  value={newAllergies}
                  onChange={(e) => setNewAllergies(e.target.value)}
                  placeholder="e.g. Penicillin, Sulfa drugs"
                  className="w-full px-3.5 py-2.5 text-xs bg-white border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand transition min-h-[44px]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ink-muted mb-1">
                  Medical history summary
                </label>
                <textarea
                  rows={2}
                  value={newHistory}
                  onChange={(e) => setNewHistory(e.target.value)}
                  placeholder="e.g. Type 2 Diabetes, Mild Hypertension"
                  className="w-full px-3.5 py-2.5 text-xs bg-white border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand transition resize-none"
                />
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-stone-100">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowCreateModal(false)}
                  className="min-h-[44px]"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isSubmittingNew}
                  isLoading={isSubmittingNew}
                  leftIcon={<CheckCircle2 className="w-4 h-4 text-white" />}
                  className="min-h-[44px]"
                >
                  Save patient record
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientSearchPage;
