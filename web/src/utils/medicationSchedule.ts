/**
 * Medication Schedule & Plain-Language Derivation Utilities.
 * Strictly adheres to Class 6 reading level and Indian prescription patterns.
 */

export type MedicineForm = 'tablet' | 'capsule' | 'syrup' | 'drops' | 'injection' | 'ointment' | 'other';
export type FoodTiming = 'before_food' | 'after_food' | 'with_food' | 'unspecified';

export interface DerivedSchedule {
  cleanName: string;
  strength: string;
  form: MedicineForm;
  morning: string; // "1 tablet", "1/2 tablet", "—"
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
 * Detect medicine physical form (Tablet, Capsule, Syrup, etc.)
 */
export function detectMedicineForm(rawText: string, route?: string | null): MedicineForm {
  const t = (rawText + ' ' + (route || '')).toLowerCase();

  if (/\b(tab|tablet|tabs|tablets|caplet)\b/.test(t)) return 'tablet';
  if (/\b(cap|capsule|caps|capsules)\b/.test(t)) return 'capsule';
  if (/\b(syr|syrup|susp|suspension|liquid|solution|elixir)\b/.test(t)) return 'syrup';
  if (/\b(drop|drops|eye drop|ear drop|nasal drop)\b/.test(t)) return 'drops';
  if (/\b(inj|injection|amp|vial|iv|im)\b/.test(t)) return 'injection';
  if (/\b(oint|ointment|cream|gel|lotion|paste|liniment)\b/.test(t)) return 'ointment';

  return 'tablet'; // Default form in standard practice
}

/**
 * Clean medicine name by removing form prefixes (e.g. "Tab Paracetamol" -> "Paracetamol")
 */
export function cleanMedicineName(rawName: string): { cleanName: string; detectedStrength: string } {
  let clean = rawName.trim();

  // Strip leading form markers: "Tab.", "Cap.", "Syr.", "Inj." etc.
  clean = clean.replace(/^(tab\.|tablet|cap\.|capsule|syr\.|syrup|inj\.|injection|drop\.|drops)\s+/i, '');

  // Extract strength if embedded in name (e.g. "Paracetamol 650mg" or "Azithromycin 500")
  let detectedStrength = '';
  const strengthMatch = clean.match(/(\d+(?:\.\d+)?\s*(?:mg|mcg|gm|g|ml|iu|%))/i);
  if (strengthMatch) {
    detectedStrength = strengthMatch[0].trim();
    // Do not remove strength from name if name becomes too short, but retain clean representation
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

  // 2. Parse 3-part numeric frequency notation (e.g. 1-0-1, 1-1-1, 1-0-0, 0-1-0, 0-0-1, 1/2-0-1/2)
  const patternMatch = combinedLower.match(/\b([0-2](?:\.[0-9]+|\/2)?)\s*[-+–—]\s*([0-2](?:\.[0-9]+|\/2)?)\s*[-+–—]\s*([0-2](?:\.[0-9]+|\/2)?)\b/);

  if (patternMatch) {
    morning = patternMatch[1];
    afternoon = patternMatch[2];
    night = patternMatch[3];

    morningCount = parseFloat(morning.replace('/2', '.5')) || 0;
    afternoonCount = parseFloat(afternoon.replace('/2', '.5')) || 0;
    nightCount = parseFloat(night.replace('/2', '.5')) || 0;
  } else if (!isOnlyIfNeeded) {
    // 3. Parse medical frequency abbreviations and plain words
    if (/\b(tds|tid|thrice daily|three times daily|three times a day|3 times a day|3 times daily|3 times)\b/.test(combinedLower)) {
      morning = '1';
      afternoon = '1';
      night = '1';
      morningCount = 1;
      afternoonCount = 1;
      nightCount = 1;
    } else if (/\b(bd|bid|twice daily|twice a day|2 times a day|2 times daily|two times daily|two times a day|morning and night|morning & night)\b/.test(combinedLower)) {
      morning = '1';
      afternoon = '0';
      night = '1';
      morningCount = 1;
      afternoonCount = 0;
      nightCount = 1;
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
    } else if (/\b(hs|at bedtime|bedtime|before sleeping|night only|at night)\b/.test(combinedLower)) {
      morning = '0';
      afternoon = '0';
      night = '1';
      morningCount = 0;
      afternoonCount = 0;
      nightCount = 1;
    } else if (/\b(morning only|in the morning|mane)\b/.test(combinedLower)) {
      morning = '1';
      afternoon = '0';
      night = '0';
      morningCount = 1;
    } else if (/\b(afternoon only|noon only|in the afternoon)\b/.test(combinedLower)) {
      morning = '0';
      afternoon = '1';
      night = '0';
      afternoonCount = 1;
    } else if (/\b(qid|four times daily|4 times a day)\b/.test(combinedLower)) {
      morning = '1';
      afternoon = '1';
      night = '1';
      morningCount = 1;
      afternoonCount = 1;
      nightCount = 1;
    } else if (freqLower || instLower) {
      // Unmapped / ambiguous frequency case (e.g. "as directed", "weekly", "alternate days")
      isUncertain = true;
      uncertainReason = freqLower ? `Unusual timing: "${freqLower}"` : 'Timing not clear on prescription';
    } else {
      isUncertain = true;
      uncertainReason = 'Daily timing was not specified by doctor';
    }
  }

  // 4. Food Timing derivation ("Before food / After food")
  let foodTiming: FoodTiming = 'unspecified';
  if (/\b(ac|before food|before meal|before meals|empty stomach|empty-stomach|खाली पेट|भूखे पेट)\b/.test(combinedLower)) {
    foodTiming = 'before_food';
  } else if (/\b(pc|after food|after meal|after meals|खाना खाने के बाद|post-meal|with food|with meals)\b/.test(combinedLower)) {
    foodTiming = 'after_food';
  } else if (/\b(with food|with meals|along with food)\b/.test(combinedLower)) {
    foodTiming = 'with_food';
  }

  // 5. Duration parsing ("For how many days")
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
    durationText = `${durationDays} days (${weeks} ${weeks === 1 ? 'week' : 'weeks'})`;
  } else if (monthMatch) {
    const months = parseInt(monthMatch[1], 10);
    durationDays = String(months * 30);
    durationText = `${durationDays} days (${months} ${months === 1 ? 'month' : 'months'})`;
  }

  // Format unit strings with form context (e.g. "1 tablet", "5 ml")
  const unitLabel = form === 'syrup' ? 'tsp / ml' : form === 'drops' ? 'drops' : form;
  const morningLabel = morningCount > 0 ? `${morning} ${unitLabel}` : '—';
  const afternoonLabel = afternoonCount > 0 ? `${afternoon} ${unitLabel}` : '—';
  const nightLabel = nightCount > 0 ? `${night} ${unitLabel}` : '—';

  return {
    cleanName,
    strength,
    form,
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
 * Build natural, comforting spoken audio text for a medicine in the given language.
 */
export function buildMedicationSpokenText(
  schedule: DerivedSchedule,
  lang: 'en' | 'hi' | 'gu' | 'mr'
): string {
  const name = schedule.cleanName;
  const strength = schedule.strength ? ` ${schedule.strength}` : '';
  const formName = schedule.form;

  if (lang === 'hi') {
    if (schedule.isOnlyIfNeeded) {
      return `${name}${strength}। यह दवा सिर्फ ज़रूरत पड़ने पर जैसे बुखार या दर्द में लें।`;
    }
    const timingParts: string[] = [];
    if (schedule.morningCount > 0) timingParts.push(`सुबह ${schedule.morning}`);
    if (schedule.afternoonCount > 0) timingParts.push(`दोपहर ${schedule.afternoon}`);
    if (schedule.nightCount > 0) timingParts.push(`रात ${schedule.night}`);
    const timeStr = timingParts.length > 0 ? timingParts.join(', ') : 'डॉक्टर के बताए अनुसार';
    const foodStr =
      schedule.foodTiming === 'before_food'
        ? 'खाना खाने से पहले'
        : schedule.foodTiming === 'after_food'
        ? 'खाना खाने के बाद'
        : '';
    const dayStr = schedule.durationDays ? `${schedule.durationDays} दिन तक` : '';
    return `${name}${strength}। ${timeStr} लें। ${foodStr}। ${dayStr}। दवा लेने से पहले डॉक्टर या केमिस्ट से ज़रूर पूछें।`;
  }

  if (lang === 'gu') {
    if (schedule.isOnlyIfNeeded) {
      return `${name}${strength}. આ દવા ફક્ત જરૂર પડે ત્યારે જ જેમ કે તાવ કે દુખાવામાં લો.`;
    }
    const timingParts: string[] = [];
    if (schedule.morningCount > 0) timingParts.push(`સવારે ${schedule.morning}`);
    if (schedule.afternoonCount > 0) timingParts.push(`બપોરે ${schedule.afternoon}`);
    if (schedule.nightCount > 0) timingParts.push(`રાત્રે ${schedule.night}`);
    const timeStr = timingParts.length > 0 ? timingParts.join(', ') : 'ડોક્ટરની સૂચના મુજબ';
    const foodStr =
      schedule.foodTiming === 'before_food'
        ? 'જમ્યા પહેલાં'
        : schedule.foodTiming === 'after_food'
        ? 'જમ્યા પછી'
        : '';
    const dayStr = schedule.durationDays ? `${schedule.durationDays} દિવસ માટે` : '';
    return `${name}${strength}. ${timeStr} લો. ${foodStr}. ${dayStr}.`;
  }

  if (lang === 'mr') {
    if (schedule.isOnlyIfNeeded) {
      return `${name}${strength}. हे औषध फक्त गरज असेल तेव्हाच ताप किंवा दुखण्यावर घ्या.`;
    }
    const timingParts: string[] = [];
    if (schedule.morningCount > 0) timingParts.push(`सकाळी ${schedule.morning}`);
    if (schedule.afternoonCount > 0) timingParts.push(`दुपारी ${schedule.afternoon}`);
    if (schedule.nightCount > 0) timingParts.push(`रात्री ${schedule.night}`);
    const timeStr = timingParts.length > 0 ? timingParts.join(', ') : 'डॉक्टरांच्या सल्ल्यानुसार';
    const foodStr =
      schedule.foodTiming === 'before_food'
        ? 'जेवणापूर्वी'
        : schedule.foodTiming === 'after_food'
        ? 'जेवणानंतर'
        : '';
    const dayStr = schedule.durationDays ? `${schedule.durationDays} दिवस` : '';
    return `${name}${strength}. ${timeStr} घ्या. ${foodStr}. ${dayStr}.`;
  }

  // Default English
  if (schedule.isOnlyIfNeeded) {
    return `${name}${strength} ${formName}. Take only when needed for ${schedule.asNeededReason}.`;
  }
  const timingParts: string[] = [];
  if (schedule.morningCount > 0) timingParts.push(`Morning: ${schedule.morning}`);
  if (schedule.afternoonCount > 0) timingParts.push(`Afternoon: ${schedule.afternoon}`);
  if (schedule.nightCount > 0) timingParts.push(`Night: ${schedule.night}`);
  const timeStr = timingParts.length > 0 ? timingParts.join(', ') : 'As directed';
  const foodStr =
    schedule.foodTiming === 'before_food'
      ? 'Before food'
      : schedule.foodTiming === 'after_food'
      ? 'After food'
      : '';
  const dayStr = schedule.durationDays ? `For ${schedule.durationDays} days` : '';
  return `${name}${strength} ${formName}. ${timeStr}. ${foodStr}. ${dayStr}. Always verify with your doctor or chemist.`;
}

/**
 * Build WhatsApp shareable message text.
 */
export function buildWhatsAppShareText(
  medications: DerivedSchedule[],
  date?: string | null
): string {
  const header = `*Prescripto 2.0 - Prescription Medicine Schedule*${date ? ` (${date})` : ''}\n\n`;

  const lines = medications.map((m, idx) => {
    const timing = m.isOnlyIfNeeded
      ? `• Timing: Only if needed (${m.asNeededReason || 'fever / pain'})`
      : `• Timing: Morning: ${m.morning} | Afternoon: ${m.afternoon} | Night: ${m.night}`;
    const food = m.foodTiming !== 'unspecified' ? ` (${m.foodTiming.replace('_', ' ')})` : '';
    const dur = m.durationDays ? ` for ${m.durationDays} days` : '';
    return `${idx + 1}. *${m.cleanName}* ${m.strength} [${m.form}]\n   ${timing}${food}${dur}`;
  });

  const footer = `\n\n_Note: This is a computer reading of the prescription. Please verify with a doctor or chemist before taking medicines._`;

  return header + lines.join('\n\n') + footer;
}

