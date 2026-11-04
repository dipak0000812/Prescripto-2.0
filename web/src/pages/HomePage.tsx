import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  ShieldCheck,
  Camera,
  Clock,
  Volume2,
  Lock,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/Button';
import { LanguageSwitcher } from '../components/LanguageSwitcher';

export const HomePage: React.FC = () => {
  const { session } = useAuth();
  const { t } = useLanguage();
  const uploadDestination = session ? '/upload' : '/login';

  return (
    <div className="min-h-screen bg-[#FAF9F6] text-[#1C252E] flex flex-col selection:bg-[#E6F0EE] selection:text-[#0F5147]">
      {/* Top Header & Language Picker */}
      <header className="border-b border-stone-200 bg-white sticky top-0 z-30 shadow-2xs">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Link
            to="/"
            className="flex items-center gap-2.5 text-[#1C252E] focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147] rounded-xl p-1"
          >
            <div className="w-9 h-9 rounded-xl bg-[#0F5147] text-white flex items-center justify-center font-bold shadow-2xs">
              <ShieldCheck className="w-5 h-5" aria-hidden="true" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              Prescripto <span className="text-[#0F5147]">2.0</span>
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <LanguageSwitcher />

            {session ? (
              <Link to={session.is_patient ? '/patient-portal' : '/prescriptions'}>
                <Button variant="secondary" size="sm">
                  {t('nav.my_portal', 'My Health Portal')}
                </Button>
              </Link>
            ) : (
              <Link to="/login">
                <Button variant="outline" size="sm">
                  {t('nav.sign_in', 'Sign In')}
                </Button>
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* HERO SECTION: Calm, warm, Class 6 reading level */}
        <section className="mx-auto max-w-6xl px-4 pt-10 pb-12 sm:px-6 sm:pt-16 sm:pb-20">
          <div className="grid gap-10 lg:grid-cols-12 lg:items-center">
            {/* Left Column: Clear headline, empathetic reassurance, 1 primary action */}
            <div className="lg:col-span-7 space-y-6 text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-xl bg-[#E6F0EE] border border-[#9DC1BB] text-[#0F5147] text-xs font-semibold">
                <ShieldCheck className="w-4 h-4 text-[#0F5147]" aria-hidden="true" />
                <span>Simple Medication Guide</span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-[#1C252E] leading-tight">
                Upload your doctor's prescription. We'll explain it simply.
              </h1>

              <p className="text-base sm:text-lg text-stone-700 leading-relaxed max-w-2xl">
                Take a photo of your prescription slip. We organize medicine names, doses, and exact morning, afternoon, and night timings into clear cards you can read and listen to.
              </p>

              {/* Primary Action Button (Only 1 primary, 1 secondary max) */}
              <div className="pt-2 flex flex-wrap items-center gap-3.5">
                <Link to={uploadDestination} className="w-full sm:w-auto">
                  <Button
                    size="lg"
                    variant="primary"
                    className="w-full sm:w-auto min-h-[52px] text-base"
                    rightIcon={<ArrowRight className="w-5 h-5" aria-hidden="true" />}
                  >
                    {session ? t('nav.new_intake', 'Upload Prescription') : t('auth.send_otp_btn', 'Get Started with Mobile OTP')}
                  </Button>
                </Link>

                <a href="#how-it-works" className="w-full sm:w-auto">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto min-h-[52px] text-base">
                    {t('auth.how_it_works_title', 'How it works')}
                  </Button>
                </a>
              </div>

              {/* Safety Reassurance in plain words */}
              <div className="pt-3 border-t border-stone-200 max-w-xl">
                <div className="flex items-start gap-3 text-xs sm:text-sm text-stone-700 bg-white p-4 rounded-xl border border-stone-200">
                  <AlertTriangle className="w-5 h-5 text-[#B45309] shrink-0 mt-0.5" aria-hidden="true" />
                  <span className="leading-relaxed">
                    <strong>Please remember:</strong> This is a computer reading of your prescription. Always confirm medicines with your doctor or chemist before taking them.
                  </span>
                </div>
              </div>
            </div>

            {/* Right Column: Visual Preview Card */}
            <div className="lg:col-span-5">
              <div className="bg-white rounded-xl border border-stone-200 p-5 sm:p-6 shadow-2xs space-y-4 text-left">
                <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                  <span className="text-xs font-bold text-stone-600 uppercase tracking-wider">
                    Example Medicine Card
                  </span>
                  <span className="text-xs font-semibold text-[#0F5147] bg-[#E6F0EE] px-2.5 py-0.5 rounded-lg border border-[#9DC1BB]">
                    Clear Schedule
                  </span>
                </div>

                {/* Example of clear schedule layout */}
                <div className="p-4 bg-[#FAF9F6] rounded-xl border border-stone-200 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-base text-[#1C252E]">Paracetamol 650mg</span>
                    <span className="text-xs font-semibold text-[#047857] bg-[#ECFDF5] px-2 py-0.5 rounded border border-[#A7F3D0]">
                      Tablet
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="bg-white p-2 rounded-lg border border-stone-200">
                      <span className="block text-stone-500 font-medium">Morning</span>
                      <strong className="text-[#0F5147]">1 Tab</strong>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-stone-200">
                      <span className="block text-stone-500 font-medium">Afternoon</span>
                      <span className="text-stone-400">—</span>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-stone-200">
                      <span className="block text-stone-500 font-medium">Night</span>
                      <strong className="text-[#0F5147]">1 Tab</strong>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs pt-1">
                    <span className="text-stone-600">Take after food · 5 days</span>
                    <span className="text-[#0F5147] font-semibold flex items-center gap-1">
                      <Volume2 className="w-3.5 h-3.5" /> Listen
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-[#FFFBEB] rounded-xl border border-amber-300 text-xs text-amber-950 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-[#B45309] shrink-0 mt-0.5" />
                  <span>Unclear handwriting is always flagged for your safety so you can check it.</span>
                </div>

                <div className="pt-1 text-xs text-stone-500 flex items-center gap-2">
                  <Lock className="w-4 h-4 text-stone-400 shrink-0" aria-hidden="true" />
                  <span>Private and secure. Photos are never shared publicly.</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 3-STEP EXPLANATION */}
        <section id="how-it-works" className="scroll-mt-16 border-y border-stone-200 bg-white py-12 sm:py-16">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 text-left">
            <div className="max-w-2xl">
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1C252E]">
                {t('auth.how_it_works_title', 'How Prescripto works')}
              </h2>
              <p className="mt-2 text-sm sm:text-base text-stone-600 leading-relaxed">
                Three simple steps designed for normal people and families.
              </p>
            </div>

            <ol className="mt-8 grid gap-6 md:grid-cols-3">
              {/* Step 1 */}
              <li className="bg-[#FAF9F6] rounded-xl border border-stone-200 p-6 flex flex-col justify-between">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-[#E6F0EE] border border-[#9DC1BB] flex items-center justify-center text-[#0F5147] font-bold mb-4">
                    <Camera className="w-6 h-6" aria-hidden="true" />
                  </div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[#0F5147] block mb-1">
                    Step 1
                  </span>
                  <h3 className="text-base font-bold text-[#1C252E]">
                    {t('auth.step1_title', '1. Upload Prescription')}
                  </h3>
                  <p className="mt-2 text-xs sm:text-sm text-stone-600 leading-relaxed">
                    {t('auth.step1_desc', "Take a clear picture of your doctor's slip.")}
                  </p>
                </div>
              </li>

              {/* Step 2 */}
              <li className="bg-[#FAF9F6] rounded-xl border border-stone-200 p-6 flex flex-col justify-between">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-[#E6F0EE] border border-[#9DC1BB] flex items-center justify-center text-[#0F5147] font-bold mb-4">
                    <Clock className="w-6 h-6" aria-hidden="true" />
                  </div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[#0F5147] block mb-1">
                    Step 2
                  </span>
                  <h3 className="text-base font-bold text-[#1C252E]">
                    {t('auth.step2_title', '2. We Organize It')}
                  </h3>
                  <p className="mt-2 text-xs sm:text-sm text-stone-600 leading-relaxed">
                    {t('auth.step2_desc', 'We read the names, doses, and times for you.')}
                  </p>
                </div>
              </li>

              {/* Step 3 */}
              <li className="bg-[#FAF9F6] rounded-xl border border-stone-200 p-6 flex flex-col justify-between">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] flex items-center justify-center text-[#047857] font-bold mb-4">
                    <Volume2 className="w-6 h-6" aria-hidden="true" />
                  </div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[#047857] block mb-1">
                    Step 3
                  </span>
                  <h3 className="text-base font-bold text-[#1C252E]">
                    {t('auth.step3_title', '3. See & Listen')}
                  </h3>
                  <p className="mt-2 text-xs sm:text-sm text-stone-600 leading-relaxed">
                    {t('auth.step3_desc', 'Understand morning, afternoon, and night timings with voice.')}
                  </p>
                </div>
              </li>
            </ol>
          </div>
        </section>
      </main>

      <footer className="border-t border-stone-200 bg-white py-6 text-center text-xs text-stone-500">
        <div className="mx-auto max-w-6xl px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <span>Prescripto 2.0 · Medication Timing & Prescription Organization Aid</span>
          <span className="text-stone-400">
            Verify all extracted details with a licensed physician or pharmacist.
          </span>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
