import React, { useState } from 'react';
import { useLanguage, Language } from '../context/LanguageContext';
import { Globe, Volume2, VolumeX, HelpCircle, X, Sparkles } from 'lucide-react';

export const LanguageSwitcher: React.FC = () => {
  const { language, setLanguage, isSpeaking, stopSpeaking, t } = useLanguage();
  const [showGlossary, setShowGlossary] = useState<boolean>(false);

  const languages: { code: Language; label: string; nativeName: string }[] = [
    { code: 'en', label: 'English', nativeName: 'English' },
    { code: 'hi', label: 'Hindi', nativeName: 'हिन्दी' },
    { code: 'gu', label: 'Gujarati', nativeName: 'ગુજરાતી' },
    { code: 'mr', label: 'Marathi', nativeName: 'मराठी' },
  ];

  return (
    <div className="flex items-center gap-2">
      {/* Speech active indicator if currently speaking */}
      {isSpeaking && (
        <button
          onClick={stopSpeaking}
          title={t('common.stop_audio', 'Stop Voice')}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 rounded-full animate-pulse hover:bg-rose-100 transition-colors cursor-pointer"
        >
          <VolumeX className="w-3.5 h-3.5" />
          <span>{t('common.stop_audio', 'Stop Voice')}</span>
        </button>
      )}

      {/* Language Selector Dropdown */}
      <div className="relative inline-flex items-center">
        <div className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium text-slate-700 bg-slate-50 border border-slate-200 rounded-lg hover:border-slate-300 transition-colors">
          <Globe className="w-3.5 h-3.5 text-indigo-600" />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            aria-label="Select Language"
            className="bg-transparent font-medium text-slate-800 text-xs focus:outline-hidden cursor-pointer pr-1"
          >
            {languages.map((l) => (
              <option key={l.code} value={l.code} className="text-slate-900 bg-white">
                {l.nativeName} ({l.label})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Plain Language / Medical Terms Help Button */}
      <button
        onClick={() => setShowGlossary(true)}
        title="Plain Language & Medicine Timing Guide"
        className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-slate-600 bg-slate-50 border border-slate-200 rounded-lg hover:text-indigo-600 hover:border-indigo-200 transition-colors cursor-pointer"
      >
        <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
        <span className="hidden sm:inline">सरल भाषा / Guide</span>
      </button>

      {/* Plain Language Glossary Modal */}
      {showGlossary && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200 relative">
            <button
              onClick={() => setShowGlossary(false)}
              className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 bg-indigo-50 text-indigo-700 rounded-xl">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-900">
                  {language === 'hi'
                    ? 'डॉक्टर के पर्चे की सरल भाषा'
                    : language === 'gu'
                    ? 'પ્રિસ્ક્રિપ્શનની સરળ સમજૂતી'
                    : language === 'mr'
                    ? 'डॉक्टरांच्या चिठ्ठीची सोपी भाषा'
                    : 'Simple Prescription Guide'}
                </h3>
                <p className="text-xs text-slate-500">
                  {language === 'hi'
                    ? 'दवाइयों पर लिखे संक्षिप्त शब्दों का आसान मतलब'
                    : language === 'gu'
                    ? 'દવાઓ પર લખેલા ટૂંકા શબ્દોનો સરળ અર્થ'
                    : 'Easy meaning of common prescription abbreviations'}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="font-bold text-indigo-700 flex items-center gap-1.5">
                  <span>OD</span>
                  <span className="text-slate-400 font-normal">| ☀️</span>
                </div>
                <div className="text-slate-700 mt-0.5">{t('sig.od', 'Once a day')}</div>
                <div className="text-[11px] text-slate-500">दिन में 1 बार (सुबह)</div>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="font-bold text-indigo-700 flex items-center gap-1.5">
                  <span>BD / BID</span>
                  <span className="text-slate-400 font-normal">| ☀️ 🌙</span>
                </div>
                <div className="text-slate-700 mt-0.5">{t('sig.bd', 'Twice a day (Morning & Night)')}</div>
                <div className="text-[11px] text-slate-500">दिन में 2 बार (सुबह और शाम)</div>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="font-bold text-indigo-700 flex items-center gap-1.5">
                  <span>TDS / TID</span>
                  <span className="text-slate-400 font-normal">| ☀️ 🌤️ 🌙</span>
                </div>
                <div className="text-slate-700 mt-0.5">{t('sig.tds', 'Three times a day')}</div>
                <div className="text-[11px] text-slate-500">दिन में 3 बार (सुबह, दोपहर, रात)</div>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="font-bold text-indigo-700 flex items-center gap-1.5">
                  <span>SOS</span>
                  <span className="text-slate-400 font-normal">| ⚠️</span>
                </div>
                <div className="text-slate-700 mt-0.5">{t('sig.sos', 'Only when needed')}</div>
                <div className="text-[11px] text-slate-500">ज़रूरत पड़ने पर (दर्द या बुख़ार)</div>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="font-bold text-indigo-700">Tab / Cap</div>
                <div className="text-slate-700 mt-0.5">Tablet / Capsule</div>
                <div className="text-[11px] text-slate-500">गोली या कैप्सूल</div>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="font-bold text-indigo-700">mg / ml</div>
                <div className="text-slate-700 mt-0.5">Strength / Quantity</div>
                <div className="text-[11px] text-slate-500">दवा की मात्रा (पावर)</div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setShowGlossary(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg cursor-pointer transition-colors"
              >
                {t('common.close', 'Close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
