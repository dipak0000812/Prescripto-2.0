/**
 * Medication Schedule & Plain-Language Derivation Utilities.
 * Strictly adheres to Class 6 reading level and Indian prescription patterns.
 */

export type MedicineForm = 'tablet' | 'capsule' | 'syrup' | 'drops' | 'injection' | 'ointment' | 'inhaler' | 'other' | null;
export type FoodTiming = 'before_food' | 'after_food' | 'with_food' | 'unspecified';

export interface DerivedSchedule {
  cleanName: string;
  strength: string;
  form: MedicineForm;
  intervalHours?: number;
  morning: string; // "1 tab", "5 ml", "—"
  afternoon: string;
  night: string;
  morningCount: number;
  afternoonCount: number;
  nightCount: number;
  foodTiming: FoodTiming;
  durationDays: string | null; // e.g. "5"
  durationText: string; // e.g. "5 days"
  isOnlyIfNeeded: boolean;
  asNeededReason?: string;
  isUncertain: boolean;
  uncertainReason?: string;
}

/**
 * Detect medicine physical form (Tablet, Capsule, Syrup, Inhaler, etc.)
 * Never defaults to 'tablet' — returns null if unknown.
 */
export function detectMedicineForm(rawText: string, route?: string | null): MedicineForm {
  const t = (rawText + ' ' + (route || '')).toLowerCase();

  // 1. Ratio concentrations like "250/5" or "120/5" (mg per 5 ml liquid)
  if (/\b\d+(?:\.\d+)?\s*\/\s*5(?:\s*ml)?\b/i.test(t)) return 'syrup';

  // 2. Oral antacids, suspensions, or gels (e.g. "Mucaine gel", "oral gel")
  if (/\b(mucaine\s+gel|antacid\s+gel|oral\s+gel)\b/i.test(t)) return 'syrup';
  if (/\b(syp|syr|syrup|susp|suspension|liquid|solution|elixir|linctus|paediatric drops|pediatric drops)\b/i.test(t)) return 'syrup';

  // 3. Inhalers, respules, nebulizer solutions
  if (/\b(inhaler|rotahaler|respule|respules|nebulizer|puffs?|inhalation)\b/i.test(t)) return 'inhaler';

  // 4. Drops (eye, ear, nasal)
  if (/\b(drop|drops|eye drop|ear drop|nasal drop|eye drops|ear drops|nasal drops)\b/i.test(t)) return 'drops';

  // 5. Injections
  if (/\b(inj|injection|amp|vial|iv|im)\b/i.test(t)) return 'injection';

  // 6. Capsules
  if (/\b(cap|capsule|caps|capsules)\b/i.test(t)) return 'capsule';

  // 7. Tablets (markers or common Indian solid dosage oral brand names)
  if (/\b(tab|tablet|tabs|tablets|caplet|chewable)\b/i.test(t)) return 'tablet';
  if (/\b(augmentin|azithral|pan\s*\d+|dolo|combiflam|meftal|zincovit|cpm)\b/i.test(t)) return 'tablet';

  // 8. Ointment / topical cream / topical gel
  if (/\b(cream|oint|ointment|lotion|paste|liniment|local application|gel)\b/i.test(t)) return 'ointment';

  // Never guess or default to tablet
  return null;
}

/**
 * Clean medicine name by removing form prefixes (e.g. "Tab Paracetamol" -> "Paracetamol")
 */
export function cleanMedicineName(rawName: string): { cleanName: string; detectedStrength: string } {
  let clean = rawName.trim();

  // Strip leading form markers: "Tab.", "Cap.", "Syr.", "Inj.", "Oint.", "Cream" etc.
  clean = clean.replace(/^(tab\.|tablet|tabs\.|cap\.|capsule|caps\.|syr\.|syrup|inj\.|injection|drop\.|drops|ointment|cream)\s+/i, '');

  // Extract strength if embedded in name (e.g. "Paracetamol 650mg", "CALPOL 250/5", or "Azithromycin 500")
  let detectedStrength = '';
  const ratioMatch = clean.match(/(\d+(?:\.\d+)?\s*\/\s*5(?:\s*ml)?)/i);
  const strengthMatch = clean.match(/(\d+(?:\.\d+)?\s*(?:mg|mcg|gm|g|ml|iu|%))/i);
  if (ratioMatch) {
    detectedStrength = ratioMatch[0].trim();
  } else if (strengthMatch) {
    detectedStrength = strengthMatch[0].trim();
  }

  return { cleanName: clean, detectedStrength };
}

/**
 * Derive 3-slot daily schedule (Morning / Afternoon / Night) from frequency, instructions, and dose.
 */
export function parseMedicationSchedule(
  name: string,
  rawFrequency?: string | null,
  rawInstructions?: string | null,
  rawDose?: string | null,
  rawStrength?: string | null,
  rawDuration?: string | null,
  route?: string | null,
  flaggedNeedsReview?: boolean
): DerivedSchedule {
  const combinedText = `${name} ${rawFrequency || ''} ${rawInstructions || ''} ${rawDose || ''}`.trim();
  const freqLower = (rawFrequency || '').toLowerCase().trim();
  const instLower = (rawInstructions || '').toLowerCase().trim();
  const combinedLower = combinedText.toLowerCase();

  const { cleanName, detectedStrength } = cleanMedicineName(name);
  const strength = rawStrength?.trim() || detectedStrength || '';
  const form = detectMedicineForm(combinedText, route);

  let morning = '0';
  let afternoon = '0';
  let night = '0';
  let morningCount = 0;
  let afternoonCount = 0;
  let nightCount = 0;
  let intervalHours: number | undefined = undefined;

  let isOnlyIfNeeded = false;
  let asNeededReason = 'fever / pain';
  let isUncertain = Boolean(flaggedNeedsReview);
  let uncertainReason: string | undefined = undefined;

  // 1. Check for SOS / PRN ("Only if needed")
  if (
    /\b(sos|prn|as needed|if needed|when needed|whenever needed|if fever|for pain|in case of pain)\b/.test(combinedLower)
  ) {
    isOnlyIfNeeded = true;
    if (/fever|temperature|pyrexia/.test(combinedLower)) {
      asNeededReason = 'fever';
    } else if (/pain|headache|bodyache/.test(combinedLower)) {
      asNeededReason = 'pain';
    } else if (/vomit|nausea/.test(combinedLower)) {
      asNeededReason = 'vomiting';
    } else if (/cough/.test(combinedLower)) {
      asNeededReason = 'cough';
    } else {
      asNeededReason = 'if needed';
    }
  }

  // 2. Check for Interval Frequencies (q4h, q6h, q8h, q12h, every N hours)
  const intervalMatch = combinedLower.match(/\b(?:q(\d+)h|every\s+(\d+)\s*(?:hours?|hrs?))\b/);
  if (intervalMatch) {
    const hours = parseInt(intervalMatch[1] || intervalMatch[2], 10);
    intervalHours = hours;
    isUncertain = false;
    uncertainReason = undefined;

    if (hours <= 4) {
      morning = '1'; afternoon = '1'; night = '1';
      morningCount = 1; afternoonCount = 1; nightCount = 1;
    } else if (hours <= 6) {
      // 4 times daily (spaced every 6 hours)
      morning = '1'; afternoon = '1'; night = '1';
      morningCount = 1; afternoonCount = 1; nightCount = 1;
    } else if (hours <= 8) {
      // 3 times daily
      morning = '1'; afternoon = '1'; night = '1';
      morningCount = 1; afternoonCount = 1; nightCount = 1;
    } else if (hours <= 12) {
      // Twice daily
      morning = '1'; afternoon = '0'; night = '1';
      morningCount = 1; afternoonCount = 0; nightCount = 1;
    } else {
      // Once daily
      morning = '1'; afternoon = '0'; night = '0';
      morningCount = 1; afternoonCount = 0; nightCount = 0;
    }
  }

  // 3. Parse 3-part numeric frequency notation (e.g. 1-0-1, 1-1-1, 1-0-0, 0-1-0, 0-0-1, 1/2-0-1/2)
  const patternMatch = combinedLower.match(/\b([0-2](?:\.[0-9]+|\/2)?)\s*[-+–—]\s*([0-2](?:\.[0-9]+|\/2)?)\s*[-+–—]\s*([0-2](?:\.[0-9]+|\/2)?)\b/);

  if (patternMatch) {
    morning = patternMatch[1];
    afternoon = patternMatch[2];
    night = patternMatch[3];

    morningCount = parseFloat(morning.replace('/2', '.5')) || 0;
    afternoonCount = parseFloat(afternoon.replace('/2', '.5')) || 0;
    nightCount = parseFloat(night.replace('/2', '.5')) || 0;
    isUncertain = false;
    uncertainReason = undefined;
  } else if (!isOnlyIfNeeded && !intervalHours) {
    // 4. Parse medical frequency abbreviations and plain words
    if (/\b(tds|tid|thrice daily|three times daily|three times a day|3 times a day|3 times daily|3 times)\b/.test(combinedLower)) {
      morning = '1';
      afternoon = '1';
      night = '1';
      morningCount = 1;
      afternoonCount = 1;
      nightCount = 1;
      isUncertain = false;
    } else if (/\b(bd|bid|twice daily|twice a day|2 times a day|2 times daily|two times daily|two times a day|morning and night|morning & night)\b/.test(combinedLower)) {
      morning = '1';
      afternoon = '0';
      night = '1';
      morningCount = 1;
      afternoonCount = 0;
      nightCount = 1;
      isUncertain = false;
    } else if (/\b(od|qd|once daily|once a day|1 time a day|1 time daily|daily|once in a day)\b/.test(combinedLower)) {
      if (/\b(bedtime|at bedtime|night|at night|hs|sleeping)\b/.test(combinedLower)) {
        morning = '0';
        afternoon = '0';
        night = '1';
        morningCount = 0;
        nightCount = 1;
      } else {
        morning = '1';
        afternoon = '0';
        night = '0';
        morningCount = 1;
      }
      isUncertain = false;
    } else if (/\b(hs|at bedtime|bedtime|before sleeping|night only|at night)\b/.test(combinedLower)) {
      morning = '0';
      afternoon = '0';
      night = '1';
      morningCount = 0;
      afternoonCount = 0;
      nightCount = 1;
      isUncertain = false;
    } else if (/\b(morning only|in the morning|mane)\b/.test(combinedLower)) {
      morning = '1';
      afternoon = '0';
      night = '0';
      morningCount = 1;
      isUncertain = false;
    } else if (/\b(afternoon only|noon only|in the afternoon)\b/.test(combinedLower)) {
      morning = '0';
      afternoon = '1';
      night = '0';
      afternoonCount = 1;
      isUncertain = false;
    } else if (/\b(qid|four times daily|4 times a day)\b/.test(combinedLower)) {
      morning = '1';
      afternoon = '1';
      night = '1';
      morningCount = 1;
      afternoonCount = 1;
      nightCount = 1;
      isUncertain = false;
    } else if (freqLower || instLower) {
      // Unmapped / ambiguous frequency case (e.g. "as directed", "weekly", "alternate days")
      isUncertain = true;
      uncertainReason = freqLower ? `Unusual timing: "${freqLower}"` : 'Timing not clear on prescription';
    } else {
      isUncertain = true;
      uncertainReason = 'Daily timing was not specified by doctor';
    }
  }

  // 5. Food Timing derivation ("Before food / After food / With food")
  let foodTiming: FoodTiming = 'unspecified';
  if (/\b(ac|before food|before meal|before meals|before breakfast|before lunch|before dinner|empty stomach|empty-stomach|खाली पेट|भूखे पेट)\b/.test(combinedLower)) {
    foodTiming = 'before_food';
  } else if (/\b(pc|after food|after meal|after meals|after breakfast|after lunch|after dinner|post-meal|खाना खाने के बाद)\b/.test(combinedLower)) {
    foodTiming = 'after_food';
  } else if (/\b(with food|with meals|along with food|with milk)\b/.test(combinedLower)) {
    foodTiming = 'with_food';
  }

  // 6. Duration parsing ("For how many days")
  let durationDays: string | null = null;
  let durationText = rawDuration || '';

  const durCandidate = `${rawDuration || ''} ${combinedText}`;
  const dayMatch = durCandidate.match(/\b(?:x\s*)?(\d+)\s*(?:days?|d|दिन|દિવસ|दिवस)\b/i);
  const weekMatch = durCandidate.match(/\b(\d+)\s*(?:weeks?|wk|wks?|हफ़्ते|અઠવાડિયા|आठवडे)\b/i);
  const monthMatch = durCandidate.match(/\b(\d+)\s*(?:months?|mo|महीने|મહિના)\b/i);
  const slashMatch = durCandidate.match(/\b(\d+)\s*\/\s*7\b/); // e.g. "5/7" means 5 days

  if (dayMatch) {
    durationDays = dayMatch[1];
    durationText = `${durationDays} days`;
  } else if (slashMatch) {
    durationDays = slashMatch[1];
    durationText = `${durationDays} days`;
  } else if (weekMatch) {
    const weeks = parseInt(weekMatch[1], 10);
    durationDays = String(weeks * 7);
    durationText = `${durationDays} days`;
  } else if (monthMatch) {
    const months = parseInt(monthMatch[1], 10);
    durationDays = String(months * 30);
    durationText = `${durationDays} days`;
  }

  // Format unit strings with form context (e.g. "1 tab", "5 ml")
  const unitLabel =
    form === 'syrup'
      ? '5 ml'
      : form === 'drops'
      ? 'drops'
      : form === 'inhaler'
      ? 'puffs'
      : form === 'ointment'
      ? 'application'
      : form === 'capsule'
      ? 'cap'
      : form === 'tablet'
      ? 'tab'
      : '';
  const morningLabel = morningCount > 0 ? (unitLabel ? `${morning} ${unitLabel}` : `${morning}`) : '—';
  const afternoonLabel = afternoonCount > 0 ? (unitLabel ? `${afternoon} ${unitLabel}` : `${afternoon}`) : '—';
  const nightLabel = nightCount > 0 ? (unitLabel ? `${night} ${unitLabel}` : `${night}`) : '—';

  return {
    cleanName,
    strength,
    form,
    intervalHours,
    morning: morningLabel,
    afternoon: afternoonLabel,
    night: nightLabel,
    morningCount,
    afternoonCount,
    nightCount,
    foodTiming,
    durationDays,
    durationText: durationText || (durationDays ? `${durationDays} days` : 'As prescribed'),
    isOnlyIfNeeded,
    asNeededReason,
    isUncertain,
    uncertainReason,
  };
}

/**
 * Generate spoken text in natural localized language for Web Speech synthesis.
 */
export function buildMedicationSpokenText(
  schedule: DerivedSchedule,
  lang: 'en' | 'hi' | 'gu' | 'mr' = 'en'
): string {
  const name = schedule.cleanName;
  const strength = schedule.strength ? ` ${schedule.strength}` : '';

  if (schedule.isOnlyIfNeeded) {
    const reason = schedule.asNeededReason || 'symptoms occur';
    switch (lang) {
      case 'hi':
        return `${name}${strength}। यह दवा केवल जरूरत पड़ने पर लें, जैसे ${reason} होने पर।`;
      case 'gu':
        return `${name}${strength}। આ દવા માત્ર જરૂર પડે ત્યારે જ લો, જેમ કે ${reason} વખતે.`;
      case 'mr':
        return `${name}${strength}। हे औषध फक्त गरज असेल तेव्हाच घ्या, जसे ${reason} झाल्यावर.`;
      default:
        return `${name}${strength}. Take only if needed, such as for ${reason}.`;
    }
  }

  if (schedule.intervalHours) {
    switch (lang) {
      case 'hi':
        return `${name}${strength}। हर ${schedule.intervalHours} घंटे में एक बार लें।`;
      case 'gu':
        return `${name}${strength}। દર ${schedule.intervalHours} કલાકે એક વાર લો.`;
      case 'mr':
        return `${name}${strength}। दर ${schedule.intervalHours} तासांनी एकदा घ्या.`;
      default:
        return `${name}${strength}. Take once every ${schedule.intervalHours} hours.`;
    }
  }

  const timesEn: string[] = [];
  const timesHi: string[] = [];
  const timesGu: string[] = [];
  const timesMr: string[] = [];

  if (schedule.morningCount > 0) {
    timesEn.push(`${schedule.morning} in the morning`);
    timesHi.push(`सुबह ${schedule.morning}`);
    timesGu.push(`સવારે ${schedule.morning}`);
    timesMr.push(`सकाळी ${schedule.morning}`);
  }
  if (schedule.afternoonCount > 0) {
    timesEn.push(`${schedule.afternoon} in the afternoon`);
    timesHi.push(`दोपहर में ${schedule.afternoon}`);
    timesGu.push(`બપોરે ${schedule.afternoon}`);
    timesMr.push(`दुपारी ${schedule.afternoon}`);
  }
  if (schedule.nightCount > 0) {
    timesEn.push(`${schedule.night} at night`);
    timesHi.push(`रात में ${schedule.night}`);
    timesGu.push(`રાત્રે ${schedule.night}`);
    timesMr.push(`रात्री ${schedule.night}`);
  }

  let foodEn = '';
  let foodHi = '';
  let foodGu = '';
  let foodMr = '';
  if (schedule.foodTiming === 'before_food') {
    foodEn = ', before food';
    foodHi = ', खाना खाने से पहले';
    foodGu = ', જમ્યા પહેલાં';
    foodMr = ', जेवणापूर्वी';
  } else if (schedule.foodTiming === 'after_food') {
    foodEn = ', after food';
    foodHi = ', खाना खाने के बाद';
    foodGu = ', જમ્યા પછી';
    foodMr = ', जेवणानंतर';
  } else if (schedule.foodTiming === 'with_food') {
    foodEn = ', with food or meals';
    foodHi = ', खाने के साथ';
    foodGu = ', ભોજન સાથે';
    foodMr = ', जेवणासोबत';
  }

  const durationEn = schedule.durationDays ? ` for ${schedule.durationDays} days` : '';
  const durationHi = schedule.durationDays ? ` ${schedule.durationDays} दिनों के लिए` : '';
  const durationGu = schedule.durationDays ? ` ${schedule.durationDays} દિવસ માટે` : '';
  const durationMr = schedule.durationDays ? ` ${schedule.durationDays} दिवसांसाठी` : '';

  switch (lang) {
    case 'hi':
      return `${name}${strength}। ${timesHi.join(', ')}${foodHi}${durationHi} लें।`;
    case 'gu':
      return `${name}${strength}। ${timesGu.join(', ')}${foodGu}${durationGu} લો.`;
    case 'mr':
      return `${name}${strength}। ${timesMr.join(', ')}${foodMr}${durationMr} घ्या.`;
    default:
      return `${name}${strength}. Take ${timesEn.join(', ')}${foodEn}${durationEn}.`;
  }
}

/**
 * Builds a friendly plain-text WhatsApp summary of all prescribed medicines and timings.
 */
export function buildWhatsAppShareText(schedules: DerivedSchedule[], date?: string): string {
  const header = `📋 *Prescripto AI — My Medicine Schedule*${date ? ` (${new Date(date).toLocaleDateString()})` : ''}\n`;
  const items = schedules.map((s, idx) => {
    const medName = `*${idx + 1}. ${s.cleanName}${s.strength ? ` ${s.strength}` : ''}*`;
    if (s.isOnlyIfNeeded) {
      return `${medName}\n   • Timing: Take only when needed (SOS)\n`;
    }
    const timingParts: string[] = [];
    if (s.morningCount > 0) timingParts.push(`Morning: ${s.morning}`);
    if (s.afternoonCount > 0) timingParts.push(`Afternoon: ${s.afternoon}`);
    if (s.nightCount > 0) timingParts.push(`Night: ${s.night}`);
    if (s.intervalHours) timingParts.push(`Every ${s.intervalHours} hours`);

    const foodNote =
      s.foodTiming === 'before_food'
        ? ' (Before food)'
        : s.foodTiming === 'after_food'
        ? ' (After food)'
        : s.foodTiming === 'with_food'
        ? ' (With food)'
        : '';
    const durationNote = s.durationText ? ` • Duration: ${s.durationText}` : '';

    return `${medName}\n   • Timing: ${timingParts.join(' | ') || 'As directed'}${foodNote}${durationNote}\n`;
  });

  const footer = `\n⚠️ *Important Notice:* This is an AI-assisted summary of a prescription. Always verify timings and dosages with your doctor or chemist before taking any medication.`;
  return `${header}\n${items.join('\n')}${footer}`;
}
