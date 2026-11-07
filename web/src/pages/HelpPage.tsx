import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  HelpCircle,
  Stethoscope,
  ChevronDown,
  ChevronUp,
  Volume2,
  Square,
  ShieldCheck,
  PhoneCall,
  Camera,
  Clock,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/Button';

export const HelpPage: React.FC = () => {
  const { t, language, speak, stopSpeaking, isSpeaking } = useLanguage();
  const [openFaq, setOpenFaq] = useState<number | null>(0); // First open by default
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null);

  const faqs = [
    {
      id: 1,
      q: t('help.faq1_q', 'How do I take a good photo of my prescription?'),
      a: t(
        'help.faq1_a',
        'Keep the paper flat on a table in good light. Avoid dark shadows or camera flash glare, and make sure the whole slip is inside the picture.'
      ),
      icon: Camera,
    },
    {
      id: 2,
      q: t('help.faq2_q', 'How do I know when to take my medicines?'),
      a: t(
        'help.faq2_a',
        'Look at the three boxes on each medicine card: Morning, Afternoon, and Night. You can also tap the Listen button to hear the timings spoken aloud in your language.'
      ),
      icon: Clock,
    },
    {
      id: 3,
      q: t('help.faq3_q', 'What if the app is unsure about a word?'),
      a: t(
        'help.faq3_a',
        'If handwriting is unclear, the card gets a calm amber border and says "Please check this". You can tap "Show on photo" to see the original handwriting, or tap "Edit" to correct it.'
      ),
      icon: AlertTriangle,
    },
    {
      id: 4,
      q: t('help.faq4_q', 'Can I take medicine based on this app alone?'),
      a: t(
        'help.faq4_a',
        'No. Always check your medicines with your doctor or chemist before taking them. Prescripto is a reading aid, not medical advice.'
      ),
      icon: ShieldCheck,
    },
  ];

  const handleSpeakFaq = (index: number, text: string) => {
    if (isSpeaking && speakingIndex === index) {
      stopSpeaking();
      setSpeakingIndex(null);
      return;
    }
    setSpeakingIndex(index);
    speak(text);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-16 text-left animate-in fade-in duration-150">
      {/* Header */}
      <div className="space-y-1.5">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-brand-soft text-brand border border-brand/20">
          <HelpCircle className="w-3.5 h-3.5 text-brand" aria-hidden="true" />
          <span>Prescripto help</span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold text-ink tracking-tight">
          {t('help.page_title', 'Help & frequently asked questions')}
        </h1>

        <p className="text-sm text-ink-muted leading-relaxed">
          {t('help.page_subtitle', 'Simple answers to help you use Prescripto and understand your medicines.')}
        </p>
      </div>

      {/* Emergency Helpline Banner */}
      <div className="p-4 sm:p-5 rounded-2xl bg-red-50 border border-red-200 text-red-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white text-red-600 flex items-center justify-center shrink-0 border border-red-200 shadow-2xs">
            <PhoneCall className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-sm sm:text-base font-bold text-red-900">
              Medical emergency? Call directly
            </h2>
            <p className="text-xs text-red-800">Free 24/7 national emergency services across India</p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <a
            href="tel:112"
            className="px-3.5 py-2 rounded-xl bg-white text-red-700 font-bold text-xs border border-red-200 hover:bg-red-100 transition shadow-2xs min-h-[40px] flex items-center"
          >
            Call 112 (National)
          </a>
          <a
            href="tel:108"
            className="px-3.5 py-2 rounded-xl bg-red-600 text-white font-bold text-xs hover:bg-red-700 transition shadow-2xs min-h-[40px] flex items-center"
          >
            Call 108 (Ambulance)
          </a>
        </div>
      </div>

      {/* DOCTOR / CHEMIST ADVISORY CARD */}
      <div className="bg-amber-50/60 border border-amber-200 rounded-2xl p-5 sm:p-6 shadow-2xs space-y-2">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white text-amber-800 flex items-center justify-center shrink-0 border border-amber-300 shadow-2xs">
            <Stethoscope className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-base font-bold text-amber-900">
              {t('help.doctor_advisory_title', 'Talk to a doctor or chemist')}
            </h2>
            <span className="text-xs text-amber-800 font-medium">Important health advisory</span>
          </div>
        </div>

        <p className="text-xs sm:text-sm text-ink-muted leading-relaxed">
          {t(
            'help.doctor_advisory_desc',
            'Prescripto is a reading aid to organize your prescription slip. If you feel unwell, have doubts about your dosage, or experience side effects, always talk to your qualified doctor or local chemist before taking any medicine.'
          )}
        </p>
      </div>

      {/* SHORT FAQ ACCORDION */}
      <div className="space-y-3 pt-2">
        <h2 className="text-xs font-semibold text-ink-muted mb-2">
          Frequently asked questions
        </h2>

        {faqs.map((faq, index) => {
          const isOpen = openFaq === index;
          const Icon = faq.icon;
          const isSpeakingThis = isSpeaking && speakingIndex === index;

          return (
            <div
              key={faq.id}
              className={`rounded-2xl border transition bg-white ${
                isOpen ? 'border-brand shadow-2xs ring-1 ring-brand/10' : 'border-stone-200 hover:border-stone-300'
              }`}
            >
              <button
                type="button"
                onClick={() => setOpenFaq(isOpen ? null : index)}
                className="w-full p-4 sm:p-5 flex items-center justify-between gap-3 text-left cursor-pointer min-h-[56px]"
                aria-expanded={isOpen}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition ${
                      isOpen ? 'bg-brand text-white' : 'bg-paper text-ink border border-stone-200'
                    }`}
                  >
                    <Icon className="w-5 h-5" aria-hidden="true" />
                  </div>
                  <span className="text-sm sm:text-base font-bold text-ink leading-tight">
                    {faq.q}
                  </span>
                </div>

                <div className="shrink-0 text-stone-400">
                  {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </div>
              </button>

              {isOpen && (
                <div className="px-4 pb-5 pt-1 sm:px-5 border-t border-stone-100 text-xs sm:text-sm text-ink leading-relaxed space-y-3">
                  <p className="text-ink-muted leading-relaxed">{faq.a}</p>

                  <div className="pt-2 flex items-center gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleSpeakFaq(index, `${faq.q}. ${faq.a}`)}
                      leftIcon={
                        isSpeakingThis ? (
                          <Square className="w-3.5 h-3.5 text-red-600 animate-pulse" />
                        ) : (
                          <Volume2 className="w-3.5 h-3.5 text-brand" />
                        )
                      }
                      className="text-xs min-h-[40px]"
                    >
                      <span>{isSpeakingThis ? t('hero.stop_voice', 'Stop') : t('hero.listen', 'Listen')}</span>
                    </Button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Quick Action to Upload or View Prescriptions */}
      <div className="bg-white border border-stone-200 rounded-2xl p-6 text-center space-y-4 shadow-2xs">
        <h3 className="text-base font-bold text-ink">
          Ready to upload your prescription?
        </h3>
        <p className="text-xs sm:text-sm text-ink-muted max-w-md mx-auto leading-relaxed">
          We will organize medicine names and morning, afternoon, and night timings into clear cards you can listen to.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link to="/upload">
            <Button variant="primary" size="lg" className="min-h-[48px]" rightIcon={<ArrowRight className="w-5 h-5" />}>
              {t('nav.new_intake', 'Upload prescription')}
            </Button>
          </Link>
          <Link to="/patient-portal">
            <Button variant="outline" size="lg" className="min-h-[48px]">
              {t('nav.my_prescriptions', 'My prescriptions')}
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HelpPage;
