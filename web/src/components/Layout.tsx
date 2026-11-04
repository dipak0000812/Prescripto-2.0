import React, { useState, useEffect } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
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
  ChevronDown,
  Menu,
  X,
  Users,
  Home,
  HelpCircle,
  PhoneCall,
  Check,
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { LanguageSwitcher } from './LanguageSwitcher';

export const Layout: React.FC = () => {
  const { session, logout } = useAuth();
  const { t, language } = useLanguage();
  const location = useLocation();

  const [healthStatus, setHealthStatus] = useState<'ok' | 'degraded' | 'down' | 'loading'>('loading');
  const [showUserMenu, setShowUserMenu] = useState<boolean>(false);
  const [showMobileNav, setShowMobileNav] = useState<boolean>(false);
  const [showHelpModal, setShowHelpModal] = useState<boolean>(false);

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

  // Role-Based Navigation Configuration with Multilingual Support
  let navLinks: { to: string; label: string; icon: any; highlight?: boolean }[] = [];

  if (session?.is_patient) {
    navLinks = [
      { to: '/patient-portal', label: t('nav.my_portal', 'My Health Portal'), icon: FileText },
      ...(session.patient_id
        ? [{ to: `/patients/${session.patient_id}`, label: t('nav.my_records', 'My Medical Records'), icon: UserCheck }]
        : []),
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
      { to: '/upload', label: t('nav.new_intake', 'Upload Prescription'), icon: UploadCloud },
    ];
  }

  // Determine mobile bottom nav paths
  const homePath = session?.is_patient ? '/patient-portal' : '/';
  const prescriptionsPath = session?.is_patient
    ? '/patient-portal'
    : session
    ? '/prescriptions'
    : '/login';

  const isHomeActive = location.pathname === '/' || (session?.is_patient && location.pathname === '/patient-portal');
  const isPrescriptionsActive =
    location.pathname === '/prescriptions' ||
    (session?.is_patient && location.pathname.startsWith('/patients/'));

  return (
    <div className="min-h-screen flex flex-col bg-[#FAF9F6] text-[#1C252E]">
      {/* Skip to main content link for screen readers & keyboard accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#0F5147] focus:text-white focus:rounded-lg"
      >
        Skip to main content
      </a>

      {/* Top Clinical & System Status Bar (For clinicians / staff) */}
      {!session?.is_patient && session && (
        <div className="bg-[#F4F2EC] text-stone-600 px-4 py-1.5 text-xs flex flex-wrap items-center justify-between border-b border-stone-200">
          <div className="flex items-center gap-2">
            <span className="font-bold text-[#0F5147] flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              PRESCRIPTO 2.0
            </span>
            <span className="text-stone-300">|</span>
            <span className="hidden sm:inline text-stone-600">
              Clinical Workspace & Prescription Review Aid
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  healthStatus === 'ok'
                    ? 'bg-emerald-500 ring-2 ring-emerald-500/20'
                    : healthStatus === 'degraded'
                    ? 'bg-amber-500 ring-2 ring-amber-500/20'
                    : healthStatus === 'loading'
                    ? 'bg-stone-400 animate-pulse'
                    : 'bg-rose-500 ring-2 ring-rose-500/20'
                }`}
              />
              <span className="text-stone-500" role="status" aria-live="polite">
                System Status:{' '}
                <span className="text-stone-700 capitalize font-medium">{healthStatus}</span>
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Main Navbar */}
      <header className="sticky top-0 z-40 bg-white border-b border-stone-200 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2">
          {/* Logo & Brand */}
          <div className="flex items-center gap-6">
            <Link to={homePath} className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-[#0F5147] text-white flex items-center justify-center shadow-2xs group-hover:bg-[#0A3831] transition">
                <ShieldCheck className="w-5 h-5 font-bold" />
              </div>
              <div>
                <span className="text-base sm:text-lg font-bold tracking-tight text-[#1C252E] group-hover:text-[#0F5147] transition flex items-center gap-1">
                  Prescripto <span className="text-[#0F5147] font-bold">2.0</span>
                </span>
                <span className="block text-[11px] font-medium text-stone-500 -mt-0.5">
                  {session?.is_patient ? 'Patient Portal' : 'Prescription Review'}
                </span>
              </div>
            </Link>

            {/* Desktop Navigation tabs */}
            <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
              {navLinks.map((link) => {
                const Icon = link.icon;
                const isActive = location.pathname === link.to;
                return (
                  <Link
                    key={link.to}
                    to={link.to}
                    aria-current={isActive ? 'page' : undefined}
                    className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition ${
                      isActive
                        ? 'bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]'
                        : 'text-stone-700 hover:text-[#1C252E] hover:bg-[#F4F2EC]'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-[#0F5147]' : 'text-stone-500'}`} />
                    <span>{link.label}</span>
                    {link.highlight && (
                      <span className="w-2 h-2 rounded-full bg-[#0F5147] animate-pulse" />
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* Right Header Actions: Language Switcher + User Profile / Sign In */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Always visible Language Switcher on EVERY screen */}
            <LanguageSwitcher />

            {session ? (
              <div className="relative">
                <div className="flex items-center gap-2 bg-[#F4F2EC] border border-stone-200 p-1.5 pr-2.5 rounded-xl hover:bg-stone-200/60 transition">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs uppercase ${
                      session.is_patient
                        ? 'bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]'
                        : 'bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]'
                    }`}
                  >
                    {(session.patient_name || session.username).substring(0, 2)}
                  </div>
                  <div className="text-left hidden sm:block">
                    <div className="text-xs font-semibold text-[#1C252E] leading-tight flex items-center gap-1.5">
                      <span>{session.patient_name || session.username}</span>
                      {session.patient_id && (
                        <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-white text-[#0F5147] border border-stone-200">
                          {session.patient_id}
                        </span>
                      )}
                    </div>
                    <div className="mt-0.5">
                      <RoleBadge role={session.role} isPatient={session.is_patient} />
                    </div>
                  </div>

                  <button
                    onClick={() => setShowUserMenu((s) => !s)}
                    className="p-1 hover:bg-stone-200 rounded-md text-stone-600 hover:text-stone-900 transition cursor-pointer min-h-[32px] min-w-[32px] flex items-center justify-center"
                    title="Account options"
                    aria-label="Account options"
                    aria-expanded={showUserMenu}
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </div>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 rounded-xl border border-stone-200 bg-white p-2 text-xs shadow-lg z-50">
                    <button
                      onClick={logout}
                      className="w-full rounded-lg px-2.5 py-2 text-left font-medium text-[#BE123C] hover:bg-[#FFE4E6] flex items-center gap-2 cursor-pointer"
                    >
                      <LogOut className="h-4 w-4" aria-hidden="true" />
                      <span>{t('nav.sign_out', 'Sign out')}</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Link
                to="/login"
                className="inline-flex items-center justify-center px-4 py-2 bg-[#0F5147] hover:bg-[#0A3831] text-white text-xs sm:text-sm font-semibold rounded-xl shadow-2xs transition min-h-[40px]"
              >
                {t('nav.sign_in', 'Sign In')}
              </Link>
            )}

            {/* Mobile Hamburger toggle for staff links if more than 2 */}
            {navLinks.length > 1 && (
              <button
                type="button"
                onClick={() => setShowMobileNav((open) => !open)}
                className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-stone-300 text-stone-700 hover:bg-[#F4F2EC] md:hidden cursor-pointer"
                aria-label={showMobileNav ? 'Close navigation menu' : 'Open navigation menu'}
                aria-expanded={showMobileNav}
                aria-controls="mobile-navigation"
              >
                {showMobileNav ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
            )}
          </div>
        </div>

        {/* Collapsible Mobile Navigation Drawer for Staff */}
        {showMobileNav && (
          <nav
            id="mobile-navigation"
            className="border-t border-stone-200 bg-white px-4 py-2 md:hidden"
            aria-label="Mobile menu"
          >
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = location.pathname === link.to;
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setShowMobileNav(false)}
                  aria-current={isActive ? 'page' : undefined}
                  className={`flex min-h-[48px] items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold ${
                    isActive ? 'bg-[#E6F0EE] text-[#0F5147]' : 'text-stone-700 hover:bg-[#F4F2EC]'
                  }`}
                >
                  <Icon className="h-5 w-5 text-[#0F5147]" aria-hidden="true" />
                  {link.label}
                </Link>
              );
            })}
          </nav>
        )}
      </header>

      {/* Main Content Area: pb-24 ensures mobile bottom navigation bar never covers page content */}
      <main id="main-content" className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-24 md:pb-8">
        <Outlet />
      </main>

      {/* Mobile Bottom Navigation Bar (Visible only on mobile < md) */}
      <nav
        className="fixed bottom-0 inset-x-0 z-40 bg-white border-t border-stone-200 shadow-md md:hidden px-2 py-1.5 flex items-center justify-around"
        aria-label="Mobile bottom navigation"
      >
        {/* 1. Home */}
        <Link
          to={homePath}
          aria-current={isHomeActive ? 'page' : undefined}
          className={`flex flex-col items-center justify-center min-h-[48px] min-w-[72px] px-2 py-1 rounded-xl transition ${
            isHomeActive ? 'text-[#0F5147] font-bold' : 'text-stone-600 hover:text-stone-900'
          }`}
        >
          <Home className="w-5 h-5 mb-0.5" aria-hidden="true" />
          <span className="text-[11px] leading-tight">{t('nav.home', 'Home')}</span>
        </Link>

        {/* 2. My Prescriptions */}
        <Link
          to={prescriptionsPath}
          aria-current={isPrescriptionsActive ? 'page' : undefined}
          className={`flex flex-col items-center justify-center min-h-[48px] min-w-[72px] px-2 py-1 rounded-xl transition ${
            isPrescriptionsActive ? 'text-[#0F5147] font-bold' : 'text-stone-600 hover:text-stone-900'
          }`}
        >
          <FileText className="w-5 h-5 mb-0.5" aria-hidden="true" />
          <span className="text-[11px] leading-tight">{t('nav.my_prescriptions', 'My Prescriptions')}</span>
        </Link>

        {/* 3. Help */}
        <Link
          to="/help"
          aria-current={location.pathname === '/help' ? 'page' : undefined}
          className={`flex flex-col items-center justify-center min-h-[48px] min-w-[72px] px-2 py-1 rounded-xl transition ${
            location.pathname === '/help' ? 'text-[#0F5147] font-bold' : 'text-stone-600 hover:text-stone-900'
          }`}
        >
          <HelpCircle className="w-5 h-5 mb-0.5 text-[#0F5147]" aria-hidden="true" />
          <span className="text-[11px] leading-tight">{t('nav.help', 'Help')}</span>
        </Link>
      </nav>

      {/* Accessible Help Modal */}
      {showHelpModal && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs"
        >
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-md border border-stone-200 relative">
            <button
              onClick={() => setShowHelpModal(false)}
              className="absolute top-4 right-4 p-2 text-stone-500 hover:text-stone-800 rounded-lg hover:bg-stone-100 transition min-h-[40px] min-w-[40px] flex items-center justify-center"
              aria-label="Close help"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center border border-[#9DC1BB]">
                <HelpCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-[#1C252E]">
                  {t('help.modal_title', 'Need Help?')}
                </h3>
                <p className="text-xs text-stone-600">Prescripto 2.0</p>
              </div>
            </div>

            <p className="text-sm text-stone-700 mb-4 leading-relaxed">
              {t('help.modal_desc', 'Prescripto helps you understand your prescription and medication timings simply.')}
            </p>

            <div className="space-y-2 text-xs sm:text-sm bg-[#FAF9F6] p-4 rounded-xl border border-stone-200 mb-4">
              <div className="flex items-start gap-2">
                <Check className="w-4 h-4 text-[#0F5147] shrink-0 mt-0.5" />
                <span>{t('help.modal_step1', '1. Take a clear photo of your prescription.')}</span>
              </div>
              <div className="flex items-start gap-2">
                <Check className="w-4 h-4 text-[#0F5147] shrink-0 mt-0.5" />
                <span>{t('help.modal_step2', '2. Wait a few moments while we read the medicines.')}</span>
              </div>
              <div className="flex items-start gap-2">
                <Check className="w-4 h-4 text-[#0F5147] shrink-0 mt-0.5" />
                <span>{t('help.modal_step3', '3. See when to take each medicine and listen in your language.')}</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#FEF3C7] border border-[#FCD34D] text-xs text-[#78350F] mb-5">
              <strong>
                {language === 'hi' ? 'महत्वपूर्ण ध्यान दें: ' : language === 'gu' ? 'મહત્વની સૂચના: ' : language === 'mr' ? 'महत्त्वाची नोंद: ' : 'Safety reminder: '}
              </strong>
              {t('help.modal_disclaimer', 'Always check with your doctor or chemist before taking medicines.')}
            </div>

            <button
              type="button"
              onClick={() => setShowHelpModal(false)}
              className="w-full py-2.5 rounded-xl bg-[#0F5147] text-white font-semibold text-sm hover:bg-[#0A3831] transition min-h-[48px] cursor-pointer"
            >
              {t('common.close', 'Close')}
            </button>
          </div>
        </div>
      )}

      {/* Footer with Calm, Always-Visible Safety Note */}
      <footer className="bg-white border-t border-stone-200 py-6 text-xs text-stone-600 hidden md:block">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-[#1C252E] font-semibold">
            <span>Prescripto 2.0</span>
            <span>&bull;</span>
            <span className="font-normal text-stone-600">Prescription Text Organization Aid</span>
          </div>

          <div className="text-xs text-stone-600 text-center md:text-right max-w-xl leading-relaxed">
            This is a computer reading of your prescription. Please check it with your doctor or chemist before taking any medicine.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
