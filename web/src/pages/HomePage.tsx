import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  ShieldCheck,
  HeartPulse,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Users,
  Eye,
  Activity,
  Database,
  ChevronRight,
  Stethoscope,
  Smartphone,
  ShieldAlert,
  Edit3,
  Cpu,
  Clock,
  Sparkles,
} from 'lucide-react';

interface SimulatorScenario {
  id: string;
  title: string;
  category: string;
  tag: string;
  doctorName: string;
  clinic: string;
  date: string;
  patientName: string;
  patientId: string;
  allergies: string;
  handwrittenLines: string[];
  recognizedDrugs: {
    name: string;
    generic: string;
    dosage: string;
    freq: string;
    confidence: number;
    cdscoResolved: boolean;
  }[];
  safetyAlerts: {
    type: 'CRITICAL_ALLERGY' | 'DOSAGE_EXCEEDED' | 'DUPLICATE_THERAPY' | 'CLEAR';
    title: string;
    description: string;
  }[];
  patientSummary: string;
}

const SCENARIOS: SimulatorScenario[] = [
  {
    id: 'allergy-alert',
    title: 'Penicillin Allergy Cross-Check',
    category: 'Patient Safety Sentinel',
    tag: 'Critical Conflict',
    doctorName: 'Dr. Vikram Malhotra, MD (Internal Med)',
    clinic: 'Apex Multispecialty Hospital, Mumbai',
    date: '21 Oct 2026',
    patientName: 'Rahul Verma (Male, 34)',
    patientId: 'PAT-1001',
    allergies: 'Penicillin, Sulfa Compounds',
    handwrittenLines: [
      'Rx: Amoxicillin 500mg',
      'Dose: 1 capsule TDS x 5 days',
      'Sig: Take after food with warm water',
    ],
    recognizedDrugs: [
      {
        name: 'Amoxicillin 500mg',
        generic: 'Amoxicillin Trihydrate',
        dosage: '500mg TDS',
        freq: '3 times daily',
        confidence: 98.6,
        cdscoResolved: true,
      },
    ],
    safetyAlerts: [
      {
        type: 'CRITICAL_ALLERGY',
        title: 'Severe Patient Allergy Contraindication',
        description:
          'Patient profile records documented hypersensitivity to Penicillins. Amoxicillin shares the beta-lactam core and carries high risk of acute anaphylaxis. Physician review required before dispensing.',
      },
    ],
    patientSummary:
      'Caution: This prescribed antibiotic belongs to the Penicillin family. Your medical profile flags a known allergy. Please confirm with Dr. Malhotra immediately for an alternative non-penicillin antibiotic (such as Azithromycin).',
  },
  {
    id: 'duplicate-overdose',
    title: 'Duplicate Paracetamol & Toxicity Shield',
    category: 'Dosage Sentinel',
    tag: 'Duplicate Therapy',
    doctorName: 'Dr. Radhika Sen, MBBS, DNB',
    clinic: 'CareWell Clinic & Diagnostic Centre',
    date: '21 Oct 2026',
    patientName: 'Priya Patel (Female, 28)',
    patientId: 'PAT-1002',
    allergies: 'None Reported',
    handwrittenLines: [
      '1. Dolo 650mg TDS x 3 days',
      '2. Combiflam (Ibuprofen+PCM) BD',
      '3. Pantoprazole 40mg OD (ante-cibum)',
    ],
    recognizedDrugs: [
      {
        name: 'Dolo 650',
        generic: 'Paracetamol',
        dosage: '650mg TDS (1950mg/day)',
        freq: '3 times daily',
        confidence: 99.1,
        cdscoResolved: true,
      },
      {
        name: 'Combiflam',
        generic: 'Ibuprofen (400mg) + Paracetamol (325mg)',
        dosage: 'BD (650mg PCM/day)',
        freq: '2 times daily',
        confidence: 97.4,
        cdscoResolved: true,
      },
      {
        name: 'Pantoprazole 40',
        generic: 'Pantoprazole Sodium',
        dosage: '40mg OD',
        freq: 'Once daily before breakfast',
        confidence: 98.9,
        cdscoResolved: true,
      },
    ],
    safetyAlerts: [
      {
        type: 'DUPLICATE_THERAPY',
        title: 'Duplicate Active Paracetamol Therapy',
        description:
          'Concurrent administration of Dolo 650 and Combiflam results in cumulative daily Paracetamol intake of 2,600mg. Exceeds safe threshold when combined. Hepatotoxicity risk flagged for review.',
      },
    ],
    patientSummary:
      'Take Pantoprazole 40 30 minutes before your morning meal. Note: Both Dolo and Combiflam contain Paracetamol; do not take extra paracetamol tablets to prevent liver strain.',
  },
  {
    id: 'cardiac-safe',
    title: 'Hypertension Master Normalization',
    category: 'Chronic Care Regimen',
    tag: 'Verified Clean',
    doctorName: 'Dr. Ananya Sharma, MD, DM (Cardiology)',
    clinic: 'National Heart & Vascular Institute',
    date: '21 Oct 2026',
    patientName: 'Amitabh Sen (Male, 58)',
    patientId: 'PAT-1003',
    allergies: 'NSAIDs (Mild Gastric Reflux)',
    handwrittenLines: [
      'Rx: Amlodipine 10mg OD morning',
      'Rx: Atenolol 50mg OD evening',
      'Check BP twice weekly & record',
    ],
    recognizedDrugs: [
      {
        name: 'Amlodipine 10',
        generic: 'Amlodipine Besylate',
        dosage: '10mg OD',
        freq: 'Once daily (morning)',
        confidence: 99.4,
        cdscoResolved: true,
      },
      {
        name: 'Atenolol 50',
        generic: 'Atenolol',
        dosage: '50mg OD',
        freq: 'Once daily (evening)',
        confidence: 98.8,
        cdscoResolved: true,
      },
    ],
    safetyAlerts: [
      {
        type: 'CLEAR',
        title: 'Safety Screen Passed: Zero Contraindications',
        description:
          'Dual antihypertensive regimen (Calcium Channel Blocker + Beta Blocker) verified against CDSCO Formulation Master. Normal daily dosages within standard therapeutic windows.',
      },
    ],
    patientSummary:
      'Take Amlodipine 10mg every morning after breakfast and Atenolol 50mg every evening. Continue checking your blood pressure twice a week. No adverse interactions detected with your current profile.',
  },
];

export const HomePage: React.FC = () => {
  const { session, isAuthenticated } = useAuth();

  const [activeScenario, setActiveScenario] = useState<SimulatorScenario>(SCENARIOS[0]);
  const [activeView, setActiveView] = useState<'scan' | 'structured' | 'safety'>('scan');

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Modern Clean Floating Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-xs">
              <ShieldCheck className="w-5 h-5 font-bold" />
            </div>
            <div>
              <div className="text-base font-bold tracking-tight text-slate-900 flex items-center gap-1">
                Prescripto <span className="text-teal-600 font-bold">2.0</span>
              </div>
              <div className="text-[10px] tracking-wider text-slate-500 font-semibold uppercase">
                Clinical Prescription Safety
              </div>
            </div>
          </Link>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-slate-600">
            <a href="#simulator" className="hover:text-teal-700 transition">
              Interactive Demo
            </a>
            <a href="#features" className="hover:text-teal-700 transition">
              Key Features
            </a>
            <a href="#architecture" className="hover:text-teal-700 transition">
              8-Stage Verification
            </a>
            <a href="#portals" className="hover:text-teal-700 transition">
              Doctor & Patient Portals
            </a>
            <Link to="/health" className="hover:text-teal-700 transition flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-emerald-600" />
              Diagnostics
            </Link>
          </nav>

          {/* Header Action Button */}
          <div className="flex items-center gap-2">
            {isAuthenticated && session ? (
              <Link
                to="/prescriptions"
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Open Workspace ({session.patient_name || session.username})</span>
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-3.5 py-2 rounded-lg text-xs font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-100 transition"
                >
                  Sign In
                </Link>
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1 px-3.5 py-2 rounded-lg text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition"
                >
                  <span>Launch Portal</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main>
        {/* HERO SECTION */}
        <section className="pt-16 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center space-y-6">
          {/* Clean Human Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-medium">
            <HeartPulse className="w-3.5 h-3.5 text-teal-600" />
            <span>Assistive Clinical Intelligence for Handwritten Prescriptions</span>
          </div>

          {/* Main Title */}
          <div className="max-w-3xl mx-auto space-y-4">
            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 leading-tight">
              Prescription reading made clear, accurate, and safe.
            </h1>
            <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
              Prescripto helps doctors, pharmacists, and patients turn handwritten prescriptions into verified medications, instantly catching allergy risks and dosage conflicts before medicines are dispensed.
            </p>
          </div>

          {/* CTA Group */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition"
            >
              <FileText className="w-4 h-4" />
              <span>Upload Prescription Scan</span>
            </Link>

            <a
              href="#simulator"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white hover:bg-slate-100 text-slate-800 text-xs font-semibold border border-slate-300 shadow-2xs transition"
            >
              <Eye className="w-4 h-4 text-slate-600" />
              <span>Try Live Interactive Demo</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </a>

            <Link
              to="/patients"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white hover:bg-slate-100 text-slate-800 text-xs font-semibold border border-slate-300 shadow-2xs transition"
            >
              <Users className="w-4 h-4 text-slate-600" />
              <span>Patient Directory</span>
            </Link>
          </div>

          {/* Quick Trust Highlights Strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto pt-6 text-left">
            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
              <div className="text-2xl font-bold text-slate-900">&lt; 500ms</div>
              <div className="text-xs text-slate-500 font-medium mt-1">
                Fast handwriting recognition
              </div>
            </div>

            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
              <div className="text-2xl font-bold text-teal-700">115+</div>
              <div className="text-xs text-slate-500 font-medium mt-1">
                Verified CDSCO generic drugs
              </div>
            </div>

            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
              <div className="text-2xl font-bold text-emerald-700">DPDPA 2023</div>
              <div className="text-xs text-slate-500 font-medium mt-1">
                India patient privacy compliant
              </div>
            </div>

            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs">
              <div className="text-2xl font-bold text-blue-700">100%</div>
              <div className="text-xs text-slate-500 font-medium mt-1">
                Doctor-in-the-loop review
              </div>
            </div>
          </div>
        </section>

        {/* INTERACTIVE SCANNER & SAFETY SIMULATOR */}
        <section id="simulator" className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-6">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-[11px] font-semibold uppercase tracking-wider">
              Interactive Demonstration
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
              See How It Reads & Verifies Prescriptions
            </h2>
            <p className="text-xs sm:text-sm text-slate-600">
              Select a clinical scenario below to see how optical recognition extracts drugs, validates against Indian CDSCO catalogs, and flags patient safety conflicts.
            </p>
          </div>

          {/* Scenario Selector Tabs */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            {SCENARIOS.map((sc) => {
              const isSelected = sc.id === activeScenario.id;
              return (
                <button
                  key={sc.id}
                  onClick={() => setActiveScenario(sc)}
                  className={`px-3.5 py-2 rounded-lg text-xs font-medium transition flex items-center gap-2 border ${
                    isSelected
                      ? 'bg-teal-50 border-teal-300 text-teal-900 font-semibold shadow-2xs'
                      : 'bg-white border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full ${
                      sc.tag.includes('Critical')
                        ? 'bg-rose-500'
                        : sc.tag.includes('Duplicate')
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                    }`}
                  />
                  <span>{sc.title}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                    {sc.tag}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Clean Interactive Workbench Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs">
            {/* Header inside simulator */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-teal-700">
                    Scenario: {activeScenario.category}
                  </span>
                  <span className="text-slate-300">&bull;</span>
                  <span className="text-xs text-slate-500 font-mono">Patient: {activeScenario.patientId}</span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  {activeScenario.title}
                </h3>
              </div>

              {/* View Switcher Tabs */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200">
                <button
                  onClick={() => setActiveView('scan')}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center gap-1.5 ${
                    activeView === 'scan'
                      ? 'bg-white text-slate-900 font-semibold shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Eye className="w-3.5 h-3.5 text-teal-600" />
                  <span>Recognized Medications</span>
                </button>

                <button
                  onClick={() => setActiveView('structured')}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center gap-1.5 ${
                    activeView === 'structured'
                      ? 'bg-white text-slate-900 font-semibold shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Database className="w-3.5 h-3.5 text-blue-600" />
                  <span>CDSCO Formulation Data</span>
                </button>

                <button
                  onClick={() => setActiveView('safety')}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition flex items-center gap-1.5 ${
                    activeView === 'safety'
                      ? 'bg-white text-slate-900 font-semibold shadow-2xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                  <span>Safety Alerts ({activeScenario.safetyAlerts.length})</span>
                </button>
              </div>
            </div>

            {/* Grid content */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 pt-6">
              {/* Left: Realistic Prescription Note (5 Cols) */}
              <div className="lg:col-span-5">
                <div className="bg-slate-50 rounded-xl p-6 border border-slate-200 font-sans min-h-[380px] flex flex-col justify-between shadow-2xs">
                  {/* Prescription Header */}
                  <div className="border-b-2 border-slate-800 pb-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-bold text-sm text-slate-900">{activeScenario.doctorName}</div>
                        <div className="text-[11px] text-slate-500">{activeScenario.clinic}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-[10px] text-slate-500">{activeScenario.date}</div>
                        <div className="text-[10px] font-semibold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200">Rx Validated</div>
                      </div>
                    </div>

                    <div className="mt-2 pt-2 border-t border-slate-200 flex items-center justify-between text-xs text-slate-700 font-medium">
                      <span>Patient: {activeScenario.patientName}</span>
                      <span className="font-mono text-slate-500">{activeScenario.patientId}</span>
                    </div>

                    {activeScenario.allergies !== 'None Reported' && (
                      <div className="mt-2 text-xs text-rose-800 font-medium bg-rose-50 px-2.5 py-1 rounded border border-rose-200 flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                        <span>Documented Allergies: {activeScenario.allergies}</span>
                      </div>
                    )}
                  </div>

                  {/* Prescription Body (Handwriting Lines) */}
                  <div className="py-4 space-y-3 font-serif text-slate-800 text-sm italic">
                    {activeScenario.handwrittenLines.map((line, idx) => (
                      <div key={idx} className="bg-white p-2.5 rounded-lg border border-slate-200/80">
                        <div className="text-base font-medium tracking-wide text-slate-900">
                          {line}
                        </div>
                        <div className="text-[10px] font-mono text-slate-400 not-italic mt-0.5">
                          Line {idx + 1} &bull; OCR Confidence: {98.2 - idx * 0.4}%
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Prescription Footer */}
                  <div className="border-t border-slate-200 pt-3 flex items-center justify-between text-xs text-slate-500">
                    <div>Prescription Intact</div>
                    <div className="font-serif italic font-bold text-slate-700">Signed: V.M., MD</div>
                  </div>
                </div>
              </div>

              {/* Right: Structured Output & Safety Findings (7 Cols) */}
              <div className="lg:col-span-7 space-y-5">
                {/* Status Bar */}
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                  <span className="text-slate-600 font-medium flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Optical Perception & Safety Pipeline
                  </span>
                  <span className="text-slate-700 font-semibold">
                    Completed in 420ms
                  </span>
                </div>

                {/* Active View: Recognized Medications */}
                {activeView === 'scan' && (
                  <div className="space-y-3">
                    <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Recognized Medications ({activeScenario.recognizedDrugs.length})
                    </div>
                    {activeScenario.recognizedDrugs.map((drug, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-white border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs hover:border-teal-300 transition"
                      >
                        <div className="space-y-1">
                          <div className="text-sm font-bold text-slate-900 flex items-center gap-2">
                            <span>{drug.name}</span>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono border border-slate-200">
                              {drug.confidence}% Conf
                            </span>
                          </div>
                          <div className="text-xs text-slate-600">
                            Generic: <span className="text-slate-900 font-medium">{drug.generic}</span>
                          </div>
                          <div className="text-xs text-slate-500">
                            Dosage: <span className="text-slate-700">{drug.dosage}</span> &bull; {drug.freq}
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            CDSCO Verified
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Active View: CDSCO Master Resolution */}
                {activeView === 'structured' && (
                  <div className="space-y-3">
                    <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Master Drug Formulation Mapping
                    </div>
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5 text-xs">
                      <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                        <span className="font-medium text-slate-600">Drug Catalog:</span>
                        <span className="font-mono text-teal-800 font-semibold">CDSCO 2024.1 National Master</span>
                      </div>
                      <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                        <span className="font-medium text-slate-600">Matching Mode:</span>
                        <span className="text-slate-800">Exact Brand Match + Typo Tolerance</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-slate-600">Verification Gate:</span>
                        <span className="text-emerald-700 font-semibold">Zero-Hallucination Human Approval</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Active View: Safety Findings */}
                {activeView === 'safety' && (
                  <div className="space-y-3">
                    <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Safety Screen Results
                    </div>
                    {activeScenario.safetyAlerts.map((alert, idx) => {
                      const isCrit = alert.type === 'CRITICAL_ALLERGY';
                      const isWarn = alert.type === 'DUPLICATE_THERAPY';
                      return (
                        <div
                          key={idx}
                          className={`p-4 rounded-xl border space-y-1.5 ${
                            isCrit
                              ? 'bg-rose-50 border-rose-200 text-rose-900'
                              : isWarn
                              ? 'bg-amber-50 border-amber-200 text-amber-900'
                              : 'bg-emerald-50 border-emerald-200 text-emerald-900'
                          }`}
                        >
                          <div className="flex items-center gap-2 font-bold text-sm">
                            {isCrit ? (
                              <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
                            ) : isWarn ? (
                              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                            ) : (
                              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                            )}
                            <span>{alert.title}</span>
                          </div>
                          <p className="text-xs leading-relaxed opacity-90">{alert.description}</p>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Patient Friendly Explanation Box */}
                <div className="p-4 rounded-xl bg-teal-50/70 border border-teal-200 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-teal-900">
                    <Sparkles className="w-3.5 h-3.5 text-teal-700" />
                    <span>Clear Patient Guidance</span>
                  </div>
                  <p className="text-xs text-teal-950 leading-relaxed">
                    &ldquo;{activeScenario.patientSummary}&rdquo;
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CORE FEATURES (6 CLEAN CARDS) */}
        <section id="features" className="py-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-10">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
              Designed for Everyday Clinical Practice
            </h2>
            <p className="text-xs sm:text-sm text-slate-600">
              Prescripto 2.0 provides an intuitive and reliable digital companion for doctors, pharmacies, and patients.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-2xs hover:border-slate-300 transition">
              <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-100">
                <Cpu className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Handwriting Digitization</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Lightweight, fast optical perception reads doctor handwriting, dosage frequencies, and meal instructions without requiring expensive server hardware.
              </p>
            </div>

            {/* Card 2 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-2xs hover:border-slate-300 transition">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center border border-blue-100">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">CDSCO Medication Catalog</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Matches trade brand names against authorized Indian pharmaceutical formulations, standardizing generics, strengths, and standard routes.
              </p>
            </div>

            {/* Card 3 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-2xs hover:border-slate-300 transition">
              <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-700 flex items-center justify-center border border-rose-100">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Allergy & Conflict Checks</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Automatically checks prescribed drugs against known patient allergies (like Penicillins or Sulfa) and duplicate daily dosage limits.
              </p>
            </div>

            {/* Card 4 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-2xs hover:border-slate-300 transition">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center border border-indigo-100">
                <Users className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Patient Medical Timeline</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Doctors can look up a patient's historical prescriptions, active medications, and safety findings chronologically in one secure ledger.
              </p>
            </div>

            {/* Card 5 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-2xs hover:border-slate-300 transition">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
                <Edit3 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Doctor In-Line Review</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Clinicians can review unclear medication lines, make quick adjustments directly on the report, and approve records before dispensing.
              </p>
            </div>

            {/* Card 6 */}
            <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-2xs hover:border-slate-300 transition">
              <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
                <Smartphone className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Easy Patient Access</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Patients log in simply with their mobile phone and OTP to read clear dosing schedules, meal instructions, and medication advisories.
              </p>
            </div>
          </div>
        </section>

        {/* 8-STAGE VERIFICATION TRANSPARENCY SECTION */}
        <section id="architecture" className="py-14 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
              The 8 Verification Stages
            </h2>
            <p className="text-xs sm:text-sm text-slate-600">
              Every document follows a clear, step-by-step verification pipeline with complete audit trails.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { num: '01', title: 'File Ingestion', desc: 'Integrity hash check and format validation' },
              { num: '02', title: 'Quality Check', desc: 'Laplacian variance check for image clarity' },
              { num: '03', title: 'Line Detection', desc: 'Identifies text lines and bounding boxes' },
              { num: '04', title: 'Handwriting OCR', desc: 'Lightweight optical recognition' },
              { num: '05', title: 'Clinical Extraction', desc: 'Parses drug name, dose, frequency, and route' },
              { num: '06', title: 'CDSCO Normalization', desc: 'Maps trade names to standard generic catalog' },
              { num: '07', title: 'Safety Screening', desc: 'Cross-checks patient allergies and duplicate doses' },
              { num: '08', title: 'Report Assembly', desc: 'Compiles clean report and queues doctor sign-off' },
            ].map((st) => (
              <div
                key={st.num}
                className="p-4 rounded-xl bg-white border border-slate-200 space-y-1.5 shadow-2xs"
              >
                <div className="text-xs font-mono font-bold text-teal-700">{st.num}</div>
                <div className="text-sm font-bold text-slate-900">{st.title}</div>
                <div className="text-xs text-slate-500 leading-relaxed">{st.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* DUAL PORTAL GATEWAY SECTION */}
        <section id="portals" className="py-14 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Doctor Portal Card */}
            <div className="p-8 rounded-2xl bg-white border border-slate-200 space-y-5 shadow-xs">
              <div className="w-11 h-11 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center border border-indigo-100">
                <Stethoscope className="w-6 h-6" />
              </div>

              <div className="space-y-1.5">
                <h3 className="text-xl font-bold text-slate-900">For Doctors & Pharmacists</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Log in with clinical credentials to search patient histories, review flagged prescriptions, edit transcribed values, and approve orders for dispensing.
                </p>
              </div>

              <div className="space-y-2 text-xs text-slate-700">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Look up patient timeline by name or mobile</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Review queue for prescriptions needing clinician sign-off</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>In-line editing with immediate safety re-screening</span>
                </div>
              </div>

              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition shadow-2xs"
              >
                <span>Doctor & Staff Login</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Patient Portal Card */}
            <div className="p-8 rounded-2xl bg-white border border-slate-200 space-y-5 shadow-xs">
              <div className="w-11 h-11 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-100">
                <Smartphone className="w-6 h-6" />
              </div>

              <div className="space-y-1.5">
                <h3 className="text-xl font-bold text-slate-900">For Patients</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Log in with your mobile number and an OTP to see your prescriptions, plain-language dosing directions, and verified medication reminders.
                </p>
              </div>

              <div className="space-y-2 text-xs text-slate-700">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-600" />
                  <span>Simple mobile OTP login (test OTP: 123456)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-600" />
                  <span>Clear instructions on meal times and dosages</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-600" />
                  <span>Protected and confidential under India DPDPA 2023</span>
                </div>
              </div>

              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white transition shadow-2xs"
              >
                <span>Patient Mobile OTP Login</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </section>

        {/* CALL TO ACTION BANNER */}
        <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <div className="rounded-2xl p-8 sm:p-10 bg-teal-50 border border-teal-200 text-center space-y-4">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">
              Ready to verify a prescription?
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 max-w-xl mx-auto leading-relaxed">
              Upload a prescription photo to test optical recognition, review structured medications, and check patient allergy safety.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <Link
                to="/upload"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition"
              >
                <span>Upload a Prescription</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/health"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-white hover:bg-slate-100 text-slate-800 text-xs font-medium border border-slate-300 transition"
              >
                <Activity className="w-4 h-4 text-emerald-600" />
                <span>System Diagnostics</span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Clean Footer */}
      <footer className="border-t border-slate-200 bg-white py-10 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-teal-600 text-white flex items-center justify-center">
              <HeartPulse className="w-4 h-4" />
            </div>
            <div>
              <div className="font-semibold text-slate-800">Prescripto 2.0</div>
              <div className="text-[11px] text-slate-500">Clinical Prescription Intelligence & Safety Platform</div>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-5 text-xs text-slate-600">
            <Link to="/prescriptions" className="hover:text-teal-700 transition">
              Prescriptions
            </Link>
            <Link to="/patients" className="hover:text-teal-700 transition">
              Patient Directory
            </Link>
            <Link to="/review-queue" className="hover:text-teal-700 transition">
              Review Queue
            </Link>
            <Link to="/health" className="hover:text-teal-700 transition">
              Diagnostics
            </Link>
            <span className="text-slate-300">&bull;</span>
            <span className="text-slate-500">India DPDPA 2023 &bull; CDSCO 2024.1</span>
          </div>

          <div className="text-xs text-slate-500 text-center md:text-right">
            Clinical Decision Support System
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
