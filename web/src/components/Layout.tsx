import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { RoleBadge } from './Badges';
import { getHealthApi } from '../api/health';
import {
  FileText,
  UploadCloud,
  CheckSquare,
  Activity,
  LogOut,
  UserCheck,
  ShieldCheck,
  HeartPulse,
  ChevronDown,
  Users,
  Lock,
} from 'lucide-react';

import { useLanguage } from '../context/LanguageContext';
import { LanguageSwitcher } from './LanguageSwitcher';

export const Layout: React.FC = () => {
  const { session, logout, login } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();

  const [healthStatus, setHealthStatus] = useState<'ok' | 'degraded' | 'down' | 'loading'>('loading');
  const [showRoleSwitcher, setShowRoleSwitcher] = useState<boolean>(false);
  const [isSwitchingRole, setIsSwitchingRole] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const h = await getHealthApi();
        if (!isMounted) return;
        if (h.database === 'ok' && (h.object_storage === 'ok' || h.object_storage === 'degraded')) {
          setHealthStatus('ok');
        } else if (h.database === 'degraded' || h.object_storage === 'degraded') {
          setHealthStatus('degraded');
        } else {
          setHealthStatus('down');
        }
      } catch {
        if (isMounted) setHealthStatus('down');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleQuickSwitch = async (username: string, pass: string) => {
    setIsSwitchingRole(true);
    try {
      await login(username, pass);
      setShowRoleSwitcher(false);
      navigate('/prescriptions');
    } catch (err) {
      console.error('Role switch failed:', err);
    } finally {
      setIsSwitchingRole(false);
    }
  };

  // Role-Based Navigation Configuration with Multilingual Support
  let navLinks: { to: string; label: string; icon: any; highlight?: boolean }[] = [];

  if (session?.is_patient) {
    navLinks = [
      { to: '/patient-portal', label: t('nav.my_portal', 'My Health Portal'), icon: HeartPulse },
      { to: `/patients/${session.patient_id || 'PAT-1001'}`, label: t('nav.my_records', 'My Medical Records'), icon: UserCheck },
      { to: '/upload', label: t('nav.new_intake', 'Upload Prescription'), icon: UploadCloud },
    ];
  } else if (session?.role === 'DOCTOR') {
    navLinks = [
      { to: '/prescriptions', label: t('nav.prescriptions', 'Prescriptions'), icon: FileText },
      { to: '/patients', label: t('nav.patient_directory', 'Patient Directory'), icon: Users },
      { to: '/upload', label: t('nav.new_intake', 'Upload Prescription'), icon: UploadCloud },
    ];
  } else if (session?.role === 'REVIEWER') {
    navLinks = [
      { to: '/prescriptions', label: t('nav.prescriptions', 'Prescriptions'), icon: FileText },
      { to: '/patients', label: t('nav.patient_directory', 'Patient Directory'), icon: Users },
      { to: '/review-queue', label: t('nav.review_queue', 'Review Queue'), icon: CheckSquare, highlight: true },
      { to: '/upload', label: t('nav.new_intake', 'Upload Prescription'), icon: UploadCloud },
    ];
  } else if (session?.role === 'ADMIN') {
    navLinks = [
      { to: '/prescriptions', label: t('nav.prescriptions', 'Prescriptions'), icon: FileText },
      { to: '/patients', label: t('nav.patient_directory', 'Patient Directory'), icon: Users },
      { to: '/review-queue', label: t('nav.review_queue', 'Review Queue'), icon: CheckSquare, highlight: true },
      { to: '/upload', label: t('nav.new_intake', 'Upload Prescription'), icon: UploadCloud },
      { to: '/health', label: t('nav.system_health', 'System Health'), icon: Activity },
    ];
  } else {
    navLinks = [
      { to: '/prescriptions', label: t('nav.prescriptions', 'Prescriptions'), icon: FileText },
      { to: '/patients', label: t('nav.patient_directory', 'Patient Directory'), icon: Users },
      { to: '/upload', label: t('nav.new_intake', 'Upload Prescription'), icon: UploadCloud },
    ];
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Top Banner / Healthcare compliance bar */}
      <div className="bg-slate-100 text-slate-600 px-4 py-1.5 text-[11px] flex flex-wrap items-center justify-between border-b border-slate-200">
        <div className="flex items-center gap-2">
          <span className="font-bold text-teal-700 flex items-center gap-1.5">
            <HeartPulse className="w-3.5 h-3.5" />
            PRESCRIPTO 2.0
          </span>
          <span className="text-slate-300">|</span>
          <span className="hidden sm:inline text-slate-600">
            {session?.is_patient
              ? 'Patient Health Portal & Confidential Medical Records'
              : 'Prescription Document Intelligence & Clinical Safety Support'}
          </span>
        </div>

        <div className="flex items-center gap-4">
          {!session?.is_patient ? (
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  healthStatus === 'ok'
                    ? 'bg-emerald-500 ring-2 ring-emerald-500/20'
                    : healthStatus === 'degraded'
                    ? 'bg-amber-500 ring-2 ring-amber-500/20'
                    : healthStatus === 'loading'
                    ? 'bg-slate-400 animate-pulse'
                    : 'bg-rose-500 ring-2 ring-rose-500/20'
                }`}
              />
              <span className="text-slate-500">
                System Status:{' '}
                <span className="text-slate-700 capitalize font-medium">{healthStatus}</span>
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-emerald-700 font-medium">
              <Lock className="w-3.5 h-3.5" />
              <span>Encrypted Patient Vault</span>
            </div>
          )}

          <span className="text-slate-300 hidden md:inline">&bull;</span>
          <span className="text-slate-500 hidden md:inline">
            Compliant with <strong className="text-slate-700 font-semibold">India DPDPA 2023</strong>
          </span>
        </div>
      </div>

      {/* Main Navbar */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-xs group-hover:bg-teal-700 transition">
                <ShieldCheck className="w-5 h-5 font-bold" />
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-slate-900 group-hover:text-teal-700 transition flex items-center gap-1">
                  Prescripto <span className="text-teal-600 font-bold">2.0</span>
                </span>
                <span className="block text-[10px] font-semibold text-slate-500 -mt-0.5 tracking-wider uppercase">
                  {session?.is_patient ? 'Patient Portal' : 'Clinical Workspace'}
                </span>
              </div>
            </Link>

            {/* Navigation tabs */}
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => {
                const Icon = link.icon;
                const isActive = location.pathname === link.to;
                return (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition ${
                      isActive
                        ? 'bg-teal-50 text-teal-800 border border-teal-200/80 font-semibold shadow-2xs'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-teal-700' : 'text-slate-500'}`} />
                    <span>{link.label}</span>
                    {link.highlight && (
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-600 animate-pulse" />
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* User Controls & Session Switcher */}
          <div className="flex items-center gap-2.5">
            <LanguageSwitcher />

            {session ? (
              <div className="relative">
                <div className="flex items-center gap-2.5 bg-slate-50 border border-slate-200 p-1.5 pr-2.5 rounded-xl hover:bg-slate-100/60 transition">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs uppercase ${
                      session.is_patient
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                        : 'bg-teal-100 text-teal-800 border border-teal-200'
                    }`}
                  >
                    {(session.patient_name || session.username).substring(0, 2)}
                  </div>
                  <div className="text-left">
                    <div className="text-xs font-semibold text-slate-900 leading-tight flex items-center gap-1.5">
                      <span>{session.patient_name || session.username}</span>
                      {session.patient_id && (
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                          {session.patient_id}
                        </span>
                      )}
                    </div>
                    <div className="mt-0.5">
                      <RoleBadge role={session.role} isPatient={session.is_patient} />
                    </div>
                  </div>

                  {/* Fast role switcher trigger */}
                  <button
                    onClick={() => setShowRoleSwitcher((s) => !s)}
                    className="ml-1 p-1 hover:bg-slate-200 rounded-md text-slate-500 hover:text-slate-800 transition"
                    title="Switch user account"
                  >
                    <ChevronDown className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Dropdown for role switching & logout */}
                {showRoleSwitcher && (
                  <div className="absolute right-0 mt-2 w-72 bg-white border border-slate-200 rounded-xl shadow-lg p-2 z-50 text-xs animate-in fade-in duration-100">
                    <div className="px-2.5 py-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100">
                      Switch Active Session
                    </div>
                    <div className="py-1 space-y-1">
                      <button
                        onClick={() => handleQuickSwitch('doctor.sharma@prescripto.local', 'DoctorPass123!')}
                        disabled={isSwitchingRole}
                        className="w-full text-left px-2.5 py-2 rounded-lg flex items-center justify-between hover:bg-indigo-50 border border-transparent hover:border-indigo-100 transition"
                      >
                        <span className="flex items-center gap-2">
                          <CheckSquare className="w-3.5 h-3.5 text-indigo-600" />
                          <span className="font-semibold text-slate-800">Dr. Ananya Sharma</span>
                        </span>
                        <span className="text-[10px] text-indigo-800 font-semibold bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
                          DOCTOR
                        </span>
                      </button>

                      <button
                        onClick={() => handleQuickSwitch('reviewer@prescripto.local', 'ReviewerPass123!')}
                        disabled={isSwitchingRole}
                        className="w-full text-left px-2.5 py-2 rounded-lg flex items-center justify-between hover:bg-blue-50 border border-transparent hover:border-blue-100 transition"
                      >
                        <span className="flex items-center gap-2">
                          <CheckSquare className="w-3.5 h-3.5 text-blue-600" />
                          <span className="font-semibold text-slate-800">Clinical Reviewer</span>
                        </span>
                        <span className="text-[10px] text-blue-800 font-semibold bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                          REVIEWER
                        </span>
                      </button>

                      <button
                        onClick={() => handleQuickSwitch('admin@prescripto.local', 'AdminPass123!')}
                        disabled={isSwitchingRole}
                        className="w-full text-left px-2.5 py-2 rounded-lg flex items-center justify-between hover:bg-purple-50 border border-transparent hover:border-purple-100 transition"
                      >
                        <span className="flex items-center gap-2">
                          <ShieldCheck className="w-3.5 h-3.5 text-purple-600" />
                          <span className="font-semibold text-slate-800">Hospital Admin</span>
                        </span>
                        <span className="text-[10px] text-purple-800 font-semibold bg-purple-50 px-1.5 py-0.5 rounded border border-purple-200">
                          ADMIN
                        </span>
                      </button>
                    </div>

                    <div className="border-t border-slate-100 pt-1 mt-1">
                      <button
                        onClick={logout}
                        className="w-full text-left px-2.5 py-1.5 rounded-lg text-rose-600 hover:bg-rose-50 flex items-center gap-2 font-medium transition"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <Link
                to="/login"
                className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg shadow-xs transition"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-800">Prescripto 2.0</span>
            <span>&bull;</span>
            <span>Clinical Prescription Intelligence & Safety Verification</span>
          </div>

          <div className="text-[11px] text-slate-500 text-center sm:text-right">
            <span>Clinical Decision Support &bull; Multi-Layer Safety Screening &bull; DPDPA 2023 Compliant</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
