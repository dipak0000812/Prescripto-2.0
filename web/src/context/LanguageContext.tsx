import React, { createContext, useContext, useState, useEffect } from 'react';

export type Language = 'en' | 'hi' | 'gu' | 'mr';

export interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, fallback?: string) => string;
  speak: (text: string, forceLang?: Language) => void;
  isSpeaking: boolean;
  stopSpeaking: () => void;
  explainSig: (sig: string) => { timing: string; plain: string; icon: string };
}

const translations: Record<Language, Record<string, string>> = {
  en: {
    // Navigation & Common
    'nav.home': 'Home',
    'nav.prescriptions': 'Prescriptions',
    'nav.patient_directory': 'Patient Directory',
    'nav.review_queue': 'Review Queue',
    'nav.new_intake': 'Upload Prescription',
    'nav.my_portal': 'My Health Portal',
    'nav.my_records': 'My Medical Records',
    'nav.system_health': 'System Health',
    'nav.sign_in': 'Sign In',
    'nav.sign_out': 'Sign Out',
    'nav.logged_in_as': 'Logged in as',
    'common.search': 'Search',
    'common.filter': 'Filter',
    'common.all': 'All',
    'common.loading': 'Loading...',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.close': 'Close',
    'common.view': 'View',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.approved': 'Approved',
    'common.pending': 'Pending Review',
    'common.processing': 'Processing',
    'common.completed': 'Completed',
    'common.failed': 'Needs Attention',
    'common.listen': 'Listen',
    'common.speaking': 'Playing audio...',
    'common.stop_audio': 'Stop Voice',

    // Safety & Warnings
    'safety.title': 'Safety & Verification',
    'safety.duplicate': 'Duplicate Medicine Warning',
    'safety.high_dose': 'High Dosage Caution',
    'safety.allergy': 'Allergy Alert',
    'safety.doctor_verified': 'Verified by Doctor',
    'safety.pending_doctor': 'Awaiting Doctor Review',
    'safety.cdsco_approved': 'Govt. Approved Medicine (CDSCO)',

    // Upload & Ingestion
    'upload.title': 'Upload Your Prescription',
    'upload.subtitle': 'Take a clear photo or select a prescription image from your device',
    'upload.dropzone': 'Drag and drop your prescription photo here, or click to browse',
    'upload.hint': 'Supports JPEG, PNG, or PDF up to 20MB',
    'upload.button': 'Upload & Verify Prescription',
    'upload.processing': 'Analyzing prescription safely...',
    'upload.tips_title': 'Helpful Photography Tips',
    'upload.tip_light': 'Ensure bright lighting so words are clearly readable',
    'upload.tip_flat': 'Keep paper flat without deep folds or shadows',
    'upload.tip_stamp': 'Include the doctor seal and signature if available',

    // Patient Portal
    'portal.welcome': 'Welcome to Your Medication Guide',
    'portal.subtitle': 'Clear, simple information about your prescribed medicines and how to take them.',
    'portal.active_meds': 'Your Current Medicines',
    'portal.how_to_take': 'How to Take',
    'portal.timing': 'When to Take',
    'portal.morning': 'Morning (Breakfast)',
    'portal.afternoon': 'Afternoon (Lunch)',
    'portal.night': 'Night (Dinner)',
    'portal.sos': 'Only when needed',
    'portal.meals_after': 'Take after food',
    'portal.meals_before': 'Take before food / Empty stomach',
    'portal.meals_with': 'Take with water',
    'portal.audio_guide': 'Press the speaker button to hear how and when to take this medicine in your language.',
    'portal.ask_doctor': 'Always consult your doctor or local pharmacist if you feel unwell.',

    // Simple Medical Explanations
    'sig.od': 'Once a day',
    'sig.bd': 'Twice a day (Morning & Night)',
    'sig.tds': 'Three times a day (Morning, Afternoon, Night)',
    'sig.qid': 'Four times a day',
    'sig.sos': 'Take only when you have pain or fever',
    'sig.hs': 'Take at bedtime before sleeping',
    'sig.q4h': 'Every 4 hours as directed',
  },
  hi: {
    // Navigation & Common
    'nav.home': 'होम',
    'nav.prescriptions': 'पर्चे (Prescriptions)',
    'nav.patient_directory': 'मरीज़ सूची (Patients)',
    'nav.review_queue': 'डॉक्टर समीक्षा (Review)',
    'nav.new_intake': 'पर्चा अपलोड करें',
    'nav.my_portal': 'मेरा स्वास्थ्य पोर्टल',
    'nav.my_records': 'मेरी स्वास्थ्य फ़ाइल',
    'nav.system_health': 'सिस्टम स्थिति',
    'nav.sign_in': 'लॉग इन करें',
    'nav.sign_out': 'लॉग आउट',
    'nav.logged_in_as': 'लॉग इन किया हुआ:',
    'common.search': 'खोजें (Search)',
    'common.filter': 'फ़िल्टर करें',
    'common.all': 'सभी',
    'common.loading': 'लोड हो रहा है...',
    'common.save': 'सहेजें (Save)',
    'common.cancel': 'रद्द करें (Cancel)',
    'common.close': 'बंद करें (Close)',
    'common.view': 'देखें (View)',
    'common.delete': 'हटाएं (Delete)',
    'common.edit': 'बदलें (Edit)',
    'common.approved': 'स्वीकृत (Approved)',
    'common.pending': 'समीक्षा बाकी (Pending)',
    'common.processing': 'जांच जारी है...',
    'common.completed': 'सत्यापित (Completed)',
    'common.failed': 'जांच की आवश्यकता',
    'common.listen': 'सुनें (Listen)',
    'common.speaking': 'आवाज़ बज रही है...',
    'common.stop_audio': 'आवाज़ बंद करें',

    // Safety & Warnings
    'safety.title': 'दवा सुरक्षा व जांच',
    'safety.duplicate': 'दोहरी दवा चेतावनी (Duplicate)',
    'safety.high_dose': 'अधिक खुराक की चेतावनी (High Dose)',
    'safety.allergy': 'एलर्जी चेतावनी (Allergy Alert)',
    'safety.doctor_verified': 'डॉक्टर द्वारा सत्यापित',
    'safety.pending_doctor': 'डॉक्टर की समीक्षा बाकी है',
    'safety.cdsco_approved': 'सरकारी मान्यता प्राप्त दवा (CDSCO)',

    // Upload & Ingestion
    'upload.title': 'अपना डॉक्टर का पर्चा अपलोड करें',
    'upload.subtitle': 'अपने मोबाइल से पर्चे की साफ़ फ़ोटो लें या फ़ाइल चुनें',
    'upload.dropzone': 'पर्चे की फ़ोटो यहां खींचें या चुनने के लिए क्लिक करें',
    'upload.hint': 'JPEG, PNG या PDF (20MB तक) समर्थित है',
    'upload.button': 'पर्चा अपलोड व जांच करें',
    'upload.processing': 'पर्चे की सुरक्षित जांच हो रही है...',
    'upload.tips_title': 'अच्छी फ़ोटो लेने के सुझाव',
    'upload.tip_light': 'अच्छी रोशनी में फ़ोटो लें ताकि लिखावट साफ़ दिखे',
    'upload.tip_flat': 'कागज़ को सीधा रखें, परछाई या सिलवट न आने दें',
    'upload.tip_stamp': 'यदि डॉक्टर की मुहर या दस्तख़त हैं तो उसे भी फ़ोटो में शामिल करें',

    // Patient Portal
    'portal.welcome': 'आपकी दवा मार्गदर्शिका में स्वागत है',
    'portal.subtitle': 'आपकी लिखी गई दवाओं को कैसे और कब लेना है, इसकी सरल जानकारी।',
    'portal.active_meds': 'आपकी चालू दवाइयाँ',
    'portal.how_to_take': 'लेने का तरीका',
    'portal.timing': 'दवा का समय',
    'portal.morning': 'सुबह (नाश्ता)',
    'portal.afternoon': 'दोपहर (खाना)',
    'portal.night': 'रात (खाना/सोते समय)',
    'portal.sos': 'केवल ज़रूरत पड़ने पर',
    'portal.meals_after': 'खाना खाने के बाद लें',
    'portal.meals_before': 'खाना खाने से पहले / खाली पेट लें',
    'portal.meals_with': 'पानी के साथ लें',
    'portal.audio_guide': 'दवा लेने का समय व तरीका अपनी भाषा में सुनने के लिए स्पीकर बटन दबाएं।',
    'portal.ask_doctor': 'यदि कोई परेशानी महसूस हो तो तुरंत अपने डॉक्टर या नजदीकी फार्मासिस्ट से संपर्क करें।',

    // Simple Medical Explanations
    'sig.od': 'दिन में 1 बार',
    'sig.bd': 'दिन में 2 बार (सुबह और रात)',
    'sig.tds': 'दिन में 3 बार (सुबह, दोपहर और रात)',
    'sig.qid': 'दिन में 4 बार',
    'sig.sos': 'केवल दर्द या बुख़ार होने पर लें',
    'sig.hs': 'रात को सोने से पहले लें',
    'sig.q4h': 'हर 4 घंटे में आवश्यकतानुसार',
  },
  gu: {
    // Navigation & Common
    'nav.home': 'હોમ',
    'nav.prescriptions': 'પ્રિસ્ક્રિપ્શન્સ (દવાનું લિસ્ટ)',
    'nav.patient_directory': 'દર્દીઓની યાદી',
    'nav.review_queue': 'ડોક્ટર ચકાસણી',
    'nav.new_intake': 'નવું પ્રિસ્ક્રિપ્શન ઉમેરો',
    'nav.my_portal': 'મારું આરોગ્ય પોર્ટલ',
    'nav.my_records': 'મારા મેડિકલ રેકોર્ડ્સ',
    'nav.system_health': 'સિસ્ટમ સ્થિતિ',
    'nav.sign_in': 'લૉગ ઇન',
    'nav.sign_out': 'લૉગ આઉટ',
    'nav.logged_in_as': 'તમે લૉગ ઇન છો:',
    'common.search': 'શોધો (Search)',
    'common.filter': 'ફિલ્ટર',
    'common.all': 'બધા',
    'common.loading': 'લોડ થઈ રહ્યું છે...',
    'common.save': 'સાચવો (Save)',
    'common.cancel': 'રદ કરો (Cancel)',
    'common.close': 'બંધ કરો',
    'common.view': 'જુઓ (View)',
    'common.delete': 'કાઢી નાખો (Delete)',
    'common.edit': 'સુધારો (Edit)',
    'common.approved': 'મંજૂર થયેલ (Approved)',
    'common.pending': 'તપાસ બાકી (Pending)',
    'common.processing': 'ચકાસણી ચાલુ છે...',
    'common.completed': 'પૂર્ણ થયેલ (Completed)',
    'common.failed': 'ધ્યાન આપવાની જરૂર',
    'common.listen': 'સાંભળો (Listen)',
    'common.speaking': 'અવાજ શરૂ છે...',
    'common.stop_audio': 'અવાજ બંધ કરો',

    // Safety & Warnings
    'safety.title': 'દવા સલામતી અને ચકાસણી',
    'safety.duplicate': 'એકસરખી બે દવાની ચેતવણી',
    'safety.high_dose': 'વધારે ડોઝની ચેતવણી',
    'safety.allergy': 'એલર્જીની ચેતવણી',
    'safety.doctor_verified': 'ડોક્ટર દ્વારા પ્રમાણિત',
    'safety.pending_doctor': 'ડોક્ટરની ચકાસણી બાકી છે',
    'safety.cdsco_approved': 'સરકાર માન્ય દવા (CDSCO)',

    // Upload & Ingestion
    'upload.title': 'ડોક્ટરનું પ્રિસ્ક્રિપ્શન અપલોડ કરો',
    'upload.subtitle': 'તમારા મોબાઈલથી ચોખ્ખો ફોટો પાડો અથવા ફાઈલ પસંદ કરો',
    'upload.dropzone': 'પ્રિસ્ક્રિપ્શનનો ફોટો અહીં લાવો અથવા સિલેક્ટ કરો',
    'upload.hint': 'JPEG, PNG અથવા PDF (20MB સુધી)',
    'upload.button': 'પ્રિસ્ક્રિપ્શન અપલોડ કરો',
    'upload.processing': 'દવાઓની સલામત તપાસ થઈ રહી છે...',
    'upload.tips_title': 'સારો ફોટો લેવા માટેની સૂચનાઓ',
    'upload.tip_light': 'સારા અજવાળામાં ફોટો લો જેથી અક્ષરો સ્પષ્ટ વંચાય',
    'upload.tip_flat': 'કાગળને સીધો રાખો, પડછાયો કે કરચલી ના પડવા દો',
    'upload.tip_stamp': 'ડોક્ટરનો સિક્કો કે સહી હોય તો તેને પણ ફોટોમાં રાખો',

    // Patient Portal
    'portal.welcome': 'તમારી દવા માર્ગદર્શિકામાં સ્વાગત છે',
    'portal.subtitle': 'તમારી લખેલી દવાઓ ક્યારે અને કેવી રીતે લેવી તેની સરળ માહિતી.',
    'portal.active_meds': 'તમારી ચાલુ દવાઓ',
    'portal.how_to_take': 'લેવાની રીત',
    'portal.timing': 'દવાનો સમય',
    'portal.morning': 'સવારે (નાસ્તો)',
    'portal.afternoon': 'બપોરે (જમ્યા પછી)',
    'portal.night': 'રાત્રે (જમ્યા પછી/સૂતી વખતે)',
    'portal.sos': 'જ્યારે જરૂર હોય ત્યારે જ',
    'portal.meals_after': 'જમ્યા પછી લેવી',
    'portal.meals_before': 'જમ્યા પહેલાં / ભૂખ્યા પેટે લેવી',
    'portal.meals_with': 'પાણી સાથે લેવી',
    'portal.audio_guide': 'દવા લેવાની રીત ગુજરાતીમાં સાંભળવા માટે સ્પીકર બટન દબાવો.',
    'portal.ask_doctor': 'કોઈપણ તકલીફ જણાય તો તરત જ તમારા ડોક્ટર અથવા મેડિકલ સ્ટોરનો સંપર્ક કરવો.',

    // Simple Medical Explanations
    'sig.od': 'દિવસમાં ૧ વાર',
    'sig.bd': 'દિવસમાં ૨ વાર (સવાર અને રાત)',
    'sig.tds': 'દિવસમાં ૩ વાર (સવાર, બપોર અને રાત)',
    'sig.qid': 'દિવસમાં ૪ વાર',
    'sig.sos': 'માત્ર દુખાવો કે તાવ હોય ત્યારે જ લેવી',
    'sig.hs': 'રાત્રે સૂતા પહેલાં લેવી',
    'sig.q4h': 'દર ૪ કલાકે જરૂર મુજબ',
  },
  mr: {
    // Navigation & Common
    'nav.home': 'मुख्यपृष्ठ (Home)',
    'nav.prescriptions': 'औषध चिठ्ठ्या (Prescriptions)',
    'nav.patient_directory': 'रुग्ण यादी (Patients)',
    'nav.review_queue': 'डॉक्टर तपासणी (Review)',
    'nav.new_intake': 'चिठ्ठी अपलोड करा',
    'nav.my_portal': 'माझे आरोग्य पोर्टल',
    'nav.my_records': 'माझी आरोग्य नोंद',
    'nav.system_health': 'सिस्टम स्थिती',
    'nav.sign_in': 'लॉग इन',
    'nav.sign_out': 'लॉग आउट',
    'nav.logged_in_as': 'लॉग इन वापरकर्ता:',
    'common.search': 'शोधा (Search)',
    'common.filter': 'फिल्टर',
    'common.all': 'सर्व',
    'common.loading': 'लोड होत आहे...',
    'common.save': 'जतन करा (Save)',
    'common.cancel': 'रद्द करा (Cancel)',
    'common.close': 'बंद करा',
    'common.view': 'पहा (View)',
    'common.delete': 'हटवा (Delete)',
    'common.edit': 'संपादित करा (Edit)',
    'common.approved': 'मंजूर (Approved)',
    'common.pending': 'तपासणी बाकी (Pending)',
    'common.processing': 'तपासणी सुरू आहे...',
    'common.completed': 'पूर्ण झाले (Completed)',
    'common.failed': 'लक्ष देणे आवश्यक',
    'common.listen': 'ऐका (Listen)',
    'common.speaking': 'आवाज सुरू आहे...',
    'common.stop_audio': 'आवाज थांबवा',

    // Safety & Warnings
    'safety.title': 'औषध सुरक्षा व खात्री',
    'safety.duplicate': 'दोनदा औषध दिल्याचा इशारा (Duplicate)',
    'safety.high_dose': 'जास्त मात्रेचा इशारा (High Dose)',
    'safety.allergy': 'ऍलर्जी इशारा (Allergy Alert)',
    'safety.doctor_verified': 'डॉक्टरांनी प्रमाणित केलेले',
    'safety.pending_doctor': 'डॉक्टरांची तपासणी बाकी आहे',
    'safety.cdsco_approved': 'शासकीय मान्यताप्राप्त औषध (CDSCO)',

    // Upload & Ingestion
    'upload.title': 'डॉक्टरांची चिठ्ठी अपलोड करा',
    'upload.subtitle': 'तुमच्या मोबाईलमधून स्पष्ट फोटो काढा किंवा फाईल निवडा',
    'upload.dropzone': 'चिठ्ठीचा फोटो येथे आणा किंवा निवडण्यासाठी क्लिक करा',
    'upload.hint': 'JPEG, PNG किंवा PDF (20MB पर्यंत)',
    'upload.button': 'चिठ्ठी अपलोड व तपासणी करा',
    'upload.processing': 'औषधांची सुरक्षित तपासणी होत आहे...',
    'upload.tips_title': 'चांगला फोटो काढण्यासाठीच्या टिप्स',
    'upload.tip_light': 'चांगल्या प्रकाशात फोटो काढा जेणेकरून अक्षरे स्पष्ट दिसतील',
    'upload.tip_flat': 'कागद सरळ ठेवा, सावली किंवा घडी पडू देऊ नका',
    'upload.tip_stamp': 'डॉक्टरांचा शिक्का किंवा स्वाक्षरी असल्यास फोटोमध्ये ठेवा',

    // Patient Portal
    'portal.welcome': 'तुमच्या औषध मार्गदर्शिकेत स्वागत आहे',
    'portal.subtitle': 'तुमची लिहून दिलेली औषधे कधी आणि कशी घ्यायची याची सोपी माहिती.',
    'portal.active_meds': 'तुमची सध्याची औषधे',
    'portal.how_to_take': 'घेण्याची पद्धत',
    'portal.timing': 'औषधाची वेळ',
    'portal.morning': 'सकाळी (नाश्ता)',
    'portal.afternoon': 'दुपारी (जेवणानंतर)',
    'portal.night': 'रात्री (जेवणानंतर/झोपताना)',
    'portal.sos': 'फक्त गरज असेल तेव्हाच',
    'portal.meals_after': 'जेवणानंतर घ्या',
    'portal.meals_before': 'जेवणापूर्वी / उपाशीपोटी घ्या',
    'portal.meals_with': 'पाण्यासोबत घ्या',
    'portal.audio_guide': 'औषध घेण्याची माहिती मराठीत ऐकण्यासाठी स्पीकरचे बटण दाबा.',
    'portal.ask_doctor': 'कोणताही त्रास जाणवल्यास लगेच तुमच्या डॉक्टरांशी किंवा औषध विक्रेत्याशी संपर्क साधा.',

    // Simple Medical Explanations
    'sig.od': 'दिवसातून १ वेळा',
    'sig.bd': 'दिवसातून २ वेळा (सकाळी व रात्री)',
    'sig.tds': 'दिवसातून ३ वेळा (सकाळी, दुपारी व रात्री)',
    'sig.qid': 'दिवसातून ४ वेळा',
    'sig.sos': 'फक्त ताप किंवा दुखणे असल्यास घ्या',
    'sig.hs': 'रात्री झोपण्यापूर्वी घ्या',
    'sig.q4h': 'दर ४ तासांनी आवश्यकतेनुसार',
  },
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('prescripto_lang');
    return (saved as Language) || 'en';
  });

  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

  useEffect(() => {
    localStorage.setItem('prescripto_lang', language);
  }, [language]);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const t = (key: string, fallback?: string): string => {
    const langDict = translations[language] || translations.en;
    if (langDict[key]) return langDict[key];
    if (translations.en[key]) return translations.en[key];
    return fallback || key;
  };

  const speak = (text: string, forceLang?: Language) => {
    if (!('speechSynthesis' in window)) {
      alert('Text-to-speech is not supported in this browser.');
      return;
    }

    window.speechSynthesis.cancel();
    const langToUse = forceLang || language;
    const utterance = new SpeechSynthesisUtterance(text);

    // Set voice language code
    if (langToUse === 'hi') utterance.lang = 'hi-IN';
    else if (langToUse === 'gu') utterance.lang = 'gu-IN';
    else if (langToUse === 'mr') utterance.lang = 'mr-IN';
    else utterance.lang = 'en-IN';

    utterance.rate = 0.9; // Slightly slower for clear medical understanding
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const explainSig = (sig: string) => {
    const s = (sig || '').toUpperCase().trim();
    if (s.includes('BD') || s.includes('BID') || s.includes('TWICE')) {
      return {
        timing: t('sig.bd', 'Twice a day (Morning & Night)'),
        plain: t('portal.morning') + ' + ' + t('portal.night'),
        icon: '☀️ 🌙',
      };
    }
    if (s.includes('TDS') || s.includes('TID') || s.includes('THRICE')) {
      return {
        timing: t('sig.tds', 'Three times a day (Morning, Afternoon & Night)'),
        plain: t('portal.morning') + ' + ' + t('portal.afternoon') + ' + ' + t('portal.night'),
        icon: '☀️ 🌤️ 🌙',
      };
    }
    if (s.includes('OD') || s.includes('QD') || s.includes('ONCE')) {
      return {
        timing: t('sig.od', 'Once a day'),
        plain: t('portal.morning'),
        icon: '☀️',
      };
    }
    if (s.includes('SOS') || s.includes('PRN') || s.includes('NEED')) {
      return {
        timing: t('sig.sos', 'Take only when needed for pain or fever'),
        plain: t('portal.sos'),
        icon: '⚠️',
      };
    }
    if (s.includes('HS') || s.includes('BED') || s.includes('NIGHT')) {
      return {
        timing: t('sig.hs', 'Take at bedtime before sleeping'),
        plain: t('portal.night'),
        icon: '🌙',
      };
    }
    return {
      timing: s || t('portal.meals_after', 'Take after food'),
      plain: t('portal.meals_after', 'Take after food'),
      icon: '💊',
    };
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        t,
        speak,
        isSpeaking,
        stopSpeaking,
        explainSig,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
