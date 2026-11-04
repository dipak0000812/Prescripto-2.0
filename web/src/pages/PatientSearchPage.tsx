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
  Loader2,
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
      setCreateSuccessMsg(`Registered patient ${created.name} (${created.patient_id}) successfully!`);
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
            <div className="w-10 h-10 rounded-xl bg-[#0F5147] text-white flex items-center justify-center font-bold shadow-2xs">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-[#1C252E] tracking-tight flex items-center gap-2">
                Patient Records & Medical History
              </h1>
              <p className="text-xs text-stone-500 font-medium mt-0.5">
                Instant clinician search across patient names, IDs, prescriptions, and historical reports
              </p>
            </div>
          </div>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={() => setShowCreateModal(true)}
          leftIcon={<UserPlus className="w-4 h-4 text-white" />}
          className="min-h-[40px] bg-[#0F5147] hover:bg-[#0A3831]"
        >
          Register New Patient
        </Button>
      </div>

      {/* Success Notification */}
      {createSuccessMsg && (
        <div className="p-3.5 bg-[#ECFDF5] border border-[#A7F3D0] rounded-2xl text-xs text-[#065F46] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-[#047857] shrink-0" />
            <span className="font-semibold">{createSuccessMsg}</span>
          </div>
          <button
            onClick={() => setCreateSuccessMsg(null)}
            className="text-[#065F46] hover:text-[#047857] p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search Bar & Quick Filters */}
      <div className="bg-white border border-stone-200 rounded-2xl p-4 shadow-2xs space-y-3">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-stone-400">
            <Search className="w-4 h-4 text-[#0F5147]" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search patients"
            placeholder="Search by patient name, reference, or phone number..."
            className="w-full pl-10 pr-10 py-2.5 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition font-medium"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-stone-400 hover:text-stone-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Patient Cards Grid */}
      {isLoading ? (
        <div className="py-20 text-center bg-white border border-stone-200 rounded-2xl shadow-xs">
          <RefreshCw className="w-8 h-8 text-[#0F5147] animate-spin mx-auto mb-3" />
          <p className="text-xs font-semibold text-stone-700">Searching patient database...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-[#FFE4E6] border border-[#FDA4AF] rounded-2xl text-xs text-[#881337] flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-[#BE123C] shrink-0" />
          <span>{error}</span>
        </div>
      ) : patients.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-2xl p-12 text-center shadow-xs">
          <Users className="w-12 h-12 text-stone-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-[#1C252E]">No matching patients found</h3>
          <p className="text-xs text-stone-500 mt-1 max-w-sm mx-auto">
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
            className="mt-4 min-h-[40px] bg-[#0F5147] hover:bg-[#0A3831]"
          >
            Add Patient &ldquo;{searchQuery}&rdquo;
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {patients.map((patient) => (
            <div
              key={patient.id}
              className="bg-white border border-stone-200 rounded-2xl p-5 shadow-2xs hover:border-stone-300 transition group flex flex-col justify-between"
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-[#E6F0EE] text-[#0F5147] font-bold flex items-center justify-center text-sm shadow-2xs border border-[#9DC1BB]">
                      {patient.name.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-[#1C252E] group-hover:text-[#0F5147] transition leading-snug">
                        {patient.name}
                      </h3>
                      <span className="inline-block text-[11px] font-mono font-semibold text-[#0F5147] bg-[#E6F0EE] px-2 py-0.5 rounded-md border border-[#9DC1BB] mt-0.5">
                        {patient.patient_id}
                      </span>
                    </div>
                  </div>

                  {patient.blood_group && (
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-[#FFE4E6] text-[#881337] border border-[#FDA4AF]">
                      {patient.blood_group}
                    </span>
                  )}
                </div>

                {/* Patient Specs */}
                <div className="space-y-2 py-3 border-y border-stone-100 text-xs text-stone-600">
                  <div className="flex items-center justify-between">
                    <span className="text-stone-500">Age / Gender:</span>
                    <span className="font-semibold text-stone-800">
                      {patient.age ? `${patient.age} yrs` : 'Not specified'} {patient.gender && `• ${patient.gender}`}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-stone-500 flex items-center gap-1">
                      <Phone className="w-3.5 h-3.5 text-stone-400" /> Mobile:
                    </span>
                    <span className="font-mono font-semibold text-stone-800">+91 {patient.phone_number}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-stone-500 flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5 text-stone-400" /> Prescriptions:
                    </span>
                    <span className="inline-flex items-center gap-1 font-semibold text-[#0F5147] bg-[#E6F0EE] px-2 py-0.5 rounded-md border border-[#9DC1BB]">
                      {patient.prescriptions_count} {patient.prescriptions_count === 1 ? 'Report' : 'Reports'}
                    </span>
                  </div>

                  {patient.latest_visit && (
                    <div className="flex items-center justify-between">
                      <span className="text-stone-500 flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-stone-400" /> Last Consultation:
                      </span>
                      <span className="font-medium text-stone-700">
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
                className="mt-4 w-full py-2.5 px-3 rounded-xl bg-stone-50 hover:bg-[#E6F0EE] text-stone-700 hover:text-[#0F5147] text-xs font-semibold border border-stone-200 hover:border-[#9DC1BB] transition flex items-center justify-center gap-1.5"
              >
                <span>View Medical Timeline</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ================= REGISTER PATIENT MODAL ================= */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-7 shadow-xl border border-stone-200 animate-in zoom-in-95 text-left">
            <div className="flex items-center justify-between pb-3 border-b border-stone-200">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-xl bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center border border-[#9DC1BB]">
                  <UserPlus className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-extrabold text-[#1C252E]">Register New Patient</h3>
                  <p className="text-[11px] text-stone-500">Create a clinical record for prescription linking</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-lg text-stone-400 hover:bg-stone-100 hover:text-stone-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePatient} className="mt-4 space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wider mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Enter patient full name"
                  className="w-full px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wider mb-1">
                    Mobile Number *
                  </label>
                  <input
                    type="tel"
                    required
                    maxLength={10}
                    value={newPhone}
                    onChange={(e) => setNewPhone(e.target.value.replace(/\D/g, ''))}
                    placeholder="10-digit mobile"
                    className="w-full px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wider mb-1">
                    Age
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={newAge}
                    onChange={(e) => setNewAge(e.target.value)}
                    placeholder="e.g. 45"
                    className="w-full px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wider mb-1">
                    Gender
                  </label>
                  <select
                    value={newGender}
                    onChange={(e) => setNewGender(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition font-medium"
                  >
                    <option value="">Not provided</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wider mb-1">
                    Blood Group
                  </label>
                  <select
                    value={newBloodGroup}
                    onChange={(e) => setNewBloodGroup(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition font-medium"
                  >
                    <option value="">Not provided</option>
                    {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((bg) => (
                      <option key={bg} value={bg}>{bg}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wider mb-1">
                  Known Drug Allergies
                </label>
                <input
                  type="text"
                  value={newAllergies}
                  onChange={(e) => setNewAllergies(e.target.value)}
                  placeholder="e.g. Penicillin, Sulfa drugs"
                  className="w-full px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 uppercase tracking-wider mb-1">
                  Medical History Summary
                </label>
                <textarea
                  rows={2}
                  value={newHistory}
                  onChange={(e) => setNewHistory(e.target.value)}
                  placeholder="e.g. Type 2 Diabetes, Mild Hypertension"
                  className="w-full px-3 py-2 text-xs bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus:outline-hidden focus:ring-2 focus:ring-[#0F5147] transition resize-none"
                />
              </div>

              <div className="pt-3 flex items-center justify-end gap-2 border-t border-stone-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCreateModal(false)}
                  className="min-h-[40px]"
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
                  className="min-h-[40px] bg-[#0F5147] hover:bg-[#0A3831]"
                >
                  Save Patient Record
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
