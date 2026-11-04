import React, { useState } from 'react';
import { useLanguage, Language } from '../context/LanguageContext';
import { VolumeX, HelpCircle, X, Sun, Moon, Sunrise, Clock, Check } from 'lucide-react';

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
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-[#881337] bg-[#FFE4E6] border border-[#FDA4AF] rounded-xl hover:bg-[#FECDD3] transition-colors cursor-pointer min-h-[36px]"
        >
          <VolumeX className="w-4 h-4 text-[#BE123C]" aria-hidden="true" />
          <span>{t('common.stop_audio', 'Stop Voice')}</span>
        </button>
      )}

      {/* Language Buttons with Script Names (English / हिन्दी / ગુજરાતી / मराठी) */}
      <div
        className="inline-flex items-center bg-[#F4F2EC] p-0.5 rounded-xl border border-stone-200"
        role="group"
        aria-label="Select Language"
      >
        {languages.map((l) => {
          const isSelected = language === l.code;
          return (
            <button
              key={l.code}
              type="button"
              onClick={() => setLanguage(l.code)}
              aria-pressed={isSelected}
              className={`px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-semibold rounded-lg transition-all cursor-pointer min-h-[36px] flex items-center gap-1 ${
                isSelected
                  ? 'bg-[#0F5147] text-white shadow-2xs'
                  : 'text-[#1C252E] hover:bg-white/60'
              }`}
            >
              <span>{l.nativeName}</span>
            </button>
          );
        })}
      </div>

      {/* Simple Guide / Medical Abbreviations Help Button */}
      <button
        type="button"
        onClick={() => setShowGlossary(true)}
        title="Plain Language & Medicine Timing Guide"
        className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-[#1C252E] bg-white border border-stone-300 rounded-xl hover:bg-[#FAF9F6] transition-colors cursor-pointer min-h-[36px]"
      >
        <HelpCircle className="w-4 h-4 text-[#0F5147]" aria-hidden="true" />
        <span className="hidden lg:inline">गाइड / Guide</span>
      </button>

      {/* Plain Language Medical Guide Modal */}
      {showGlossary && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs"
        >
          <div className="bg-white rounded-xl max-w-lg w-full p-5 sm:p-6 shadow-md border border-stone-200 relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setShowGlossary(false)}
              className="absolute top-4 right-4 p-2 text-stone-500 hover:text-stone-800 rounded-lg hover:bg-stone-100 transition-colors cursor-pointer min-h-[40px] min-w-[40px] flex items-center justify-center"
              aria-label="Close guide"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2.5 mb-4 pr-10">
              <div className="w-10 h-10 rounded-xl bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center border border-[#9DC1BB] shrink-0">
                <HelpCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base sm:text-lg font-bold text-[#1C252E]">
                  {language === 'hi'
                    ? 'दवा का समय व सरल अर्थ'
                    : language === 'gu'
                    ? 'દવા લેવાનો સમય અને સરળ સમજૂતી'
                    : language === 'mr'
                    ? 'औषधाची वेळ व सोपा अर्थ'
                    : 'Medicine Timing Guide'}
                </h3>
                <p className="text-xs text-stone-600">
                  {language === 'hi'
                    ? 'पर्चे पर लिखे संक्षिप्त शब्दों का आसान मतलब'
                    : language === 'gu'
                    ? 'પ્રિસ્ક્રિપ્શનમાં લખેલા શબ્દોનો સરળ અર્થ'
                    : language === 'mr'
                    ? 'चिठ्ठीवरील संक्षिप्त शब्दांचा सोपा अर्थ'
                    : 'Clear explanations for prescription abbreviations'}
                </p>
              </div>
            </div>

            <div className="space-y-2.5 text-xs sm:text-sm">
              <div className="p-3 bg-[#FAF9F6] rounded-xl border border-stone-200 flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center shrink-0 font-bold text-xs">
                  OD
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-[#1C252E] flex items-center gap-1.5">
                    <Sun className="w-4 h-4 text-amber-600" aria-hidden="true" />
                    <span>{t('sig.od', 'Once a day')}</span>
                  </div>
                  <p className="text-stone-600 text-xs mt-0.5">
                    {language === 'hi' ? 'दिन में केवल एक बार' : language === 'gu' ? 'દિવસમાં ૧ વાર' : language === 'mr' ? 'दिवसातून १ वेळा' : 'Take 1 time daily, usually in the morning'}
                  </p>
                </div>
              </div>

              <div className="p-3 bg-[#FAF9F6] rounded-xl border border-stone-200 flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center shrink-0 font-bold text-xs">
                  BD
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-[#1C252E] flex items-center gap-1.5">
                    <Sunrise className="w-4 h-4 text-amber-600" aria-hidden="true" />
                    <Moon className="w-4 h-4 text-stone-600" aria-hidden="true" />
                    <span>{t('sig.bd', 'Twice a day (Morning & Night)')}</span>
                  </div>
                  <p className="text-stone-600 text-xs mt-0.5">
                    {language === 'hi' ? 'सुबह और रात को' : language === 'gu' ? 'સવારે અને રાત્રે' : language === 'mr' ? 'सकाळी आणि रात्री' : 'Take in morning and at night with 12 hour gap'}
                  </p>
                </div>
              </div>

              <div className="p-3 bg-[#FAF9F6] rounded-xl border border-stone-200 flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center shrink-0 font-bold text-xs">
                  TDS
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-[#1C252E] flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-[#0F5147]" aria-hidden="true" />
                    <span>{t('sig.tds', 'Three times a day (Morning, Afternoon, Night)')}</span>
                  </div>
                  <p className="text-stone-600 text-xs mt-0.5">
                    {language === 'hi' ? 'सुबह, दोपहर और रात को' : language === 'gu' ? 'સવાર, બપોર અને રાત્રે' : language === 'mr' ? 'सकाळी, दुपारी आणि रात्री' : 'Take morning, afternoon, and night with food'}
                  </p>
                </div>
              </div>

              <div className="p-3 bg-[#FAF9F6] rounded-xl border border-stone-200 flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#FEF3C7] text-[#78350F] flex items-center justify-center shrink-0 font-bold text-xs border border-[#FCD34D]">
                  SOS
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-bold text-[#78350F] flex items-center gap-1.5">
                    <span>{t('sig.sos', 'Take only when you have pain or fever')}</span>
                  </div>
                  <p className="text-stone-600 text-xs mt-0.5">
                    {language === 'hi' ? 'दवा सिर्फ ज़रूरत पड़ने पर लें' : language === 'gu' ? 'માત્ર જરૂર હોય ત્યારે જ લેવી' : language === 'mr' ? 'फक्त गरज असेल तेव्हाच घ्या' : 'Only take when you feel pain, fever, or symptoms'}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-5 p-3 rounded-xl bg-[#E6F0EE] border border-[#9DC1BB] text-xs text-[#0F5147] flex items-start gap-2">
              <Check className="w-4 h-4 text-[#0F5147] shrink-0 mt-0.5" />
              <span>
                {language === 'hi'
                  ? 'दवा की खुराक या समय में कोई भी संदेह होने पर अपने डॉक्टर या दवा विक्रेता (केमिस्ट) से सलाह लें।'
                  : language === 'gu'
                  ? 'દવા લેવામાં કોઈ પણ શંકા હોય તો હંમેશા તમારા ડોક્ટર અથવા મેડિકલ સ્ટોરવાળાની સલાહ લો.'
                  : language === 'mr'
                  ? 'औषधाबद्दल कोणतीही शंका असल्यास नेहमी आपल्या डॉक्टरांचा किंवा केमिस्टचा सल्ला घ्या.'
                  : 'Always check with your doctor or pharmacist if you are unsure about any medicine timing.'}
              </span>
            </div>

            <div className="mt-5">
              <button
                type="button"
                onClick={() => setShowGlossary(false)}
                className="w-full py-2.5 rounded-xl bg-[#0F5147] text-white font-semibold text-sm hover:bg-[#0A3831] transition min-h-[48px] cursor-pointer"
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

export default LanguageSwitcher;
