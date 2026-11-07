import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ShieldCheck,
  Camera,
  Clock,
  Volume2,
  VolumeX,
  Lock,
  AlertTriangle,
  CheckCircle2,
  Stethoscope,
  Heart,
  Globe,
  Sparkles,
  ChevronDown,
  ChevronUp,
  PhoneCall,
  FileText,
  Users,
  Check,
  ExternalLink,
  Scan,
  Maximize2,
  Layers,
  HelpCircle,
  Activity,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/Button';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import {
  TabletIcon,
  CapsuleIcon,
  SyrupIcon,
  SunriseIcon,
  MiddaySunIcon,
  MoonIcon,
  ShieldSafetyIcon,
  CheckmarkIcon,
  AlertAmberIcon,
} from '../components/icons/HealthcareIcons';

export const HomePage: React.FC = () => {
  const { session } = useAuth();
  const { language, setLanguage, speak, isSpeaking, stopSpeaking, t } = useLanguage();
  const navigate = useNavigate();

  const uploadDestination = session ? '/upload' : '/login';

  // Interactive showcase state: 'scan' vs 'card'
  const [activeHeroTab, setActiveHeroTab] = useState<'both' | 'photo' | 'digital'>('both');
  const [selectedDemoMedicine, setSelectedDemoMedicine] = useState<'paracetamol' | 'amoxicillin'>('paracetamol');

  // FAQ Accordion State
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  // Audio sample state
  const handlePlaySampleAudio = () => {
    if (isSpeaking) {
      stopSpeaking();
      return;
    }

    if (selectedDemoMedicine === 'amoxicillin') {
      if (language === 'hi') {
        speak('अमोक्सिसिलिन 500 मिलीग्राम कैप्सूल। दिन में तीन बार खाना खाने के बाद 7 दिनों के लिए लें।');
      } else if (language === 'gu') {
        speak('એમોક્સિસિલિન 500 મિલીગ્રામ કેપ્સ્યુલ. દિવસમાં ત્રણ વખત જમ્યા પછી 7 દિવસ માટે લો.');
      } else if (language === 'mr') {
        speak('अमोक्सिसिलिन 500 मिग्रॅ कॅप्सूल. दिवसातून तीन वेळा जेवणानंतर 7 दिवसांसाठी घ्या.');
      } else {
        speak('Amoxicillin 500 milligram capsule. Take one capsule three times daily after food for seven days.');
      }
    } else {
      if (language === 'hi') {
        speak('पैरासिटामोल 650 मिलीग्राम। सुबह एक गोली और रात को एक गोली खाना खाने के बाद 5 दिनों के लिए लें।');
      } else if (language === 'gu') {
        speak('પેરાસિટામોલ 650 મિલીગ્રામ. સવારે એક ગોળી અને રાત્રે એક ગોળી જમ્યા પછી 5 દિવસ માટે લો.');
      } else if (language === 'mr') {
        speak('पॅरासिटामॉल 650 मिग्रॅ. सकाळी एक गोळी आणि रात्री एक गोळी जेवणानंतर 5 दिवसांसाठी घ्या.');
      } else {
        speak('Paracetamol 650 milligram tablet. Take one tablet in the morning and one tablet at night after food for five days.');
      }
    }
  };

  const faqs = [
    {
      q: 'Is my prescription and personal medical data private?',
      a: 'Yes, 100%. We comply strictly with the Digital Personal Data Protection (DPDPA) Act of 2023. Prescriptions are encrypted with AES-256 at rest and TLS 1.3 in transit. Your photos are never shared publicly or sold to third-party advertisers.',
    },
    {
      q: 'Which languages are supported for audio readouts?',
      a: 'Prescripto currently supports English, Hindi (हिन्दी), Gujarati (ગુજરાતી), and Marathi (मराठी). You can switch languages instantly with one tap from the header, and all medication instructions will be read aloud.',
    },
    {
      q: 'What happens if the doctor handwriting is very messy or unreadable?',
      a: 'We follow a strict medical safety rule: Upstream uncertainty is never hidden. When a word, dose, or frequency is faded or ambiguous, it is highlighted in amber as "Please check this" and linked directly to the original photo for your safety.',
    },
    {
      q: 'Is Prescripto free for patients and families?',
      a: 'Yes. Prescripto is completely free for patients, seniors, and families across India to digitize, organize, and listen to their prescriptions.',
    },
    {
      q: 'Can doctors, pharmacists, and clinics use Prescripto?',
      a: 'Yes! Healthcare professionals can log into the dedicated Doctor & Staff Portal to access the Clinical Review Queue, inspect prescriptions side-by-side with original images, and sign off on verified records.',
    },
  ];

  return (
    <div className="min-h-screen bg-[#FAF9F6] text-[#1C252E] flex flex-col selection:bg-[#E6F0EE] selection:text-[#0F5147]">
      {/* 1. TOP NOTICE & EMERGENCY HELPLINE BANNER */}
      <aside aria-label="National Helpline" className="bg-[#0A3831] text-emerald-100 text-xs py-2 px-4 border-b border-emerald-900/40">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-semibold text-white">National Healthcare Utility:</span>
            <span>Free digital prescription assistant for patients across India</span>
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <a
              href="tel:112"
              className="flex items-center gap-1 text-emerald-200 hover:text-white transition font-medium"
            >
              <PhoneCall className="w-3 h-3 text-emerald-400" />
              <span>Emergency: <strong>112</strong></span>
            </a>
            <span className="text-emerald-700">|</span>
            <a
              href="tel:108"
              className="flex items-center gap-1 text-emerald-200 hover:text-white transition font-medium"
            >
              <PhoneCall className="w-3 h-3 text-emerald-400" />
              <span>Ambulance: <strong>108</strong></span>
            </a>
          </div>
        </div>
      </aside>

      {/* 2. MAIN HEADER NAVBAR */}
      <header className="border-b border-stone-200/80 bg-white/95 backdrop-blur-md sticky top-0 z-40 shadow-xs">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          {/* Brand Logo */}
          <Link
            to="/"
            className="flex items-center gap-2.5 text-[#1C252E] focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#0F5147] rounded-xl p-1"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0F5147] to-[#0A3831] text-white flex items-center justify-center font-bold shadow-xs">
              <ShieldCheck className="w-6 h-6 text-emerald-300" aria-hidden="true" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-extrabold tracking-tight text-[#1C252E]">
                Prescripto <span className="text-[#0F5147]">2.0</span>
              </span>
              <span className="text-[10px] font-semibold text-stone-500 uppercase tracking-wider -mt-0.5">
                Medication Intelligence
              </span>
            </div>
          </Link>

          {/* Center Navigation Links (Desktop) */}
          <nav className="hidden lg:flex items-center gap-6 text-sm font-semibold text-stone-600">
            <a href="#how-it-works" className="hover:text-[#0F5147] transition">How It Works</a>
            <a href="#comparison" className="hover:text-[#0F5147] transition">Visual Demo</a>
            <a href="#features" className="hover:text-[#0F5147] transition">Features</a>
            <a href="#safety" className="hover:text-[#0F5147] transition">Clinical Safety</a>
            <a href="#clinicians" className="hover:text-[#0F5147] transition">For Doctors</a>
            <a href="#faq" className="hover:text-[#0F5147] transition">FAQ</a>
          </nav>

          {/* Right Controls: Language Switcher & CTAs */}
          <div className="flex items-center gap-3">
            <LanguageSwitcher />

            {session ? (
              <Link to={session.is_patient ? '/patient-portal' : '/prescriptions'}>
                <Button variant="primary" size="sm" className="hidden sm:inline-flex">
                  {t('nav.my_portal', 'My Health Portal')}
                </Button>
              </Link>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login?mode=doctor" className="hidden sm:inline-block">
                  <Button variant="outline" size="sm" className="text-xs">
                    <Stethoscope className="w-3.5 h-3.5 mr-1 text-[#0F5147]" />
                    <span>Doctor Portal</span>
                  </Button>
                </Link>
                <Link to="/login">
                  <Button variant="primary" size="sm" className="font-bold">
                    {t('nav.sign_in', 'Sign In')}
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* 3. HERO SECTION WITH RICH MESH BACKGROUND & VISUAL SHOWCASE */}
        <section className="relative overflow-hidden pt-8 pb-16 sm:pt-14 sm:pb-24 border-b border-stone-200/90 bg-gradient-to-br from-[#F5F8F7] via-[#FAF9F6] to-[#EBF3F1]">
          {/* Subtle medical dot grid overlay */}
          <div
            className="absolute inset-0 pointer-events-none opacity-[0.04]"
            style={{
              backgroundImage: 'radial-gradient(#0F5147 1px, transparent 1px)',
              backgroundSize: '24px 24px',
            }}
          />

          {/* Ambient glow orbs */}
          <div className="absolute top-10 right-1/4 w-[450px] h-[450px] bg-emerald-200/35 rounded-full blur-3xl pointer-events-none -z-10" />
          <div className="absolute bottom-5 left-10 w-[400px] h-[400px] bg-amber-200/30 rounded-full blur-3xl pointer-events-none -z-10" />

          <div className="mx-auto max-w-6xl px-4 sm:px-6 relative">
            <div className="grid gap-12 lg:grid-cols-12 lg:items-center">
              {/* Left Column: Value Proposition & CTAs */}
              <div className="lg:col-span-6 space-y-6 text-left">
                {/* Product Badge */}
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/90 backdrop-blur-md border border-[#9DC1BB] text-[#0F5147] text-xs font-bold tracking-wide shadow-2xs">
                  <Sparkles className="w-4 h-4 text-[#0F5147]" />
                  <span>AI Document Intelligence · Built for Indian Families</span>
                </div>

                {/* Primary Headline */}
                <h1 className="text-3xl sm:text-5xl lg:text-[3.25rem] font-extrabold tracking-tight text-[#1C252E] leading-[1.15]">
                  Never Guess Your Doctor's{' '}
                  <span className="text-[#0F5147] relative inline-block">
                    Handwriting
                    <svg
                      className="absolute -bottom-2 left-0 w-full h-3 text-[#9DC1BB]/60 -z-10"
                      viewBox="0 0 100 12"
                      preserveAspectRatio="none"
                    >
                      <path d="M0,8 Q50,0 100,8" stroke="currentColor" strokeWidth="6" fill="none" />
                    </svg>
                  </span>{' '}
                  Again.
                </h1>

                {/* Subtitle */}
                <p className="text-base sm:text-lg text-stone-700 leading-relaxed max-w-xl">
                  Snap a photo of your doctor's slip. Prescripto reads the handwritten lines, maps exact morning-afternoon-night doses, and explains everything spoken aloud in your language.
                </p>

                {/* Primary Action Buttons */}
                <div className="pt-2 flex flex-wrap items-center gap-3.5">
                  <Link to={uploadDestination} className="w-full sm:w-auto">
                    <Button
                      size="lg"
                      variant="primary"
                      className="w-full sm:w-auto min-h-[54px] text-base font-bold shadow-md hover:shadow-lg hover:-translate-y-0.5 transition-all"
                      leftIcon={<Camera className="w-5 h-5" />}
                      rightIcon={<ArrowRight className="w-5 h-5" />}
                    >
                      {session ? 'Upload Prescription Now' : 'Upload & Get Started (Mobile OTP)'}
                    </Button>
                  </Link>

                  <Link to="/login?mode=doctor" className="w-full sm:w-auto">
                    <Button
                      size="lg"
                      variant="outline"
                      className="w-full sm:w-auto min-h-[54px] text-base font-semibold border-stone-300 bg-white/80 hover:bg-white"
                      leftIcon={<Stethoscope className="w-5 h-5 text-[#0F5147]" />}
                    >
                      Doctor & Staff Portal
                    </Button>
                  </Link>
                </div>

                {/* Reassurance Checklist */}
                <div className="pt-3 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs sm:text-sm text-stone-700 font-medium">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>100% Free for Patients</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Voice in 4 Languages</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>DPDPA 2023 Compliant</span>
                  </div>
                </div>
              </div>

              {/* Right Column: RICH VISUAL SHOWCASE (PRESCRIPTION IMAGE + SCANNER OVERLAY + LIVE DIGITAL CARD) */}
              <div className="lg:col-span-6">
                <div className="relative">
                  {/* Outer decorative card shadow frame */}
                  <div className="absolute -inset-1.5 bg-gradient-to-r from-emerald-500/20 via-teal-500/20 to-amber-500/20 rounded-3xl blur-lg opacity-70" />

                  <div className="relative bg-white/95 backdrop-blur-md rounded-2xl border border-stone-200/90 shadow-2xl overflow-hidden text-left">
                    {/* Showcase Header Controls */}
                    <div className="bg-[#FAF9F6] border-b border-stone-200 px-4 py-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-xs font-bold text-stone-700 uppercase tracking-wider">
                          Prescription Transformation
                        </span>
                      </div>

                      {/* Medicine Selector Pills */}
                      <div className="flex items-center gap-1.5 bg-stone-200/70 p-1 rounded-xl text-xs font-semibold">
                        <button
                          type="button"
                          onClick={() => setSelectedDemoMedicine('paracetamol')}
                          className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                            selectedDemoMedicine === 'paracetamol'
                              ? 'bg-white text-[#0F5147] shadow-xs'
                              : 'text-stone-600 hover:text-stone-900'
                          }`}
                        >
                          Paracetamol
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelectedDemoMedicine('amoxicillin')}
                          className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                            selectedDemoMedicine === 'amoxicillin'
                              ? 'bg-white text-[#0F5147] shadow-xs'
                              : 'text-stone-600 hover:text-stone-900'
                          }`}
                        >
                          Amoxicillin
                        </button>
                      </div>
                    </div>

                    {/* TOP LAYER: Real Prescription Document with AI Scan Line */}
                    <div className="relative border-b border-stone-200 bg-stone-100 overflow-hidden">
                      {/* Real prescription preview slip */}
                      <div className="relative h-44 sm:h-48 overflow-hidden bg-white select-none">
                        <img
                          src="/sample_prescription.png"
                          alt="Doctor prescription document preview"
                          className="w-full h-full object-cover object-top opacity-90 contrast-[1.05]"
                        />

                        {/* Animated Laser Scanning Beam */}
                        <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-emerald-500 to-transparent shadow-[0_0_12px_#10B981] animate-bounce pointer-events-none" style={{ top: '48%' }} />

                        {/* Optical Bounding Box Over Detected Medication */}
                        <div className="absolute top-16 left-6 right-8 border-2 border-emerald-500 bg-emerald-500/10 rounded-md p-1.5 flex items-center justify-between shadow-xs">
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#0F5147] text-white tracking-wide uppercase">
                            <Scan className="w-3 h-3" />
                            {selectedDemoMedicine === 'paracetamol' ? 'Line 2 Detected (99.4%)' : 'Line 1 Detected (98.9%)'}
                          </span>
                          <span className="text-[10px] font-semibold text-emerald-900 bg-white/90 px-1.5 py-0.5 rounded border border-emerald-300">
                            Handwriting OCR
                          </span>
                        </div>

                        {/* Doctor Stamp watermark */}
                        <div className="absolute bottom-2 right-4 px-2.5 py-1 rounded-lg bg-white/95 border border-stone-300 text-[10px] font-semibold text-stone-600 shadow-xs flex items-center gap-1.5">
                          <Stethoscope className="w-3.5 h-3.5 text-[#0F5147]" />
                          <span>Dr. Ananya Sharma, MD</span>
                        </div>
                      </div>

                      {/* Transition Ribbon */}
                      <div className="bg-[#0F5147] text-white py-1 px-4 flex items-center justify-between text-[11px] font-bold">
                        <span className="flex items-center gap-1.5">
                          <Sparkles className="w-3 h-3 text-emerald-300" />
                          <span>AI Extracted & CDSCO Verified Result</span>
                        </span>
                        <span className="text-emerald-200 font-medium">Instant Conversion</span>
                      </div>
                    </div>

                    {/* BOTTOM LAYER: The Clean Structured Digitized Result Card */}
                    <div className="p-5 sm:p-6 space-y-4 bg-white">
                      {/* Medicine Info Header */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-11 h-11 rounded-xl bg-emerald-100 text-[#0F5147] flex items-center justify-center shrink-0 border border-emerald-200">
                            {selectedDemoMedicine === 'paracetamol' ? (
                              <TabletIcon size={24} />
                            ) : (
                              <CapsuleIcon size={24} />
                            )}
                          </div>
                          <div>
                            <p className="font-extrabold text-lg text-[#1C252E] leading-tight">
                              {selectedDemoMedicine === 'paracetamol' ? 'Paracetamol 650mg' : 'Amoxicillin 500mg'}
                            </p>
                            <p className="text-xs text-stone-500 font-medium">
                              {selectedDemoMedicine === 'paracetamol' ? 'Tablet · 1-0-1 · Fever & Pain' : 'Capsule · 1-1-1 · Antibiotic'}
                            </p>
                          </div>
                        </div>

                        <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 shadow-2xs">
                          {selectedDemoMedicine === 'paracetamol' ? '5 Days Course' : '7 Days Course'}
                        </span>
                      </div>

                      {/* 3-Slot Visual Schedule (Morning / Afternoon / Night) */}
                      <div className="grid grid-cols-3 gap-2.5 text-center text-xs">
                        {/* Morning Slot */}
                        <div className="bg-[#FAF9F6] p-2.5 rounded-xl border border-stone-200 shadow-2xs">
                          <div className="flex items-center justify-center gap-1 text-amber-700 font-bold mb-1">
                            <SunriseIcon size={16} />
                            <span>Morning</span>
                          </div>
                          <strong className="text-base text-[#0F5147]">1 Dose</strong>
                          <span className="block text-[10px] text-stone-400 mt-0.5">8:00 AM</span>
                        </div>

                        {/* Afternoon Slot */}
                        <div className="bg-[#FAF9F6] p-2.5 rounded-xl border border-stone-200 shadow-2xs">
                          <div className="flex items-center justify-center gap-1 text-amber-500 font-medium mb-1">
                            <MiddaySunIcon size={16} />
                            <span>Afternoon</span>
                          </div>
                          {selectedDemoMedicine === 'amoxicillin' ? (
                            <>
                              <strong className="text-base text-[#0F5147]">1 Dose</strong>
                              <span className="block text-[10px] text-stone-400 mt-0.5">1:00 PM</span>
                            </>
                          ) : (
                            <>
                              <span className="text-base text-stone-400 font-semibold">—</span>
                              <span className="block text-[10px] text-stone-400 mt-0.5">Skip</span>
                            </>
                          )}
                        </div>

                        {/* Night Slot */}
                        <div className="bg-[#FAF9F6] p-2.5 rounded-xl border border-stone-200 shadow-2xs">
                          <div className="flex items-center justify-center gap-1 text-indigo-700 font-bold mb-1">
                            <MoonIcon size={16} />
                            <span>Night</span>
                          </div>
                          <strong className="text-base text-[#0F5147]">1 Dose</strong>
                          <span className="block text-[10px] text-stone-400 mt-0.5">9:00 PM</span>
                        </div>
                      </div>

                      {/* Timing & Interactive Spoken Audio Button with Animated Soundwaves */}
                      <div className="flex items-center justify-between text-xs pt-2 border-t border-stone-100">
                        <span className="text-stone-600 font-medium flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5 text-stone-400" />
                          <span>Take after food (pc)</span>
                        </span>

                        <button
                          type="button"
                          onClick={handlePlaySampleAudio}
                          className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                            isSpeaking
                              ? 'bg-rose-100 text-rose-800 border border-rose-300 shadow-xs'
                              : 'bg-[#0F5147] text-white hover:bg-[#0A3831] shadow-sm hover:shadow'
                          }`}
                          title="Click to hear speech in active language"
                        >
                          {isSpeaking ? (
                            <>
                              {/* Animated equalizing bars */}
                              <div className="flex items-center gap-0.5 h-3">
                                <span className="w-0.5 h-full bg-rose-600 animate-pulse" />
                                <span className="w-0.5 h-2 bg-rose-600 animate-bounce" />
                                <span className="w-0.5 h-full bg-rose-600 animate-pulse" />
                              </div>
                              <span>Stop Audio</span>
                            </>
                          ) : (
                            <>
                              <Volume2 className="w-4 h-4 text-emerald-200" />
                              <span>Listen Spoken ({language.toUpperCase()})</span>
                            </>
                          )}
                        </button>
                      </div>

                      {/* Safety Guarantee Callout */}
                      <div className="p-3 bg-amber-50/90 rounded-xl border border-amber-200/90 text-xs text-amber-950 flex items-start gap-2.5">
                        <AlertTriangle className="w-4 h-4 text-[#B45309] shrink-0 mt-0.5" />
                        <span>
                          <strong>Clinical Traceability:</strong> Every extracted dose links directly to the original prescription photo so you can verify with your chemist.
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 4. TRUST & METRICS BANNER */}
        <section className="bg-white border-b border-stone-200 py-10">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
              <div className="p-4 rounded-xl bg-[#FAF9F6] border border-stone-200">
                <p className="text-3xl sm:text-4xl font-extrabold text-[#0F5147]">10,000+</p>
                <p className="text-xs sm:text-sm font-semibold text-stone-600 mt-1">Prescriptions Analyzed</p>
              </div>
              <div className="p-4 rounded-xl bg-[#FAF9F6] border border-stone-200">
                <p className="text-3xl sm:text-4xl font-extrabold text-[#0F5147]">99.2%</p>
                <p className="text-xs sm:text-sm font-semibold text-stone-600 mt-1">Field Extraction Reliability</p>
              </div>
              <div className="p-4 rounded-xl bg-[#FAF9F6] border border-stone-200">
                <p className="text-3xl sm:text-4xl font-extrabold text-[#0F5147]">4 Languages</p>
                <p className="text-xs sm:text-sm font-semibold text-stone-600 mt-1">Spoken Hindi, Guj, Mar & Eng</p>
              </div>
              <div className="p-4 rounded-xl bg-[#FAF9F6] border border-stone-200">
                <p className="text-3xl sm:text-4xl font-extrabold text-[#0F5147]">0 Guesswork</p>
                <p className="text-xs sm:text-sm font-semibold text-stone-600 mt-1">Doctor Sign-Off Protected</p>
              </div>
            </div>
          </div>
        </section>

        {/* 5. VISUAL BEFORE & AFTER COMPARISON SECTION */}
        <section id="comparison" className="py-16 sm:py-20 bg-gradient-to-b from-[#FAF9F6] to-white border-b border-stone-200">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 text-left">
            <div className="text-center max-w-3xl mx-auto space-y-3 mb-12">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0F5147] bg-[#E6F0EE] px-3 py-1 rounded-full border border-[#9DC1BB]">
                See the Difference
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C252E]">
                From Hard-to-Read Handwriting to Total Peace of Mind
              </h2>
              <p className="text-base text-stone-600">
                Compare what you get from a clinic slip with what Prescripto 2.0 generates for you.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-8 items-stretch">
              {/* BEFORE: The Raw Slip */}
              <div className="bg-white rounded-2xl border border-rose-200 p-6 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-rose-100">
                    <span className="text-xs font-bold text-rose-700 uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-rose-500" />
                      Before: Doctor's Handwritten Slip
                    </span>
                    <span className="text-xs font-semibold text-rose-600 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200">
                      Confusing
                    </span>
                  </div>

                  <div className="mt-4 rounded-xl border border-stone-300 overflow-hidden relative bg-stone-100">
                    <img
                      src="/sample_prescription.png"
                      alt="Sample handwritten prescription slip"
                      className="w-full h-44 object-cover object-top opacity-85"
                    />
                    <div className="absolute inset-0 bg-stone-900/10" />
                    <div className="absolute bottom-2 left-2 right-2 bg-white/95 backdrop-blur-xs p-2 rounded-lg border border-stone-200 text-xs text-stone-700">
                      <p className="font-semibold text-rose-900">Common Problems:</p>
                      <ul className="list-disc pl-4 text-[11px] text-stone-600 space-y-0.5 mt-0.5">
                        <li>Shorthand like "1 tab pc TID" is easily forgotten.</li>
                        <li>Unclear handwriting leads to wrong pill intake.</li>
                        <li>Elderly patients struggle to read English text.</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-rose-50 rounded-xl border border-rose-200 text-xs text-rose-900 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>High risk of missed doses or accidental double medication.</span>
                </div>
              </div>

              {/* AFTER: Prescripto Digital Routine */}
              <div className="bg-white rounded-2xl border border-emerald-300 p-6 shadow-md flex flex-col justify-between relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-100/40 rounded-full blur-2xl pointer-events-none" />

                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-emerald-100">
                    <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      After: Prescripto 2.0 Digital Guide
                    </span>
                    <span className="text-xs font-bold text-[#0F5147] bg-[#E6F0EE] px-2.5 py-0.5 rounded-full border border-[#9DC1BB]">
                      Clear & Spoken
                    </span>
                  </div>

                  <div className="mt-4 p-4 rounded-xl bg-[#FAF9F6] border border-emerald-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-9 h-9 rounded-lg bg-emerald-100 text-[#0F5147] flex items-center justify-center">
                          <TabletIcon size={20} />
                        </div>
                        <div>
                          <p className="font-bold text-sm text-[#1C252E]">Paracetamol 650mg</p>
                          <p className="text-xs text-stone-500">Take after food · 5 Days</p>
                        </div>
                      </div>
                      <span className="text-xs font-bold text-[#0F5147] bg-[#E6F0EE] px-2.5 py-0.5 rounded-md border border-[#9DC1BB]">
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
                  </div>
                </div>

                <div className="mt-4 p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-900 flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0" />
                    <span>Spoken aloud in Hindi, Gujarati, Marathi & English</span>
                  </span>
                  <Link to="/upload" className="font-bold text-[#0F5147] hover:underline shrink-0">
                    Try Now →
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 6. PROBLEM VS SOLUTION / FEATURES GRID */}
        <section id="features" className="py-16 sm:py-20 bg-white">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 text-left">
            <div className="text-center max-w-3xl mx-auto space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0F5147] bg-[#E6F0EE] px-3 py-1 rounded-full border border-[#9DC1BB]">
                Core Capabilities
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C252E]">
                Everything You Need to Take Medicines Safely
              </h2>
              <p className="text-base text-stone-600 leading-relaxed">
                Built specifically for Indian healthcare realities, multi-generational families, and busy local doctors.
              </p>
            </div>

            <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {/* Feature 1 */}
              <div className="bg-[#FAF9F6] rounded-2xl border border-stone-200 p-6 shadow-xs hover:shadow-md transition">
                <div className="w-12 h-12 rounded-xl bg-[#E6F0EE] border border-[#9DC1BB] flex items-center justify-center text-[#0F5147] font-bold mb-5">
                  <FileText className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-[#1C252E]">Clear Digital Cards</h3>
                <p className="mt-2 text-sm text-stone-600 leading-relaxed">
                  Cursive doctor handwriting is converted into bold, high-contrast cards with exact dosage and formulation (Tablet, Syrup, Drops).
                </p>
              </div>

              {/* Feature 2 */}
              <div className="bg-[#FAF9F6] rounded-2xl border border-stone-200 p-6 shadow-xs hover:shadow-md transition">
                <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700 font-bold mb-5">
                  <Clock className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-[#1C252E]">3-Slot Schedule</h3>
                <p className="mt-2 text-sm text-stone-600 leading-relaxed">
                  Never mix up whether to take 1-0-1 or 1-1-1. Dedicated slots for Morning, Afternoon, and Night with before or after food guidance.
                </p>
              </div>

              {/* Feature 3 */}
              <div className="bg-[#FAF9F6] rounded-2xl border border-stone-200 p-6 shadow-xs hover:shadow-md transition">
                <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 font-bold mb-5">
                  <Volume2 className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-[#1C252E]">Voice in Your Language</h3>
                <p className="mt-2 text-sm text-stone-600 leading-relaxed">
                  Elderly parents and low-literacy users can tap the Listen button to hear clear spoken instructions in Hindi, Gujarati, Marathi, or English.
                </p>
              </div>

              {/* Feature 4 */}
              <div className="bg-[#FAF9F6] rounded-2xl border border-stone-200 p-6 shadow-xs hover:shadow-md transition">
                <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-700 font-bold mb-5">
                  <ShieldSafetyIcon size={24} />
                </div>
                <h3 className="text-lg font-bold text-[#1C252E]">Clinical Safety Shield</h3>
                <p className="mt-2 text-sm text-stone-600 leading-relaxed">
                  Screened against CDSCO registered formulations. Flags duplicate active ingredients and dangerous interactions automatically.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 7. HOW IT WORKS SECTION */}
        <section id="how-it-works" className="scroll-mt-16 border-y border-stone-200 bg-[#FAF9F6] py-16 sm:py-20">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 text-left">
            <div className="text-center max-w-2xl mx-auto space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0F5147] bg-[#E6F0EE] px-3 py-1 rounded-full border border-[#9DC1BB]">
                Simple Process
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C252E]">
                How Prescripto Works
              </h2>
              <p className="text-base text-stone-600 leading-relaxed">
                Three easy steps designed so anyone can use it without technical training.
              </p>
            </div>

            <div className="mt-12 grid gap-8 md:grid-cols-3">
              {/* Step 1 */}
              <div className="relative bg-white rounded-2xl border border-stone-200 p-7 flex flex-col justify-between shadow-xs">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-[#0F5147] text-white flex items-center justify-center font-extrabold text-lg mb-5 shadow-xs">
                    1
                  </div>
                  <h3 className="text-xl font-bold text-[#1C252E]">Upload or Take a Photo</h3>
                  <p className="mt-3 text-sm text-stone-600 leading-relaxed">
                    Snap a photo of the paper prescription slip using your phone camera or select an existing picture from your gallery.
                  </p>
                </div>
                <div className="mt-6 pt-4 border-t border-stone-200/80 text-xs font-semibold text-[#0F5147] flex items-center gap-1.5">
                  <Check className="w-4 h-4" /> Works with handwritten & printed slips
                </div>
              </div>

              {/* Step 2 */}
              <div className="relative bg-white rounded-2xl border border-stone-200 p-7 flex flex-col justify-between shadow-xs">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-[#0F5147] text-white flex items-center justify-center font-extrabold text-lg mb-5 shadow-xs">
                    2
                  </div>
                  <h3 className="text-xl font-bold text-[#1C252E]">Intelligent Verification</h3>
                  <p className="mt-3 text-sm text-stone-600 leading-relaxed">
                    Our model detects drug lines, maps abbreviations like OD/BD/TDS, and cross-references Indian drug regulatory records.
                  </p>
                </div>
                <div className="mt-6 pt-4 border-t border-stone-200/80 text-xs font-semibold text-[#0F5147] flex items-center gap-1.5">
                  <Check className="w-4 h-4" /> Ambiguities clearly highlighted
                </div>
              </div>

              {/* Step 3 */}
              <div className="relative bg-white rounded-2xl border border-stone-200 p-7 flex flex-col justify-between shadow-xs">
                <div>
                  <div className="w-12 h-12 rounded-xl bg-[#0F5147] text-white flex items-center justify-center font-extrabold text-lg mb-5 shadow-xs">
                    3
                  </div>
                  <h3 className="text-xl font-bold text-[#1C252E]">Understand, Listen & Remind</h3>
                  <p className="mt-3 text-sm text-stone-600 leading-relaxed">
                    View your morning, afternoon, and night cards. Listen to instructions in your own language and set daily reminder alerts.
                  </p>
                </div>
                <div className="mt-6 pt-4 border-t border-stone-200/80 text-xs font-semibold text-[#0F5147] flex items-center gap-1.5">
                  <Check className="w-4 h-4" /> Share on WhatsApp with family
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 8. CLINICAL SAFETY STANDARD */}
        <section id="safety" className="py-16 sm:py-20 bg-white">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="bg-gradient-to-br from-[#0F5147] to-[#0A3831] rounded-3xl p-8 sm:p-12 text-white shadow-xl">
              <div className="grid lg:grid-cols-12 gap-8 items-center text-left">
                <div className="lg:col-span-8 space-y-4">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-300 bg-white/10 px-3 py-1 rounded-full border border-emerald-400/20">
                    Clinical Integrity Guarantee
                  </span>
                  <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight leading-tight">
                    Upstream Uncertainty Must Never Silently Become Downstream Certainty.
                  </h2>
                  <p className="text-emerald-100/90 text-sm sm:text-base leading-relaxed">
                    Most AI systems "hallucinate" confident guesses when text is blurry. In healthcare, a wrong guess is dangerous. Prescripto is engineered so that if handwriting is unclear, it remains explicitly flagged for human check.
                  </p>

                  <div className="pt-2 grid sm:grid-cols-2 gap-4 text-xs sm:text-sm text-emerald-100">
                    <div className="flex items-start gap-2.5 bg-white/10 p-3.5 rounded-xl border border-white/10">
                      <CheckCircle2 className="w-5 h-5 text-emerald-300 shrink-0 mt-0.5" />
                      <span><strong>Traceable Provenance:</strong> Tap any medicine card to see the exact highlighted ink line on the original photo.</span>
                    </div>
                    <div className="flex items-start gap-2.5 bg-white/10 p-3.5 rounded-xl border border-white/10">
                      <CheckCircle2 className="w-5 h-5 text-emerald-300 shrink-0 mt-0.5" />
                      <span><strong>Zero AI Diagnosis:</strong> We organize what the doctor wrote; we never prescribe or change medications.</span>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-4 flex flex-col items-center justify-center bg-white/10 border border-white/20 p-6 rounded-2xl text-center backdrop-blur-xs">
                  <ShieldSafetyIcon size={56} className="text-emerald-300 mb-3" />
                  <p className="font-bold text-lg text-white">DPDPA 2023 Compliant</p>
                  <p className="text-xs text-emerald-200 mt-1">
                    Your health records are stored encrypted, never shared with third parties, and deleted upon request.
                  </p>
                  <Link to="/upload" className="mt-5 w-full">
                    <Button variant="secondary" className="w-full font-bold">
                      Try with a Prescription
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 9. FOR CLINICIANS & DOCTORS CALLOUT */}
        <section id="clinicians" className="py-16 bg-[#FAF9F6] border-b border-stone-200">
          <div className="mx-auto max-w-6xl px-4 sm:px-6">
            <div className="bg-white rounded-2xl border border-stone-200 p-8 sm:p-10 flex flex-col md:flex-row items-center justify-between gap-8 text-left shadow-xs">
              <div className="max-w-2xl space-y-3">
                <div className="flex items-center gap-2 text-[#0F5147] font-bold text-xs uppercase tracking-wider">
                  <Stethoscope className="w-4 h-4" />
                  <span>For Doctors, Pharmacists & Clinics</span>
                </div>
                <h3 className="text-2xl sm:text-3xl font-extrabold text-[#1C252E]">
                  Dedicated Clinical Verification Desk
                </h3>
                <p className="text-sm sm:text-base text-stone-600 leading-relaxed">
                  Speed up outpatient intake and prevent dispensing errors. Review ambiguous scripts side-by-side with zoomable photos, edit dosages, and sign off on verified records in under 30 seconds.
                </p>
              </div>

              <div className="shrink-0 flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
                <Link to="/login?mode=doctor" className="w-full sm:w-auto">
                  <Button variant="primary" size="lg" className="w-full sm:w-auto min-h-[50px] font-bold">
                    Open Doctor Workspace
                  </Button>
                </Link>
                <Link to="/styleguide" className="w-full sm:w-auto">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto min-h-[50px]">
                    Design System
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* 10. FREQUENTLY ASKED QUESTIONS */}
        <section id="faq" className="py-16 sm:py-20 bg-white">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 text-left">
            <div className="text-center space-y-3 mb-12">
              <span className="text-xs font-bold uppercase tracking-wider text-[#0F5147] bg-[#E6F0EE] px-3 py-1 rounded-full border border-[#9DC1BB]">
                Got Questions?
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#1C252E]">
                Frequently Asked Questions
              </h2>
              <p className="text-base text-stone-600">
                Everything you need to know about Prescripto, privacy, and medication safety.
              </p>
            </div>

            <div className="space-y-3.5">
              {faqs.map((faq, index) => {
                const isOpen = openFaq === index;
                return (
                  <div
                    key={index}
                    className="bg-[#FAF9F6] rounded-xl border border-stone-200 overflow-hidden transition"
                  >
                    <button
                      type="button"
                      onClick={() => setOpenFaq(isOpen ? null : index)}
                      className="w-full px-5 py-4 text-left flex items-center justify-between gap-4 font-bold text-base text-[#1C252E] hover:bg-stone-100 transition cursor-pointer"
                      aria-expanded={isOpen}
                    >
                      <span>{faq.q}</span>
                      {isOpen ? (
                        <ChevronUp className="w-5 h-5 text-[#0F5147] shrink-0" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-stone-400 shrink-0" />
                      )}
                    </button>
                    {isOpen && (
                      <div className="px-5 pb-5 text-sm text-stone-600 leading-relaxed border-t border-stone-200/80 pt-3">
                        {faq.a}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* 11. PRE-FOOTER CTA SECTION */}
        <section className="bg-[#FAF9F6] py-16 border-t border-stone-200">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 text-center space-y-6">
            <div className="w-14 h-14 rounded-2xl bg-[#E6F0EE] border border-[#9DC1BB] text-[#0F5147] flex items-center justify-center mx-auto shadow-xs">
              <Camera className="w-7 h-7" />
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#1C252E]">
              Make Sense of Your Prescription in Seconds
            </h2>
            <p className="text-base sm:text-lg text-stone-600 max-w-xl mx-auto leading-relaxed">
              Join thousands of families across India who never worry about reading doctor handwriting again.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3.5 pt-2">
              <Link to={uploadDestination}>
                <Button size="lg" variant="primary" className="min-h-[52px] font-bold px-8 shadow-md">
                  Upload Prescription Slip
                </Button>
              </Link>
              <Link to="/login">
                <Button size="lg" variant="outline" className="min-h-[52px] font-semibold px-6 border-stone-300 bg-white">
                  Patient Sign In (OTP)
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* 12. COMPREHENSIVE TRUST FOOTER */}
      <footer className="border-t border-stone-200 bg-white py-12 text-left text-xs text-stone-600">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Col 1 */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-[#0F5147] text-white flex items-center justify-center font-bold">
                <ShieldCheck className="w-4 h-4 text-emerald-300" />
              </div>
              <span className="text-base font-bold text-[#1C252E]">Prescripto 2.0</span>
            </div>
            <p className="text-xs text-stone-500 leading-relaxed">
              Medication timing and prescription document intelligence designed for Indian families, patients, and clinical reviewers.
            </p>
            <p className="text-[11px] text-stone-400">
              © 2026 Prescripto AI. All rights reserved.
            </p>
          </div>

          {/* Col 2 */}
          <div className="space-y-2">
            <p className="font-bold text-[#1C252E] uppercase tracking-wider text-[11px]">Patient Services</p>
            <ul className="space-y-1.5 text-stone-500">
              <li><Link to="/upload" className="hover:text-[#0F5147] transition">Upload Prescription</Link></li>
              <li><Link to="/login" className="hover:text-[#0F5147] transition">Patient Mobile OTP Login</Link></li>
              <li><Link to="/help" className="hover:text-[#0F5147] transition">Medication Timing Guide</Link></li>
              <li><a href="#how-it-works" className="hover:text-[#0F5147] transition">How to Take Clear Photos</a></li>
            </ul>
          </div>

          {/* Col 3 */}
          <div className="space-y-2">
            <p className="font-bold text-[#1C252E] uppercase tracking-wider text-[11px]">Clinical & Regulatory</p>
            <ul className="space-y-1.5 text-stone-500">
              <li><Link to="/login?mode=doctor" className="hover:text-[#0F5147] transition">Doctor & Reviewer Portal</Link></li>
              <li><Link to="/styleguide" className="hover:text-[#0F5147] transition">Component Styleguide</Link></li>
              <li><span className="text-stone-400">CDSCO Master Drug Formulations</span></li>
              <li><span className="text-stone-400">DPDPA 2023 Compliant</span></li>
            </ul>
          </div>

          {/* Col 4 */}
          <div className="space-y-2">
            <p className="font-bold text-[#1C252E] uppercase tracking-wider text-[11px]">Emergency Contacts</p>
            <div className="p-3 bg-red-50 rounded-xl border border-red-200 text-red-900 space-y-1">
              <p className="font-bold">Medical Emergency: 112</p>
              <p>National Ambulance: 108</p>
              <p className="text-[10px] text-red-700">Available 24 hours across India</p>
            </div>
            <p className="text-[11px] text-stone-400 leading-normal pt-1">
              <strong>Medical Disclaimer:</strong> Prescripto is an organizational aid. Never alter medications without consulting your prescribing physician or pharmacist.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
