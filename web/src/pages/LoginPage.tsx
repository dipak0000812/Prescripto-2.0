import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck,
  Lock,
  Mail,
  Phone,
  KeyRound,
  User,
  AlertCircle,
  Loader2,
  ArrowRight,
  Stethoscope,
  HeartPulse,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { doctorLogin, sendOtp, loginWithOtp } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Active tab: 'patient' or 'doctor'
  const [authMode, setAuthMode] = useState<'patient' | 'doctor'>('patient');

  // Patient OTP State
  const [phoneNumber, setPhoneNumber] = useState<string>('9876543210');
  const [patientName, setPatientName] = useState<string>('Rahul Verma');
  const [otp, setOtp] = useState<string>('');
  const [otpSent, setOtpSent] = useState<boolean>(false);
  const [otpInfoMessage, setOtpInfoMessage] = useState<string | null>(null);

  // Doctor / Staff State
  const [email, setEmail] = useState<string>('doctor.sharma@prescripto.local');
  const [password, setPassword] = useState<string>('DoctorPass123!');

  // Common UI State
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const fromState = (location.state as any)?.from?.pathname;

  // Handle Patient Send OTP
  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumber.trim()) {
      setError('Please enter your 10-digit mobile number.');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await sendOtp(phoneNumber.trim());
      setOtpSent(true);
      setOtp(res.mock_otp || '123456');
      setOtpInfoMessage(`OTP sent to +91 ${phoneNumber.slice(-10)}. Test OTP is ${res.mock_otp || '123456'}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to send OTP. Please check mobile number.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Patient Verify OTP
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp.trim()) {
      setError('Please enter the 6-digit OTP code.');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await loginWithOtp(phoneNumber.trim(), otp.trim(), patientName.trim());
      const destination = fromState && fromState !== '/' && fromState !== '/login' ? fromState : '/patient-portal';
      navigate(destination, { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Invalid OTP code. Please use 123456 for testing.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Doctor / Staff Login
  const handleDoctorLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Please enter your email and password.');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await doctorLogin(email.trim(), password);
      const destination = fromState && fromState !== '/' && fromState !== '/login' && fromState !== '/patient-portal' ? fromState : '/prescriptions';
      navigate(destination, { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Invalid email or password. Please verify your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick Presets
  const setPatientPreset = (phone: string, name: string) => {
    setPhoneNumber(phone);
    setPatientName(name);
    setOtpSent(false);
    setOtp('');
    setError(null);
    setOtpInfoMessage(null);
  };

  const setDoctorPreset = (em: string, pw: string) => {
    setEmail(em);
    setPassword(pw);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-lg">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-teal-600 text-white shadow-xs mb-3 hover:bg-teal-700 transition">
            <HeartPulse className="w-7 h-7" />
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center justify-center gap-2">
            Prescripto <span>2.0</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Clinical Document Intelligence & Patient Safety Platform
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white border border-slate-200 rounded-2xl shadow-xs p-7 sm:p-9">
          {/* Top Tabs: Patient vs Doctor */}
          <div className="grid grid-cols-2 p-1 bg-slate-100 rounded-xl mb-6 border border-slate-200">
            <button
              type="button"
              onClick={() => {
                setAuthMode('patient');
                setError(null);
              }}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition ${
                authMode === 'patient'
                  ? 'bg-white text-teal-900 shadow-2xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <User className="w-4 h-4 text-teal-600" />
              <span>Patient Login</span>
              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-teal-50 text-teal-800 border border-teal-200">OTP</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setAuthMode('doctor');
                setError(null);
              }}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg text-xs font-semibold transition ${
                authMode === 'doctor'
                  ? 'bg-white text-indigo-900 shadow-2xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Stethoscope className="w-4 h-4 text-indigo-600" />
              <span>Doctor & Staff</span>
              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-800 border border-indigo-200">Email</span>
            </button>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-5 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="leading-relaxed font-medium">{error}</div>
            </div>
          )}

          {/* Info Banner */}
          {otpInfoMessage && authMode === 'patient' && (
            <div className="mb-5 p-3.5 bg-teal-50 border border-teal-200 rounded-xl text-xs text-teal-800 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
              <div className="leading-relaxed font-medium">{otpInfoMessage}</div>
            </div>
          )}

          {/* ================= PATIENT AUTH FLOW ================= */}
          {authMode === 'patient' && (
            <div>
              {!otpSent ? (
                /* Step 1: Enter Phone Number */
                <form onSubmit={handleSendOtp} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                      Mobile Number
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 font-medium text-xs">
                        <Phone className="w-4 h-4 text-slate-400 mr-1.5" />
                        <span>+91</span>
                      </div>
                      <input
                        type="tel"
                        required
                        maxLength={10}
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, ''))}
                        className="w-full pl-16 pr-4 py-2.5 text-sm font-medium bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 transition"
                        placeholder="9876543210"
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">
                      We will send a 6-digit verification code to this mobile number.
                    </p>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                      Patient Full Name
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <User className="w-4 h-4" />
                      </div>
                      <input
                        type="text"
                        value={patientName}
                        onChange={(e) => setPatientName(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 text-sm font-medium bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 transition"
                        placeholder="e.g. Rahul Verma"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-xs transition disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Sending OTP...</span>
                      </>
                    ) : (
                      <>
                        <span>Get Verification OTP</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>
              ) : (
                /* Step 2: Enter OTP */
                <form onSubmit={handleVerifyOtp} className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
                        Enter 6-Digit OTP
                      </label>
                      <button
                        type="button"
                        onClick={() => setOtpSent(false)}
                        className="text-xs font-medium text-teal-700 hover:text-teal-800 underline"
                      >
                        Change Number
                      </button>
                    </div>

                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <KeyRound className="w-4 h-4" />
                      </div>
                      <input
                        type="text"
                        required
                        maxLength={6}
                        value={otp}
                        onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                        className="w-full pl-10 pr-4 py-2.5 text-base tracking-widest font-mono font-bold bg-white border border-slate-300 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-600/20 focus:border-teal-600 transition"
                        placeholder="123456"
                      />
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-[11px] text-slate-500">Test OTP Code: <strong className="font-mono text-teal-700">123456</strong></span>
                      <button
                        type="button"
                        onClick={() => setOtp('123456')}
                        className="text-[11px] font-semibold text-teal-800 hover:text-teal-900 bg-teal-50 px-2 py-0.5 rounded border border-teal-200"
                      >
                        Auto Fill 123456
                      </button>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-xl shadow-xs transition disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Verifying Session...</span>
                      </>
                    ) : (
                      <>
                        <span>Verify & Enter Patient Portal</span>
                        <CheckCircle2 className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>
              )}

              {/* Patient Quick Demo Profiles */}
              <div className="mt-6 pt-5 border-t border-slate-100">
                <div className="flex items-center gap-1.5 mb-2.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    Quick Demo Profiles
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => setPatientPreset('9876543210', 'Rahul Verma')}
                    className="p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition"
                  >
                    <span className="font-bold text-slate-900 block text-xs">Rahul Verma</span>
                    <span className="text-[10px] text-slate-500 font-mono">98765 43210 &bull; PAT-1001</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setPatientPreset('9812345678', 'Pooja Sharma')}
                    className="p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition"
                  >
                    <span className="font-bold text-slate-900 block text-xs">Pooja Sharma</span>
                    <span className="text-[10px] text-slate-500 font-mono">98123 45678 &bull; PAT-1002</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ================= DOCTOR & STAFF AUTH FLOW ================= */}
          {authMode === 'doctor' && (
            <div>
              <form onSubmit={handleDoctorLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Doctor / Staff Email
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      type="text"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 text-xs font-medium bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 transition"
                      placeholder="e.g. doctor.sharma@prescripto.local"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 text-xs bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 transition"
                      placeholder="Enter clinical access password"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full mt-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl shadow-xs transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Authenticating...</span>
                    </>
                  ) : (
                    <>
                      <span>Sign In to Clinical Console</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Staff Presets */}
              <div className="mt-6 pt-5 border-t border-slate-100">
                <span className="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Demo Clinical Roles
                </span>
                <div className="space-y-1.5 text-xs">
                  <button
                    type="button"
                    onClick={() => setDoctorPreset('doctor.sharma@prescripto.local', 'DoctorPass123!')}
                    className="w-full p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left flex items-center justify-between transition"
                  >
                    <div>
                      <span className="font-bold text-slate-900">Dr. Ananya Sharma, MD</span>
                      <span className="text-[10px] text-slate-500 block">Doctor &bull; Full Clinical Review & Patient History</span>
                    </div>
                    <span className="text-[10px] font-semibold text-indigo-800 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                      Doctor
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setDoctorPreset('reviewer@prescripto.local', 'ReviewerPass123!')}
                    className="w-full p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left flex items-center justify-between transition"
                  >
                    <div>
                      <span className="font-bold text-slate-900">Clinical Reviewer</span>
                      <span className="text-[10px] text-slate-500 block">Pharmacist &bull; Review Queue & Audit Sign-Off</span>
                    </div>
                    <span className="text-[10px] font-semibold text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      Reviewer
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setDoctorPreset('admin@prescripto.local', 'AdminPass123!')}
                    className="w-full p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left flex items-center justify-between transition"
                  >
                    <div>
                      <span className="font-bold text-slate-900">Hospital Administrator</span>
                      <span className="text-[10px] text-slate-500 block">Admin &bull; Full System Health, Models & Audit</span>
                    </div>
                    <span className="text-[10px] font-semibold text-purple-800 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                      Admin
                    </span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="mt-6 text-center text-xs text-slate-500 flex items-center justify-center gap-3">
          <span className="inline-flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
            Secure Authentication
          </span>
          <span>&bull;</span>
          <span>Zero-PHI Transmission</span>
          <span>&bull;</span>
          <span>DPDPA 2023 Compliant</span>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
