import React, { useState, useEffect } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getHealthApi } from '../api/health';
import {
  FileText,
  UploadCloud,
  CheckSquare,
  Activity,
  LogOut,
  UserCheck,
  ChevronDown,
  Menu,
  X,
  Users,
  Home,
  HelpCircle,
  Bell,
  Camera,
  Search,
  Check,
  Stethoscope,
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { LanguageSwitcher } from './LanguageSwitcher';
import { Avatar } from './ui/Avatar';
import { AssistantDrawer } from './AssistantDrawer';
import { OfflineBanner } from './OfflineBanner';

export const Layout: React.FC = () => {
  const { session, logout } = useAuth();
  const { t, language } = useLanguage();
  const location = useLocation();

  const [healthStatus, setHealthStatus] = useState<'ok' | 'degraded' | 'down' | 'loading'>('loading');
  const [showUserMenu, setShowUserMenu] = useState<boolean>(false);
  const [showSidebarDrawer, setShowSidebarDrawer] = useState<boolean>(false);
  const [showHelpModal, setShowHelpModal] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

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

    if (session?.role === 'ADMIN') {
      checkHealth();
      const interval = setInterval(checkHealth, 30000);
      return () => {
        isMounted = false;
        clearInterval(interval);
      };
    }
  }, [session?.role]);

  // Handle staff search submission
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    window.location.href = `/prescriptions?q=${encodeURIComponent(searchQuery.trim())}`;
  };

  const isPatient = Boolean(session?.is_patient);
  const homePath = isPatient ? '/patient-portal' : '/';

  // Format Staff Display Name
  const staffDisplayName = session?.patient_name || session?.username || 'Staff User';
  const roleLabel = session?.role === 'DOCTOR'
    ? 'Doctor'
    : session?.role === 'REVIEWER'
    ? 'Clinical Reviewer'
    : session?.role === 'ADMIN'
    ? 'Administrator'
    : 'Patient';

  // Staff Sidebar Navigation links
  const staffNavLinks = [
    ...(session?.role === 'REVIEWER' || session?.role === 'ADMIN'
      ? [{ to: '/review-queue', label: t('nav.review_queue', 'Review Queue'), icon: CheckSquare, badge: '!' }]
      : []),
    { to: '/prescriptions', label: t('nav.prescriptions', 'Prescriptions'), icon: FileText },
    { to: '/patients', label: t('nav.patient_directory', 'Patients'), icon: Users },
    { to: '/upload', label: t('nav.new_intake', 'Upload Prescription'), icon: UploadCloud },
    ...(session?.role === 'ADMIN'
      ? [{ to: '/health', label: t('nav.system_health', 'System Health'), icon: Activity }]
      : []),
  ];

  // ---------------------------------------------------------------------------
  // 1. PATIENT APP SHELL
  // ---------------------------------------------------------------------------
  if (isPatient || !session) {
    const isHomeActive = location.pathname === '/' || location.pathname === '/patient-portal';
    const isTodayActive = location.pathname === '/today';
    const isPrescriptionsActive =
      location.pathname.startsWith('/patients/') ||
      (location.pathname === '/patient-portal' && !isHomeActive);

    return (
      <div className="min-h-screen flex flex-col bg-[#FAF9F6] text-[#1C252E]">
        <OfflineBanner />
        {/* Accessible Skip Link */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#0F5147] focus:text-white focus:rounded-xl shadow-md"
        >
          Skip to main content
        </a>

        {/* Slim Patient Top Bar */}
        <header className="sticky top-0 z-40 bg-white border-b border-stone-200 shadow-2xs">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
            {/* Logo */}
            <Link to={homePath} className="flex items-center gap-2.5 group shrink-0">
              <div className="w-9 h-9 rounded-xl bg-[#0F5147] text-white flex items-center justify-center shadow-2xs group-hover:bg-[#0A3831] transition">
                <Stethoscope className="w-5 h-5 font-bold" aria-hidden="true" />
              </div>
              <div>
                <span className="text-base sm:text-lg font-bold tracking-tight text-[#1C252E] group-hover:text-[#0F5147] transition">
                  Prescripto <span className="text-[#0F5147]">2.0</span>
                </span>
                <span className="hidden sm:block text-[11px] font-medium text-stone-500 -mt-0.5">
                  Neighborhood Clinic Guide
                </span>
              </div>
            </Link>

            {/* Desktop Top Nav for Patients */}
            <nav className="hidden md:flex items-center gap-1" aria-label="Patient navigation">
              <Link
                to={homePath}
                aria-current={isHomeActive ? 'page' : undefined}
                className={`px-3.5 py-2 rounded-xl text-sm font-semibold transition ${
                  isHomeActive
                    ? 'bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]'
                    : 'text-stone-700 hover:text-[#1C252E] hover:bg-[#F4F2EC]'
                }`}
              >
                {t('nav.home', 'Home')}
              </Link>
              <Link
                to="/today"
                aria-current={isTodayActive ? 'page' : undefined}
                className={`px-3.5 py-2 rounded-xl text-sm font-semibold transition ${
                  isTodayActive
                    ? 'bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]'
                    : 'text-stone-700 hover:text-[#1C252E] hover:bg-[#F4F2EC]'
                }`}
              >
                {t('nav.today_doses', "Today's Doses")}
              </Link>
              <Link
                to="/upload"
                aria-current={location.pathname === '/upload' ? 'page' : undefined}
                className={`px-3.5 py-2 rounded-xl text-sm font-semibold transition ${
                  location.pathname === '/upload'
                    ? 'bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]'
                    : 'text-stone-700 hover:text-[#1C252E] hover:bg-[#F4F2EC]'
                }`}
              >
                {t('nav.new_intake', 'Scan Prescription')}
              </Link>
            </nav>

            {/* Language Switcher + Help Trigger + Profile */}
            <div className="flex items-center gap-2">
              <LanguageSwitcher />

              <button
                type="button"
                onClick={() => setShowHelpModal(true)}
                title={t('nav.help', 'Help')}
                aria-label={t('nav.help', 'Help')}
                className="p-2 text-stone-600 hover:text-[#0F5147] hover:bg-[#F4F2EC] rounded-xl transition min-h-[40px] min-w-[40px] flex items-center justify-center cursor-pointer"
              >
                <HelpCircle className="w-5 h-5" aria-hidden="true" />
              </button>

              {session ? (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowUserMenu((s) => !s)}
                    aria-expanded={showUserMenu}
                    aria-label="User account menu"
                    className="flex items-center gap-1.5 p-1 rounded-xl hover:bg-[#F4F2EC] transition cursor-pointer min-h-[40px]"
                  >
                    <Avatar name={session.patient_name || session.username} size="sm" />
                    <ChevronDown className="w-4 h-4 text-stone-500" />
                  </button>

                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-52 rounded-xl border border-stone-200 bg-white p-2 text-xs shadow-lg z-50 animate-in fade-in-50 duration-150">
                      <div className="px-3 py-2 border-b border-stone-100">
                        <div className="font-semibold text-[#1C252E] truncate">
                          {session.patient_name || session.username}
                        </div>
                        <div className="text-[11px] text-stone-500 font-mono mt-0.5">
                          {session.patient_id || 'Patient Account'}
                        </div>
                      </div>
                      <button
                        onClick={logout}
                        className="w-full mt-1 rounded-lg px-3 py-2 text-left font-medium text-[#BE123C] hover:bg-[#FFE4E6] flex items-center gap-2 cursor-pointer transition min-h-[40px]"
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
                  className="inline-flex items-center justify-center px-3.5 py-1.5 bg-[#0F5147] hover:bg-[#0A3831] text-white text-xs sm:text-sm font-semibold rounded-xl shadow-2xs transition min-h-[40px]"
                >
                  {t('nav.sign_in', 'Sign In')}
                </Link>
              )}
            </div>
          </div>
        </header>

        {/* Patient Main Container: Centered Column (~960px) */}
        <main id="main-content" className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-6 pb-28 md:pb-8">
          <Outlet />
        </main>

        {/* Mobile Bottom Navigation for Patients (Raised Center Scan Button) */}
        <nav
          className="fixed bottom-0 inset-x-0 z-40 bg-white border-t border-stone-200 shadow-lg md:hidden px-3 py-1 flex items-center justify-between safe-bottom"
          aria-label="Mobile bottom navigation"
        >
          {/* 1. Home */}
          <Link
            to={homePath}
            aria-current={isHomeActive ? 'page' : undefined}
            className={`flex-1 flex flex-col items-center justify-center min-h-[48px] py-1 transition ${
              isHomeActive ? 'text-[#0F5147] font-bold' : 'text-stone-500 hover:text-stone-900'
            }`}
          >
            <Home className="w-5 h-5 mb-0.5" aria-hidden="true" />
            <span className="text-[11px] leading-tight">{t('nav.home', 'Home')}</span>
          </Link>

          {/* 2. Today's Doses */}
          <Link
            to="/today"
            aria-current={isTodayActive ? 'page' : undefined}
            className={`flex-1 flex flex-col items-center justify-center min-h-[48px] py-1 transition ${
              isTodayActive ? 'text-[#0F5147] font-bold' : 'text-stone-500 hover:text-stone-900'
            }`}
          >
            <Bell className="w-5 h-5 mb-0.5" aria-hidden="true" />
            <span className="text-[11px] leading-tight">{t('nav.today_doses', "Today")}</span>
          </Link>

          {/* 3. Scan Prescription (Raised Prominent Center Button) */}
          <div className="relative -top-3 flex flex-col items-center px-1">
            <Link
              to="/upload"
              aria-label={t('nav.new_intake', 'Scan Prescription')}
              className="w-14 h-14 rounded-full bg-[#0F5147] text-white flex items-center justify-center shadow-md hover:bg-[#0A3831] active:scale-95 transition-transform border-4 border-[#FAF9F6] focus-visible:ring-2 focus-visible:ring-[#0F5147] focus-visible:ring-offset-2"
            >
              <Camera className="w-6 h-6" aria-hidden="true" />
            </Link>
            <span className="text-[10px] font-bold text-[#0F5147] mt-0.5">Scan</span>
          </div>

          {/* 4. My Prescriptions */}
          <Link
            to={session?.patient_id ? `/patients/${session.patient_id}` : '/patient-portal'}
            aria-current={isPrescriptionsActive ? 'page' : undefined}
            className={`flex-1 flex flex-col items-center justify-center min-h-[48px] py-1 transition ${
              isPrescriptionsActive ? 'text-[#0F5147] font-bold' : 'text-stone-500 hover:text-stone-900'
            }`}
          >
            <FileText className="w-5 h-5 mb-0.5" aria-hidden="true" />
            <span className="text-[11px] leading-tight">{t('nav.my_prescriptions', 'Records')}</span>
          </Link>

          {/* 5. Help Modal Trigger */}
          <button
            type="button"
            onClick={() => setShowHelpModal(true)}
            className="flex-1 flex flex-col items-center justify-center min-h-[48px] py-1 text-stone-500 hover:text-stone-900 cursor-pointer"
          >
            <HelpCircle className="w-5 h-5 mb-0.5 text-[#0F5147]" aria-hidden="true" />
            <span className="text-[11px] leading-tight">{t('nav.help', 'Help')}</span>
          </button>
        </nav>

        {/* Healthcare Assistant Drawer */}
        <AssistantDrawer isOpen={showHelpModal} onClose={() => setShowHelpModal(false)} />
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 2. STAFF WORKSPACE SHELL (Doctor, Reviewer, Admin)
  // ---------------------------------------------------------------------------
  return (
    <div className="min-h-screen flex bg-[#FAF9F6] text-[#1C252E]">
      {/* Accessible Skip Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#0F5147] focus:text-white focus:rounded-xl shadow-md"
      >
        Skip to main content
      </a>

      {/* Desktop Left Sidebar */}
      <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-stone-200 shrink-0 select-none">
        {/* Brand Header */}
        <div className="h-16 px-6 border-b border-stone-100 flex items-center justify-between">
          <Link to="/prescriptions" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-[#0F5147] text-white flex items-center justify-center shadow-2xs group-hover:bg-[#0A3831] transition">
              <Stethoscope className="w-4 h-4 font-bold" aria-hidden="true" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-[#1C252E] group-hover:text-[#0F5147] transition">
                Prescripto <span className="text-[#0F5147]">2.0</span>
              </span>
              <span className="block text-[10px] uppercase font-semibold text-stone-500 tracking-wider">
                Clinical Workspace
              </span>
            </div>
          </Link>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Staff navigation">
          {staffNavLinks.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.to || location.pathname.startsWith(`${item.to}/`);
            return (
              <Link
                key={item.to}
                to={item.to}
                aria-current={isActive ? 'page' : undefined}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition min-h-[44px] ${
                  isActive
                    ? 'bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]'
                    : 'text-[#4B5563] hover:text-[#1C252E] hover:bg-[#F4F2EC]'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#0F5147]' : 'text-stone-500'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-1.5 py-0.5 rounded-md text-[11px] font-bold bg-[#0F5147] text-white">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Admin System Status Dot in Sidebar */}
        {session?.role === 'ADMIN' && (
          <div className="p-3 mx-3 mb-3 rounded-xl bg-[#FAF9F6] border border-stone-200 text-xs">
            <Link to="/health" className="flex items-center justify-between text-stone-600 hover:text-[#1C252E]">
              <span className="font-semibold text-stone-700">System Status</span>
              <div className="flex items-center gap-1.5">
                <span
                  className={`w-2 h-2 rounded-full ${
                    healthStatus === 'ok'
                      ? 'bg-emerald-500 ring-2 ring-emerald-500/20'
                      : healthStatus === 'degraded'
                      ? 'bg-amber-500 ring-2 ring-amber-500/20'
                      : 'bg-rose-500 ring-2 ring-rose-500/20'
                  }`}
                />
                <span className="capitalize font-mono text-[11px]">{healthStatus}</span>
              </div>
            </Link>
          </div>
        )}

        {/* User Card at Bottom of Sidebar */}
        <div className="p-3 border-t border-stone-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5 overflow-hidden">
            <Avatar name={staffDisplayName} size="sm" />
            <div className="overflow-hidden">
              <div className="text-xs font-semibold text-[#1C252E] truncate">
                {staffDisplayName}
              </div>
              <div className="text-[10px] text-stone-500 truncate">
                {roleLabel}
              </div>
            </div>
          </div>

          <button
            onClick={logout}
            title={t('nav.sign_out', 'Sign out')}
            aria-label={t('nav.sign_out', 'Sign out')}
            className="p-1.5 text-stone-500 hover:text-[#BE123C] hover:bg-[#FFE4E6] rounded-lg transition cursor-pointer min-h-[36px] min-w-[36px] flex items-center justify-center"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </aside>

      {/* Main Staff Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0">
        <OfflineBanner />
        {/* Staff Top Bar */}
        <header className="sticky top-0 z-30 bg-white border-b border-stone-200 h-16 flex items-center justify-between px-4 sm:px-6 gap-4">
          {/* Mobile drawer toggle & Quick Search */}
          <div className="flex items-center gap-3 flex-1 max-w-md">
            <button
              type="button"
              onClick={() => setShowSidebarDrawer((s) => !s)}
              className="lg:hidden p-2 text-stone-600 hover:text-stone-900 rounded-lg hover:bg-stone-100 transition min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
              aria-label="Toggle navigation drawer"
            >
              <Menu className="w-5 h-5" />
            </button>

            <form onSubmit={handleSearchSubmit} className="relative w-full hidden sm:block">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-stone-400 pointer-events-none" />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search prescriptions, patients, medicines..."
                className="w-full pl-9 pr-4 py-2 bg-[#FAF9F6] border border-stone-200 rounded-xl text-xs sm:text-sm text-[#1C252E] focus:outline-hidden focus:border-[#0F5147] focus:bg-white transition"
              />
            </form>
          </div>

          {/* Top Actions: Language Switcher, Help, Single Profile Dropdown */}
          <div className="flex items-center gap-3">
            <LanguageSwitcher />

            <button
              type="button"
              onClick={() => setShowHelpModal(true)}
              title={t('nav.help', 'Help')}
              aria-label={t('nav.help', 'Help')}
              className="p-2 text-stone-600 hover:text-[#0F5147] hover:bg-[#F4F2EC] rounded-xl transition min-h-[40px] min-w-[40px] flex items-center justify-center cursor-pointer"
            >
              <HelpCircle className="w-5 h-5" aria-hidden="true" />
            </button>

            {/* Single Unified Profile Menu */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowUserMenu((s) => !s)}
                aria-expanded={showUserMenu}
                aria-label="Clinical user menu"
                className="flex items-center gap-2 p-1.5 rounded-xl border border-stone-200 hover:bg-[#F4F2EC] transition cursor-pointer min-h-[44px]"
              >
                <Avatar name={staffDisplayName} size="sm" />
                <div className="text-left hidden md:block">
                  <div className="text-xs font-bold text-[#1C252E] leading-tight">
                    {staffDisplayName}
                  </div>
                  <div className="text-[10px] text-stone-500">
                    {roleLabel}
                  </div>
                </div>
                <ChevronDown className="w-4 h-4 text-stone-500" />
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-56 rounded-xl border border-stone-200 bg-white p-2 text-xs shadow-lg z-50 animate-in fade-in-50 duration-150">
                  <div className="px-3 py-2 border-b border-stone-100">
                    <div className="font-bold text-[#1C252E]">{staffDisplayName}</div>
                    <div className="text-[11px] text-stone-500">{roleLabel}</div>
                    <div className="text-[10px] font-mono text-stone-400 mt-0.5 truncate">
                      {session.username}
                    </div>
                  </div>

                  <Link
                    to="/prescriptions"
                    onClick={() => setShowUserMenu(false)}
                    className="w-full mt-1 rounded-lg px-3 py-2 text-left font-medium text-stone-700 hover:bg-stone-50 flex items-center gap-2 min-h-[38px]"
                  >
                    <FileText className="w-4 h-4 text-stone-500" />
                    <span>Prescriptions Ledger</span>
                  </Link>

                  <button
                    onClick={logout}
                    className="w-full mt-1 rounded-lg px-3 py-2 text-left font-medium text-[#BE123C] hover:bg-[#FFE4E6] flex items-center gap-2 cursor-pointer transition min-h-[38px]"
                  >
                    <LogOut className="w-4 h-4" aria-hidden="true" />
                    <span>{t('nav.sign_out', 'Sign out')}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Collapsible Mobile/Tablet Drawer for Staff */}
        {showSidebarDrawer && (
          <div
            className="fixed inset-0 z-50 lg:hidden flex"
            role="dialog"
            aria-modal="true"
          >
            <div
              className="fixed inset-0 bg-stone-900/50 backdrop-blur-xs transition-opacity"
              onClick={() => setShowSidebarDrawer(false)}
            />
            <div className="relative w-64 max-w-[80%] bg-white h-full shadow-2xl flex flex-col p-4 animate-in slide-in-from-left duration-200">
              <div className="flex items-center justify-between pb-4 border-b border-stone-100">
                <span className="font-bold text-[#1C252E]">Prescripto 2.0</span>
                <button
                  type="button"
                  onClick={() => setShowSidebarDrawer(false)}
                  className="p-1.5 text-stone-500 hover:text-stone-900 rounded-lg hover:bg-stone-100 min-h-[40px] min-w-[40px] flex items-center justify-center cursor-pointer"
                  aria-label="Close drawer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <nav className="flex-1 py-4 space-y-1">
                {staffNavLinks.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.to;
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      onClick={() => setShowSidebarDrawer(false)}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold ${
                        isActive
                          ? 'bg-[#E6F0EE] text-[#0F5147]'
                          : 'text-stone-700 hover:bg-[#F4F2EC]'
                      }`}
                    >
                      <Icon className="w-4 h-4 text-[#0F5147]" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>

              <div className="pt-4 border-t border-stone-100">
                <button
                  onClick={logout}
                  className="w-full px-3 py-2.5 text-left text-sm font-semibold text-[#BE123C] hover:bg-[#FFE4E6] rounded-xl flex items-center gap-2 cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  <span>{t('nav.sign_out', 'Sign out')}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <main id="main-content" className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Outlet />
        </main>
      </div>

      {/* Healthcare Assistant Drawer */}
      <AssistantDrawer isOpen={showHelpModal} onClose={() => setShowHelpModal(false)} />
    </div>
  );
};

export default Layout;
