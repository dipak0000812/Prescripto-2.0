import React, { useState } from 'react';
import { X, Save, Edit3, Pill, Clock, UtensilsCrossed, Calendar } from 'lucide-react';
import { Button } from './ui/Button';
import { useLanguage } from '../context/LanguageContext';
import { DerivedSchedule } from '../utils/medicationSchedule';

interface EditMedicineModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (updated: {
    line_index: number;
    name: string;
    strength: string;
    frequency: string;
    instructions: string;
    duration: string;
  }) => Promise<void>;
  lineIndex: number;
  initialSchedule: DerivedSchedule;
  isSaving: boolean;
}

export const EditMedicineModal: React.FC<EditMedicineModalProps> = ({
  isOpen,
  onClose,
  onSave,
  lineIndex,
  initialSchedule,
  isSaving,
}) => {
  const { t } = useLanguage();

  const [name, setName] = useState<string>(initialSchedule.cleanName);
  const [strength, setStrength] = useState<string>(initialSchedule.strength || '');
  const [frequency, setFrequency] = useState<string>(() => {
    if (initialSchedule.isOnlyIfNeeded) return 'SOS';
    if (initialSchedule.morningCount > 0 && initialSchedule.nightCount > 0 && initialSchedule.afternoonCount === 0) return '1-0-1';
    if (initialSchedule.morningCount > 0 && initialSchedule.nightCount > 0 && initialSchedule.afternoonCount > 0) return '1-1-1';
    if (initialSchedule.morningCount > 0 && initialSchedule.nightCount === 0 && initialSchedule.afternoonCount === 0) return '1-0-0';
    if (initialSchedule.morningCount === 0 && initialSchedule.nightCount > 0 && initialSchedule.afternoonCount === 0) return '0-0-1';
    return '1-0-1';
  });
  const [foodTiming, setFoodTiming] = useState<string>(initialSchedule.foodTiming);
  const [duration, setDuration] = useState<string>(initialSchedule.durationDays ? `${initialSchedule.durationDays} days` : '5 days');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const instructions =
      foodTiming === 'before_food'
        ? 'Before food'
        : foodTiming === 'after_food'
        ? 'After food'
        : foodTiming === 'with_food'
        ? 'With food'
        : '';

    await onSave({
      line_index: lineIndex,
      name: name.trim(),
      strength: strength.trim(),
      frequency: frequency.trim(),
      instructions,
      duration: duration.trim(),
    });
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in"
    >
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-stone-200 relative text-left">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-stone-200">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#E6F0EE] text-[#0F5147] flex items-center justify-center border border-[#9DC1BB]">
              <Edit3 className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[#1C252E]">
                {t('hero.edit_title', 'Edit Medicine Details')}
              </h3>
              <p className="text-xs text-stone-500">Prescription line #{lineIndex + 1}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 text-stone-400 hover:text-stone-700 rounded-lg hover:bg-stone-100 transition min-h-[40px] min-w-[40px] flex items-center justify-center"
            aria-label="Close edit dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 pt-4">
          {/* Medicine Name */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-1.5">
              {t('hero.edit_name', 'Medicine Name')}
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 text-base font-bold bg-white border border-stone-300 rounded-xl text-[#1C252E] focus-visible:ring-2 focus-visible:ring-[#0F5147]"
              placeholder="e.g. Paracetamol"
            />
          </div>

          {/* Strength */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-1.5">
              {t('hero.edit_strength', 'Strength (e.g. 500mg)')}
            </label>
            <input
              type="text"
              value={strength}
              onChange={(e) => setStrength(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-white border border-stone-300 rounded-xl text-[#1C252E] focus-visible:ring-2 focus-visible:ring-[#0F5147]"
              placeholder="e.g. 650 mg"
            />
          </div>

          {/* Timing Presets */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-1.5">
              {t('hero.edit_timing', 'Daily Timing')}
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              {[
                { label: '1-0-1 (Morning & Night)', value: '1-0-1' },
                { label: '1-1-1 (3 times a day)', value: '1-1-1' },
                { label: '1-0-0 (Morning only)', value: '1-0-0' },
                { label: '0-0-1 (Night only)', value: '0-0-1' },
                { label: 'SOS (Only if needed)', value: 'SOS' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setFrequency(opt.value)}
                  className={`p-2.5 rounded-xl border font-semibold text-left transition cursor-pointer min-h-[44px] ${
                    frequency === opt.value
                      ? 'bg-[#0F5147] text-white border-[#0F5147]'
                      : 'bg-[#FAF9F6] text-[#1C252E] border-stone-200 hover:bg-[#F4F2EC]'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Food Timing */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-1.5">
              {t('hero.edit_food', 'Food Timing')}
            </label>
            <div className="grid grid-cols-3 gap-2 text-xs">
              {[
                { label: t('hero.after_food', 'After food'), value: 'after_food' },
                { label: t('hero.before_food', 'Before food'), value: 'before_food' },
                { label: t('hero.with_food', 'With food'), value: 'with_food' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setFoodTiming(opt.value)}
                  className={`p-2.5 rounded-xl border font-semibold text-center transition cursor-pointer min-h-[44px] ${
                    foodTiming === opt.value
                      ? 'bg-[#0F5147] text-white border-[#0F5147]'
                      : 'bg-[#FAF9F6] text-[#1C252E] border-stone-200 hover:bg-[#F4F2EC]'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Duration */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-1.5">
              {t('hero.edit_duration', 'How many days')}
            </label>
            <input
              type="text"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-white border border-stone-300 rounded-xl text-[#1C252E] focus-visible:ring-2 focus-visible:ring-[#0F5147]"
              placeholder="e.g. 5 days or 1 week"
            />
          </div>

          {/* Actions */}
          <div className="pt-3 flex items-center justify-end gap-3 border-t border-stone-100">
            <Button type="button" variant="ghost" onClick={onClose} disabled={isSaving}>
              {t('hero.edit_cancel', 'Cancel')}
            </Button>
            <Button
              type="submit"
              variant="primary"
              isLoading={isSaving}
              leftIcon={<Save className="w-4 h-4" />}
            >
              {t('hero.edit_save', 'Save changes')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

