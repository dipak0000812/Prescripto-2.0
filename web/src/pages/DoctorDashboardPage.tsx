import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import {
  listDoctorPatientsApi,
  linkPatientToDoctorApi,
  unlinkPatientFromDoctorApi,
} from '../api/doctorPatients';
import { searchPatientsApi, PatientSummary } from '../api/patients';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { EmptyState } from '../components/ui/EmptyState';
import { AlertBanner } from '../components/ui/AlertBanner';
import {
  UserPlus,
  UserCheck,
  Search,
  Stethoscope,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Clock,
  PlusCircle,
  Users,
  ArrowRight,
  RefreshCw,
  X,
} from 'lucide-react';

interface LinkedPatient {
  id: string;
  patient_id: string;
  patient_name: string;
  patient_patient_id: string;
  phone_number: string;
  created_at: string;
}

export const DoctorDashboardPage: React.FC = () => {
  const { session } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [linkedPatients, setLinkedPatients] = useState<LinkedPatient[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<PatientSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [isLinking, setIsLinking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const fetchLinkedPatients = async () => {
    try {
      const data = await listDoctorPatientsApi();
      setLinkedPatients(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load linked patients.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    setIsSearching(true);
    setError(null);
    try {
      const data = await searchPatientsApi(query.trim());
      setSearchResults(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to search patients.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleLinkPatient = async (patientId: string) => {
    setIsLinking(patientId);
    setError(null);
    try {
      await linkPatientToDoctorApi(patientId);
      setSuccess(`Patient linked successfully.`);
      setSearchResults([]);
      setSearchQuery('');
      fetchLinkedPatients();
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to link patient.');
    } finally {
      setIsLinking(null);
    }
  };

  const handleUnlinkPatient = async (patientId: string, patientName: string) => {
    if (!window.confirm(`Unlink ${patientName}? You will lose access to their records.`)) return;
    setError(null);
    try {
      await unlinkPatientFromDoctorApi(patientId);
      setSuccess(`${patientName} unlinked successfully.`);
      fetchLinkedPatients();
    } catch (err: any) {
      setError(err?.message || 'Failed to unlink patient.');
    }
  };

  useEffect(() => {
    fetchLinkedPatients();
  }, []);

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="space-y-6 text-left animate-in fade-in duration-150 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-stone-200">
        <div>
          <h1 className="text-2xl font-bold text-ink tracking-tight flex items-center gap-2.5">
            <Stethoscope className="w-6 h-6 text-brand" />
            Doctor Dashboard
            <Badge variant="brand" dot>
              {session?.username}
            </Badge>
          </h1>
          <p className="text-xs text-ink-muted mt-1">
            Manage your authorized patients, review pending prescriptions, and sign off on safety findings.
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={fetchLinkedPatients}
          disabled={isLoading}
          leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-brand' : ''}`} />}
          className="min-h-[40px]"
        >
          Refresh
        </Button>
      </div>

      {/* Notifications */}
      {(error || success) && (
        <div className="mb-4">
          <AlertBanner
            type={error ? 'error' : 'success'}
            title={error ? 'Notice' : 'Saved'}
            action={
              <button
                type="button"
                onClick={clearMessages}
                className="text-xs font-semibold text-brand hover:underline flex items-center gap-1 cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
                <span>Dismiss</span>
              </button>
            }
          >
            {error || success}
          </AlertBanner>
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
        <Card className="p-4 bg-white border-stone-200 space-y-1">
          <div className="flex items-center gap-2 text-xs text-ink-muted">
            <Users className="w-4 h-4" />
            <span>Linked Patients</span>
          </div>
          <div className="text-3xl font-extrabold text-ink">{linkedPatients.length}</div>
        </Card>
        <Card className="p-4 bg-white border-stone-200 space-y-1">
          <div className="flex items-center gap-2 text-xs text-ink-muted">
            <ShieldCheck className="w-4 h-4" />
            <span>Pending Reviews</span>
          </div>
          <div className="text-3xl font-extrabold text-brand">0</div>
        </Card>
        <Card className="p-4 bg-white border-stone-200 space-y-1">
          <div className="flex items-center gap-2 text-xs text-ink-muted">
            <AlertTriangle className="w-4 h-4" />
            <span>Safety Alerts</span>
          </div>
          <div className="text-3xl font-extrabold text-amber-600">0</div>
        </Card>
        <Card className="p-4 bg-white border-stone-200 space-y-1">
          <div className="flex items-center gap-2 text-xs text-ink-muted">
            <PlusCircle className="w-4 h-4" />
            <span>New This Week</span>
          </div>
          <div className="text-3xl font-extrabold text-emerald-600">0</div>
        </Card>
      </div>

      {/* Patient Search & Linking */}
      <Card className="p-5 space-y-4 bg-white border-stone-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-ink flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-brand" />
            Add Patient to Your Care
          </h2>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by name, patient ID (PAT-…), or phone number…"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              handleSearch(e.target.value);
            }}
            className="w-full pl-10 pr-4 py-2.5 text-xs bg-paper border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand focus:bg-white transition"
            disabled={isLoading}
          />
        </div>

        {isSearching && (
          <div className="flex items-center justify-center py-4 text-xs text-stone-500">
            <RefreshCw className="w-4 h-4 text-brand animate-spin mr-2" />
            Searching patient registry…
          </div>
        )}

        {searchResults.length > 0 && (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {searchResults.map((patient) => {
              const isAlreadyLinked = linkedPatients.some(
                (lp) => lp.patient_id === patient.id
              );
              return (
                <div
                  key={patient.id}
                  className="flex items-center justify-between p-3 bg-paper border border-stone-200 rounded-xl space-x-3 min-h-[52px]"
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand font-bold text-sm flex items-center justify-center border border-brand/20 shrink-0">
                      {patient.name.substring(0, 2).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <div className="font-bold text-sm text-ink truncate">{patient.name}</div>
                      <div className="text-[11px] text-ink-muted flex items-center gap-1.5 mt-0.5">
                        <span className="font-mono bg-stone-100 px-1.5 py-0.5 rounded text-ink border border-stone-200">
                          {patient.patient_id}
                        </span>
                        <span>•</span>
                        <span className="font-mono">{patient.phone_number}</span>
                      </div>
                    </div>
                  </div>
                  {isAlreadyLinked ? (
                    <Badge variant="success" size="sm" className="shrink-0">
                      <UserCheck className="w-3.5 h-3.5 mr-1" />
                      Already Linked
                    </Badge>
                  ) : (
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => handleLinkPatient(patient.id)}
                      disabled={isLinking === patient.id}
                      className="shrink-0 min-h-[40px]"
                    >
                      {isLinking === patient.id ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          Linking…
                        </>
                      ) : (
                        <>
                          <UserPlus className="w-3.5 h-3.5" />
                          Link
                        </>
                      )}
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {searchQuery && searchResults.length === 0 && !isSearching && (
          <EmptyState
            title="No patients found"
            description="No patients matched your search. Try a different name, PAT-ID, or phone number."
          />
        )}
      </Card>

      {/* Linked Patients List */}
      <Card className="p-5 space-y-4 bg-white border-stone-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-ink flex items-center gap-2">
            <Users className="w-5 h-5 text-brand" />
            Your Authorized Patients ({linkedPatients.length})
          </h2>
        </div>

        {linkedPatients.length === 0 ? (
          <EmptyState
            title="No linked patients yet"
            description="Search for patients above and click 'Link' to add them to your care panel. You'll then be able to review their prescriptions and sign off on safety findings."
            actionLabel="Search for patients"
            onAction={() => {
              const input = document.querySelector('input[placeholder*="Search"]') as HTMLInputElement | null;
              input?.focus();
            }}
          />
        ) : (
          <div className="space-y-3">
            {linkedPatients.map((patient) => (
              <div
                key={patient.id}
                className="flex items-center justify-between p-4 bg-paper border border-stone-200 rounded-xl hover:border-stone-300 transition space-x-3 min-h-[52px]"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="w-10 h-10 rounded-xl bg-brand-soft text-brand font-bold text-sm flex items-center justify-center border border-brand/20 shrink-0">
                    {patient.patient_name.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <div className="font-bold text-sm text-ink truncate">{patient.patient_name}</div>
                    <div className="text-[11px] text-ink-muted flex items-center gap-1.5 mt-0.5">
                      <span className="font-mono bg-stone-100 px-1.5 py-0.5 rounded text-ink border border-stone-200">
                        {patient.patient_patient_id}
                      </span>
                      <span>•</span>
                      <span className="font-mono">{patient.phone_number}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/patients/${patient.patient_id}`)}
                    leftIcon={<ExternalLink className="w-3.5 h-3.5 text-brand" />}
                    className="min-h-[40px] text-xs"
                  >
                    View Timeline
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleUnlinkPatient(patient.patient_id, patient.patient_name)}
                    leftIcon={<X className="w-3.5 h-3.5 text-red-600" />}
                    className="min-h-[40px] text-xs text-red-600 hover:bg-red-50"
                  >
                    Unlink
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Link to="/prescriptions">
          <Card className="p-5 bg-white border-stone-200 hover:border-brand/50 hover:bg-brand-soft/10 transition text-center">
            <div className="w-12 h-12 rounded-xl bg-brand-soft text-brand flex items-center justify-center mx-auto mb-3 border border-brand/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-ink">Review Queue</h3>
            <p className="text-xs text-ink-muted mt-1">View prescriptions awaiting clinical sign-off</p>
          </Card>
        </Link>
        <Link to="/patients">
          <Card className="p-5 bg-white border-stone-200 hover:border-brand/50 hover:bg-brand-soft/10 transition text-center">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3 border border-emerald-200">
              <Users className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-ink">Patient Directory</h3>
            <p className="text-xs text-ink-muted mt-1">Browse all registered patients in the system</p>
          </Card>
        </Link>
      </div>
    </div>
  );
};

export default DoctorDashboardPage;