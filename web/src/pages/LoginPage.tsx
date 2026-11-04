import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage, Language } from '../context/LanguageContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { AlertBanner } from '../components/ui/AlertBanner';
import {
  Phone,
  KeyRound,
  User,
  Mail,
  Lock,
  Camera,
  Clock,
  Volume2,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Stethoscope,
  RotateCcw,
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { doctorLogin, sendOtp, loginWithOtp } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();

  // Active mode: 'patient' or 'doctor'
  const [authMode, setAuthMode] = useState<'patient' | 'doctor'>('patient');

  // Patient OTP State
  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [patientName, setPatientName] = useState<string>('');
  const [otp, setOtp] = useState<string>('');
  const [otpSent, setOtpSent] = useState<boolean>(false);
  const [otpInfoMessage, setOtpInfoMessage] = useState<string | null>(null);

  // Doctor / Staff State
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');

  // Common UI State
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const fromState = (location.state as any)?.from?.pathname;

  const languages: { code: Language; nativeName: string; label: string }[] = [
    { code: 'en', nativeName: 'English', label: 'English' },
    { code: 'hi', nativeName: 'हिन्दी', label: 'Hindi' },
    { code: 'gu', nativeName: 'ગુજરાતી', label: 'Gujarati' },
    { code: 'mr', nativeName: 'मराठी', label: 'Marathi' },
  ];

  // Handle Patient Send OTP
  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanNumber = phoneNumber.replace(/\D/g, '').trim();
    if (cleanNumber.length < 10) {
      setError(t('auth.error_phone_required', 'Please enter your 10-digit mobile number.'));
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await sendOtp(cleanNumber);
      setOtpSent(true);
      const code = res.mock_otp || '123456';
      setOtp(code);
      setOtpInfoMessage(`${t('auth.test_mode_notice', 'Test Mode: Use verification code 123456')}`);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Could not send code. Please check your number and tap Send again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Patient Verify OTP
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanOtp = otp.replace(/\D/g, '').trim();
    if (!cleanOtp) {
      setError(t('auth.error_otp_required', 'Please enter the 6-digit code received on your phone.'));
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await loginWithOtp(phoneNumber.trim(), cleanOtp, patientName.trim());
      const destination =
        fromState && fromState !== '/' && fromState !== '/login' ? fromState : '/patient-portal';
      navigate(destination, { replace: true });
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'The code does not match. Please use code 123456 or tap Resend.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Doctor / Staff Login
  const handleDoctorLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError(t('auth.error_credentials_required', 'Please enter both email and password.'));
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await doctorLogin(email.trim(), password);
      const destination =
        fromState && fromState !== '/' && fromState !== '/login' && fromState !== '/patient-portal'
          ? fromState
          : '/prescriptions';
      navigate(destination, { replace: true });
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Email or password incorrect. Please check and try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF9F6] text-[#1C252E] flex flex-col justify-between py-6 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-lg mx-auto">
        {/* Brand Header */}
        <div className="text-center mb-6">
          <Link to="/" className="inline-flex items-center gap-2 mb-2 group">
            <div className="w-10 h-10 rounded-xl bg-[#0F5147] text-white flex items-center justify-center shadow-2xs group-hover:bg-[#0A3831] transition">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-[#1C252E]">
              Prescripto <span className="text-[#0F5147]">2.0</span>
            </span>
          </Link>
          <p className="text-sm text-stone-600">
            {t('auth.welcome_subtitle', 'Log in with your mobile number to view and listen to your prescribed medicines.')}
          </p>
        </div>

        {/* 1. Language Pick (Big Script-Named Buttons on First Screen) */}
        <div className="mb-6 bg-white border border-stone-200 rounded-xl p-3 sm:p-4 shadow-2xs">
          <label className="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-2 text-center">
            {t('auth.pick_language', 'Choose your language')}
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" role="group" aria-label="Select Language">
            {languages.map((l) => {
              const isSelected = language === l.code;
              return (
                <button
                  key={l.code}
                  type="button"
                  onClick={() => setLanguage(l.code)}
                  aria-pressed={isSelected}
                  className={`min-h-[48px] px-3 py-2 rounded-xl text-sm font-semibold transition flex flex-col items-center justify-center cursor-pointer border ${
                    isSelected
                      ? 'bg-[#0F5147] text-white border-[#0F5147] shadow-2xs'
                      : 'bg-[#FAF9F6] text-[#1C252E] border-stone-200 hover:bg-[#F4F2EC]'
                  }`}
                >
                  <span className="text-base font-bold leading-tight">{l.nativeName}</span>
                  <span className={`text-[11px] ${isSelected ? 'text-emerald-100' : 'text-stone-500'}`}>
                    {l.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2. Main Login / OTP Card */}
        <div className="bg-white border border-stone-200 rounded-xl p-5 sm:p-7 shadow-2xs mb-6">
          {/* Calm Mode Switcher: Patient OTP (Default) vs Staff */}
          <div className="flex items-center justify-between border-b border-stone-200 pb-3 mb-5">
            <h2 className="text-lg font-bold text-[#1C252E]">
              {authMode === 'patient'
                ? otpSent
                  ? t('auth.otp_label', 'Enter 6-digit code')
                  : t('auth.welcome_title', 'Welcome to Prescripto')
                : t('auth.doctor_tab', 'Doctor & Staff')}
            </h2>

            <button
              type="button"
              onClick={() => {
                setAuthMode(authMode === 'patient' ? 'doctor' : 'patient');
                setError(null);
                setOtpSent(false);
              }}
              className="text-xs font-semibold text-[#0F5147] hover:underline flex items-center gap-1 cursor-pointer min-h-[36px]"
            >
              {authMode === 'patient' ? (
                <>
                  <Stethoscope className="w-3.5 h-3.5" />
                  <span>{t('auth.doctor_tab', 'Doctor & Staff')}</span>
                </>
              ) : (
                <>
                  <User className="w-3.5 h-3.5" />
                  <span>{t('auth.patient_tab', 'Patient (Mobile OTP)')}</span>
                </>
              )}
            </button>
          </div>

          {/* Error Banner with Plain Words + Retry Guidance */}
          {error && (
            <div className="mb-4">
              <AlertBanner
                type="error"
                title="Please check"
                badgeLabel="Problem"
                action={
                  <button
                    type="button"
                    onClick={() => setError(null)}
                    className="text-xs font-semibold text-[#BE123C] hover:underline flex items-center gap-1 cursor-pointer mt-1"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Dismiss and try again</span>
                  </button>
                }
              >
                {error}
              </AlertBanner>
            </div>
          )}

          {/* Info Banner for Test Mode */}
          {otpInfoMessage && authMode === 'patient' && (
            <div className="mb-4">
              <AlertBanner type="info" title="Test Mode" badgeLabel="Note">
                {otpInfoMessage}
              </AlertBanner>
            </div>
          )}

          {/* ================= PATIENT AUTH FLOW ================= */}
          {authMode === 'patient' && (
            <div>
              {!otpSent ? (
                /* Step 1: Enter Phone Number */
                <form onSubmit={handleSendOtp} className="space-y-4">
                  <div>
                    <label
                      htmlFor="patient-phone"
                      className="block text-sm font-semibold text-[#1C252E] mb-1.5"
                    >
                      {t('auth.phone_label', 'Your 10-digit mobile number')} <span className="text-[#BE123C]">*</span>
                    </label>

                    <div className="relative flex items-center">
                      <div className="absolute left-3.5 flex items-center gap-1.5 text-stone-600 font-semibold text-base pointer-events-none">
                        <Phone className="w-5 h-5 text-stone-500" aria-hidden="true" />
                        <span>+91</span>
                      </div>
                      <input
                        id="patient-phone"
                        type="tel"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        autoComplete="tel-national"
                        required
                        maxLength={10}
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, ''))}
                        className="w-full pl-20 pr-4 py-3 min-h-[52px] text-lg font-semibold bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147] focus-visible:border-[#0F5147]"
                        placeholder={t('auth.phone_placeholder', 'e.g. 9876543210')}
                      />
                    </div>
                  </div>

                  <div>
                    <label
                      htmlFor="patient-name"
                      className="block text-sm font-semibold text-[#1C252E] mb-1.5"
                    >
                      {t('auth.patient_name_label', 'Patient name (optional)')}
                    </label>
                    <div className="relative flex items-center">
                      <div className="absolute left-3.5 text-stone-500 pointer-events-none">
                        <User className="w-5 h-5" aria-hidden="true" />
                      </div>
                      <input
                        id="patient-name"
                        type="text"
                        autoComplete="name"
                        value={patientName}
                        onChange={(e) => setPatientName(e.target.value)}
                        className="w-full pl-11 pr-4 py-3 min-h-[48px] text-base bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147] focus-visible:border-[#0F5147]"
                        placeholder={t('auth.patient_name_placeholder', 'e.g. Rahul Sharma')}
                      />
                    </div>
                  </div>

                  <div className="pt-2">
                    <Button
                      type="submit"
                      variant="primary"
                      size="lg"
                      isLoading={isSubmitting}
                      className="w-full min-h-[52px] text-base"
                      rightIcon={<ArrowRight className="w-5 h-5" />}
                    >
                      {t('auth.send_otp_btn', 'Send Verification Code')}
                    </Button>
                  </div>
                </form>
              ) : (
                /* Step 2: Enter OTP */
                <form onSubmit={handleVerifyOtp} className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label
                        htmlFor="patient-otp"
                        className="block text-sm font-semibold text-[#1C252E]"
                      >
                        {t('auth.otp_label', 'Enter 6-digit code')} <span className="text-[#BE123C]">*</span>
                      </label>
                      <button
                        type="button"
                        onClick={() => {
                          setOtpSent(false);
                          setError(null);
                        }}
                        className="text-xs font-semibold text-[#0F5147] hover:underline cursor-pointer"
                      >
                        {t('auth.change_number', 'Change mobile number')}
                      </button>
                    </div>

                    <div className="relative flex items-center">
                      <div className="absolute left-3.5 text-stone-500 pointer-events-none">
                        <KeyRound className="w-5 h-5" aria-hidden="true" />
                      </div>
                      <input
                        id="patient-otp"
                        type="tel"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        autoComplete="one-time-code"
                        required
                        maxLength={6}
                        value={otp}
                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                        className="w-full pl-11 pr-4 py-3 min-h-[52px] text-xl font-bold font-mono tracking-widest bg-white border border-stone-300 rounded-xl text-[#1C252E] placeholder:text-stone-400 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147] focus-visible:border-[#0F5147]"
                        placeholder="123456"
                      />
                    </div>

                    <div className="mt-3 flex items-center justify-between bg-[#F4F2EC] p-2.5 rounded-xl border border-stone-200">
                      <span className="text-xs text-stone-700">
                        Code: <strong className="font-mono text-[#0F5147]">123456</strong>
                      </span>
                      <button
                        type="button"
                        onClick={() => setOtp('123456')}
                        className="text-xs font-semibold text-[#0F5147] bg-white px-2.5 py-1 rounded-lg border border-stone-300 hover:bg-[#FAF9F6] cursor-pointer"
                      >
                        {t('auth.autofill_btn', 'Autofill 123456')}
                      </button>
                    </div>
                  </div>

                  <div className="pt-2">
                    <Button
                      type="submit"
                      variant="primary"
                      size="lg"
                      isLoading={isSubmitting}
                      className="w-full min-h-[52px] text-base"
                      rightIcon={<CheckCircle2 className="w-5 h-5" />}
                    >
                      {t('auth.verify_otp_btn', 'Verify Code & View Medicines')}
                    </Button>
                  </div>
                </form>
              )}
            </div>
          )}

          {/* ================= DOCTOR & STAFF AUTH FLOW ================= */}
          {authMode === 'doctor' && (
            <form onSubmit={handleDoctorLogin} className="space-y-4">
              <div>
                <Input
                  label={t('auth.doctor_email', 'Staff Email')}
                  id="staff-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  leftIcon={<Mail className="w-5 h-5" />}
                  placeholder="doctor@hospital.org"
                />
              </div>

              <div>
                <Input
                  label={t('auth.doctor_password', 'Password')}
                  id="staff-password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  leftIcon={<Lock className="w-5 h-5" />}
                  placeholder="••••••••"
                />
              </div>

              <div className="pt-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  isLoading={isSubmitting}
                  className="w-full min-h-[52px] text-base"
                  rightIcon={<ArrowRight className="w-5 h-5" />}
                >
                  {t('auth.doctor_login_btn', 'Sign In to Clinical Console')}
                </Button>
              </div>
            </form>
          )}
        </div>

        {/* 3. Calm 3-Step "How It Works" Section */}
        <div className="bg-white border border-stone-200 rounded-xl p-5 shadow-2xs mb-6">
          <h3 className="text-sm font-bold uppercase tracking-wider text-stone-600 mb-3">
            {t('auth.how_it_works_title', 'How Prescripto works')}
          </h3>

          <div className="space-y-3 text-sm">
            {/* Step 1 */}
            <div className="flex items-start gap-3 p-2.5 rounded-xl bg-[#FAF9F6] border border-stone-200">
              <div className="w-9 h-9 rounded-lg bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center shrink-0">
                <Camera className="w-5 h-5" aria-hidden="true" />
              </div>
              <div>
                <h4 className="font-bold text-[#1C252E]">{t('auth.step1_title', '1. Upload Prescription')}</h4>
                <p className="text-xs text-stone-600 mt-0.5 leading-relaxed">
                  {t('auth.step1_desc', "Take a clear picture of your doctor's slip.")}
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex items-start gap-3 p-2.5 rounded-xl bg-[#FAF9F6] border border-stone-200">
              <div className="w-9 h-9 rounded-lg bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center shrink-0">
                <Clock className="w-5 h-5" aria-hidden="true" />
              </div>
              <div>
                <h4 className="font-bold text-[#1C252E]">{t('auth.step2_title', '2. We Organize It')}</h4>
                <p className="text-xs text-stone-600 mt-0.5 leading-relaxed">
                  {t('auth.step2_desc', 'We read the names, doses, and times for you.')}
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex items-start gap-3 p-2.5 rounded-xl bg-[#FAF9F6] border border-stone-200">
              <div className="w-9 h-9 rounded-lg bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center shrink-0">
                <Volume2 className="w-5 h-5" aria-hidden="true" />
              </div>
              <div>
                <h4 className="font-bold text-[#1C252E]">{t('auth.step3_title', '3. See & Listen')}</h4>
                <p className="text-xs text-stone-600 mt-0.5 leading-relaxed">
                  {t('auth.step3_desc', 'Understand morning, afternoon, and night timings with voice.')}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Reassuring Privacy & Safety Note */}
        <p className="text-xs text-center text-stone-500 leading-relaxed max-w-sm mx-auto mb-4">
          {t('auth.safety_note', 'Your medical data is private and confidential.')}
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
