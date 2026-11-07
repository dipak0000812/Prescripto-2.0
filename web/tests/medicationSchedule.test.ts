import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  detectMedicineForm,
  parseMedicationSchedule,
  cleanMedicineName,
} from '../src/utils/medicationSchedule.ts';

describe('Indian Prescription Shorthand & Schedule Parsing', () => {
  it('never defaults unknown form to tablet and recognizes liquid from 250/5 or 125/5 ratio', () => {
    // Unknown medicine without form keyword should NOT be guessed as tablet
    const unknownForm = detectMedicineForm('SomeUnknownDrug 500mg');
    assert.equal(unknownForm, null, 'Unknown medicine must not default to tablet');

    // 250/5 concentration implies syrup/liquid
    const calpolLiquid = detectMedicineForm('CALPOL 250/5');
    assert.equal(calpolLiquid, 'syrup', '250/5 concentration ratio must identify syrup/liquid form');

    const suspForm = detectMedicineForm('Crocin 120/5');
    assert.equal(suspForm, 'syrup', '120/5 concentration ratio must identify syrup/liquid form');
  });

  it('correctly detects inhaler and cream/gel/ointment', () => {
    assert.equal(detectMedicineForm('Asthalin Inhaler 2 puffs'), 'inhaler');
    assert.equal(detectMedicineForm('Duolin respules nebulizer'), 'inhaler');
    assert.equal(detectMedicineForm('Volini Gel'), 'ointment');
    assert.equal(detectMedicineForm('Betadine Cream'), 'ointment');
  });

  it('correctly parses q6h/q4h/q8h/q12h interval frequencies without flagging unusual', () => {
    const q6hResult = parseMedicationSchedule('Calpol 250/5', 'q6h');
    assert.equal(q6hResult.isUncertain, false, 'q6h must NOT be flagged as uncertain');
    assert.equal(q6hResult.intervalHours, 6, 'q6h should resolve to 6-hour interval');
    // q6h is 4 times a day (morning, afternoon, evening/night)
    assert.ok(q6hResult.morningCount > 0, 'q6h should have morning dose');
    assert.ok(q6hResult.afternoonCount > 0, 'q6h should have afternoon dose');
    assert.ok(q6hResult.nightCount > 0, 'q6h should have night dose');

    const q8hResult = parseMedicationSchedule('Corex DX', 'q8h');
    assert.equal(q8hResult.isUncertain, false, 'q8h must not be flagged uncertain');
    assert.equal(q8hResult.intervalHours, 8);

    const q4hResult = parseMedicationSchedule('Ciplox drops', 'q4h');
    assert.equal(q4hResult.isUncertain, false, 'q4h must not be flagged uncertain');
    assert.equal(q4hResult.intervalHours, 4);

    const q12hResult = parseMedicationSchedule('Augmentin 625', 'q12h');
    assert.equal(q12hResult.isUncertain, false);
    assert.equal(q12hResult.intervalHours, 12);
  });

  it('correctly maps 1-1-1 and fills morning, afternoon, night slots', () => {
    const res = parseMedicationSchedule('Paracetamol 650', '1-1-1');
    assert.equal(res.morningCount, 1);
    assert.equal(res.afternoonCount, 1);
    assert.equal(res.nightCount, 1);
    assert.notEqual(res.morning, '—');
    assert.notEqual(res.afternoon, '—');
    assert.notEqual(res.night, '—');
  });

  // Table of 40+ real-world Indian prescription shorthands
  const cases = [
    { text: 'Tab Paracetamol 650mg 1-0-1 x 5 days', form: 'tablet', morning: 1, afternoon: 0, night: 1, duration: '5 days' },
    { text: 'CALPOL 250/5 syp 5ml TDS x 3 days', form: 'syrup', morning: 1, afternoon: 1, night: 1, duration: '3 days' },
    { text: 'Calpol 120/5 susp 5ml q6h', form: 'syrup', interval: 6 },
    { text: 'Augmentin 625 BD pc x 7 days', form: 'tablet', morning: 1, afternoon: 0, night: 1, food: 'after_food', duration: '7 days' },
    { text: 'Azithral 500 OD x 3 days', form: 'tablet', morning: 1, afternoon: 0, night: 0, duration: '3 days' },
    { text: 'Pan 40 OD ac 30 mins', form: 'tablet', morning: 1, food: 'before_food' },
    { text: 'Syp Ambrolite 1 tsp TID', form: 'syrup', morning: 1, afternoon: 1, night: 1 },
    { text: 'Cap Omez 20mg OD empty stomach', form: 'capsule', morning: 1, food: 'before_food' },
    { text: 'Dolo 650 SOS for fever', form: 'tablet', sos: true, reason: 'fever' },
    { text: 'Combiflam PRN for pain', form: 'tablet', sos: true, reason: 'pain' },
    { text: 'Syp Corex DX 5ml q8h', form: 'syrup', interval: 8 },
    { text: 'Inj Ceftriaxone 1g IV OD', form: 'injection', morning: 1 },
    { text: 'Candid cream apply BID', form: 'ointment', morning: 1, night: 1 },
    { text: 'Otrivin nasal drops 2 drops TDS', form: 'drops', morning: 1, afternoon: 1, night: 1 },
    { text: 'Asthalin inhaler 2 puffs SOS', form: 'inhaler', sos: true },
    { text: 'Tab Pantocid 40 1-0-0 before food', form: 'tablet', morning: 1, afternoon: 0, night: 0, food: 'before_food' },
    { text: 'Tab Metformin 500mg 0-0-1 after food', form: 'tablet', morning: 0, afternoon: 0, night: 1, food: 'after_food' },
    { text: 'Tab Telma 40 1-0-0', form: 'tablet', morning: 1, afternoon: 0, night: 0 },
    { text: 'Tab Ecosprin 75 0-1-0 after lunch', form: 'tablet', morning: 0, afternoon: 1, night: 0, food: 'after_food' },
    { text: 'Amoxicillin 250mg/5ml susp 5ml TID', form: 'syrup', morning: 1, afternoon: 1, night: 1 },
    { text: 'Cpm 4mg HS', form: 'tablet', morning: 0, afternoon: 0, night: 1 },
    { text: 'Tab Clonazepam 0.5mg at bedtime', form: 'tablet', morning: 0, afternoon: 0, night: 1 },
    { text: 'Meftal Spas SOS for severe pain', form: 'tablet', sos: true, reason: 'pain' },
    { text: 'Zincovit 1-0-0 x 1 month', form: 'tablet', morning: 1, duration: '30 days' },
    { text: 'Becosules cap 1 daily x 15 days', form: 'capsule', morning: 1, duration: '15 days' },
    { text: 'Tab Cifran 500 QID', form: 'tablet', morning: 1, afternoon: 1, night: 1 },
    { text: 'Volini gel local application BD', form: 'ointment', morning: 1, afternoon: 0, night: 1 },
    { text: 'Betadine oint apply twice daily', form: 'ointment', morning: 1, afternoon: 0, night: 1 },
    { text: 'Ciplox eye drops 1 drop q4h', form: 'drops', interval: 4 },
    { text: 'Syp Zinc 20/5 5ml OD', form: 'syrup', morning: 1 },
    { text: 'Unknownmed 50mg 1-0-1', form: null, morning: 1, afternoon: 0, night: 1 },
    { text: 'Paracetamol 250/5', form: 'syrup' },
    { text: 'Azithromycin 200/5 suspension', form: 'syrup' },
    { text: 'Tab Voveran 50mg BD pc', form: 'tablet', morning: 1, night: 1, food: 'after_food' },
    { text: 'Tab Limcee 500mg chewable OD', form: 'tablet', morning: 1 },
    { text: 'Duolin respules via nebulizer q6h', form: 'inhaler', interval: 6 },
    { text: 'Tab Glycomet-GP 1 1-0-1 before meals', form: 'tablet', morning: 1, night: 1, food: 'before_food' },
    { text: 'Moxikind-CV 625 1 tab BID x 5 days', form: 'tablet', morning: 1, night: 1, duration: '5 days' },
    { text: 'Supradyn 1 cap daily after breakfast', form: 'capsule', morning: 1, food: 'after_food' },
    { text: 'Syrup Grilinctus 10ml thrice daily', form: 'syrup', morning: 1, afternoon: 1, night: 1 },
    { text: 'Tab Rantac 150mg BD 30 min before food', form: 'tablet', morning: 1, night: 1, food: 'before_food' },
    { text: 'Tab Shelcal 500 0-0-1 with milk', form: 'tablet', night: 1 },
    { text: 'Crocin 120/5 syrup 5ml SOS', form: 'syrup', sos: true },
    { text: 'Mucaine gel 2 tsp after meals TDS', form: 'syrup', morning: 1, afternoon: 1, night: 1, food: 'after_food' },
  ];

  cases.forEach((c, idx) => {
    it(`Case #${idx + 1}: parses "${c.text}" correctly`, () => {
      const schedule = parseMedicationSchedule(c.text);
      if (c.form !== undefined) {
        assert.equal(schedule.form, c.form, `Expected form ${c.form} for "${c.text}", got ${schedule.form}`);
      }
      if (c.morning !== undefined) {
        assert.equal(schedule.morningCount, c.morning, `Expected morning count ${c.morning} for "${c.text}"`);
      }
      if (c.afternoon !== undefined) {
        assert.equal(schedule.afternoonCount, c.afternoon, `Expected afternoon count ${c.afternoon} for "${c.text}"`);
      }
      if (c.night !== undefined) {
        assert.equal(schedule.nightCount, c.night, `Expected night count ${c.night} for "${c.text}"`);
      }
      if (c.interval !== undefined) {
        assert.equal(schedule.intervalHours, c.interval, `Expected interval ${c.interval} for "${c.text}"`);
      }
      if (c.food !== undefined) {
        assert.equal(schedule.foodTiming, c.food, `Expected food timing ${c.food} for "${c.text}"`);
      }
      if (c.duration !== undefined) {
        assert.equal(schedule.durationText, c.duration, `Expected duration ${c.duration} for "${c.text}"`);
      }
      if (c.sos !== undefined) {
        assert.equal(schedule.isOnlyIfNeeded, c.sos, `Expected SOS ${c.sos} for "${c.text}"`);
      }
    });
  });
});

