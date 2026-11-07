import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, Minus, Plus } from 'lucide-react';
import { Button } from './ui/Button';
import { useLanguage } from '../context/LanguageContext';
import { DerivedSchedule } from '../utils/medicationSchedule';
import {
  SunriseIcon,
  MiddaySunIcon,
  MoonIcon,
  BeforeFoodIcon,
  AfterFoodIcon,
  WithFoodIcon,
} from './icons/HealthcareIcons';

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
  const parseInitialDays = (val: string | null | undefined): number => {
    if (!val) return 5;
    const parsed = parseInt(val, 10);
    return isNaN(parsed) || parsed <= 0 ? 5 : parsed;
  };

  const [foodTiming, setFoodTiming] = useState<string>(initialSchedule.foodTiming);
  const [durationDays, setDurationDays] = useState<number>(() => parseInitialDays(initialSchedule.durationDays));
  const [isAsNeededDuration, setIsAsNeededDuration] = useState<boolean>(() => !initialSchedule.durationDays && initialSchedule.isOnlyIfNeeded);
  const [customDuration, setCustomDuration] = useState<string>(initialSchedule.durationDays ? `${initialSchedule.durationDays} days` : '5 days');
  const [modalError, setModalError] = useState<string | null>(null);

  // Sync state whenever modal opens or initialSchedule changes
  useEffect(() => {
    if (isOpen) {
      setName(initialSchedule.cleanName);
      setStrength(initialSchedule.strength || '');
      setFoodTiming(initialSchedule.foodTiming);
      const days = parseInitialDays(initialSchedule.durationDays);
      setDurationDays(days);
      setIsAsNeededDuration(!initialSchedule.durationDays && initialSchedule.isOnlyIfNeeded);
      setCustomDuration(initialSchedule.durationDays ? `${days} days` : initialSchedule.isOnlyIfNeeded ? 'As needed' : '5 days');
      setModalError(null);
    }
  }, [isOpen, initialSchedule]);

  if (!isOpen) return null;

  const handleDaysChange = (newDays: number) => {
    const clamped = Math.max(1, Math.min(90, newDays));
    setDurationDays(clamped);
    setIsAsNeededDuration(false);
    setCustomDuration(`${clamped} days`);
  };

  const handleAsNeededToggle = () => {
    setIsAsNeededDuration(true);
    setCustomDuration('As needed');
  };

  const isValid = name.trim().length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);

    const cleanName = name.trim();
    if (!cleanName) {
      setModalError('Medicine name is required.');
      return;
    }

    const cleanDuration = isAsNeededDuration ? 'As needed' : customDuration.trim() || `${durationDays} days`;

    const instructions =
      foodTiming === 'before_food'
        ? 'Before food'
        : foodTiming === 'after_food'
        ? 'After food'
        : foodTiming === 'with_food'
        ? 'With food'
        : '';

    try {
      await onSave({
        line_index: lineIndex,
        name: cleanName,
        strength: strength.trim(),
        frequency: frequency.trim(),
        instructions,
        duration: cleanDuration,
      });
    } catch (err: any) {
      setModalError(err?.message || 'Could not update medicine. Please try again.');
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-medicine-heading"
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-stone-900/40 backdrop-blur-xs p-0 sm:p-4 animate-in fade-in"
    >
      <div className="bg-white rounded-t-3xl sm:rounded-2xl max-w-lg w-full max-h-[92vh] flex flex-col shadow-xl border border-stone-200 relative text-left overflow-hidden">
        {/* Mobile drag handle */}
        <div className="sm:hidden pt-3 pb-1 flex justify-center shrink-0">
          <div className="w-12 h-1 bg-stone-300 rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200 shrink-0">
          <div>
            <h3 id="edit-medicine-heading" className="text-lg font-bold text-ink">
              {t('hero.edit_title', 'Edit medicine details')}
            </h3>
            <p className="text-xs text-ink-muted">Prescription line #{lineIndex + 1}</p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 text-stone-400 hover:text-stone-700 rounded-xl hover:bg-stone-100 transition min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Close edit dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable form body */}
        <form onSubmit={handleSubmit} className="overflow-y-auto px-6 py-5 space-y-5 flex-1">
          {modalError && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-xs font-semibold text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{modalError}</span>
            </div>
          )}

          {/* Medicine Name */}
          <div>
            <label className="block text-xs font-semibold text-ink-muted mb-1.5">
              {t('hero.edit_name', 'Medicine name')} <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3.5 py-2.5 text-base font-medium bg-white border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand min-h-[44px]"
              placeholder="e.g. Paracetamol"
            />
          </div>

          {/* Strength */}
          <div>
            <label className="block text-xs font-semibold text-ink-muted mb-1.5">
              {t('hero.edit_strength', 'Strength')}
            </label>
            <input
              type="text"
              value={strength}
              onChange={(e) => setStrength(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm bg-white border border-stone-300 rounded-xl text-ink placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-brand min-h-[44px]"
              placeholder="e.g. 650 mg"
            />
          </div>

          {/* Daily Timing */}
          <div>
            <label className="block text-xs font-semibold text-ink-muted mb-2">
              {t('hero.edit_timing', 'Daily schedule')}
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              {[
                {
                  label: '1-0-1',
                  desc: 'Morning & Night',
                  value: '1-0-1',
                  icons: [SunriseIcon, MoonIcon],
                },
                {
                  label: '1-1-1',
                  desc: 'Three times a day',
                  value: '1-1-1',
                  icons: [SunriseIcon, MiddaySunIcon, MoonIcon],
                },
                {
                  label: '1-0-0',
                  desc: 'Morning only',
                  value: '1-0-0',
                  icons: [SunriseIcon],
                },
                {
                  label: '0-0-1',
                  desc: 'Night only',
                  value: '0-0-1',
                  icons: [MoonIcon],
                },
                {
                  label: 'SOS',
                  desc: 'Only if needed',
                  value: 'SOS',
                  icons: [],
                },
              ].map((opt) => {
                const isSelected = frequency === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setFrequency(opt.value)}
                    className={`p-2.5 rounded-xl border text-left transition cursor-pointer min-h-[48px] flex flex-col justify-between ${
                      isSelected
                        ? 'bg-brand text-white border-brand shadow-2xs'
                        : 'bg-paper text-ink border-stone-200 hover:bg-stone-50'
                    }`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <span className="font-bold text-sm">{opt.label}</span>
                      <div className="flex items-center gap-0.5">
                        {opt.icons.map((IconComp, idx) => (
                          <IconComp
                            key={idx}
                            className={`w-3.5 h-3.5 ${isSelected ? 'text-white/80' : 'text-ink-muted'}`}
                          />
                        ))}
                      </div>
                    </div>
                    <span className={`text-[11px] ${isSelected ? 'text-white/80' : 'text-ink-muted'}`}>
                      {opt.desc}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Food Timing */}
          <div>
            <label className="block text-xs font-semibold text-ink-muted mb-2">
              {t('hero.edit_food', 'Food timing')}
            </label>
            <div className="grid grid-cols-3 gap-2 text-xs">
              {[
                {
                  label: t('hero.after_food', 'After food'),
                  value: 'after_food',
                  icon: AfterFoodIcon,
                },
                {
                  label: t('hero.before_food', 'Before food'),
                  value: 'before_food',
                  icon: BeforeFoodIcon,
                },
                {
                  label: t('hero.with_food', 'With food'),
                  value: 'with_food',
                  icon: WithFoodIcon,
                },
              ].map((opt) => {
                const isSelected = foodTiming === opt.value;
                const IconComp = opt.icon;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setFoodTiming(opt.value)}
                    className={`p-3 rounded-xl border font-semibold text-center transition cursor-pointer min-h-[48px] flex items-center justify-center gap-1.5 ${
                      isSelected
                        ? 'bg-brand text-white border-brand shadow-2xs'
                        : 'bg-paper text-ink border-stone-200 hover:bg-stone-50'
                    }`}
                  >
                    <IconComp className={`w-4 h-4 shrink-0 ${isSelected ? 'text-white' : 'text-brand'}`} />
                    <span>{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Duration with Stepper */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-ink-muted">
                {t('hero.edit_duration', 'How many days')}
              </label>
              <button
                type="button"
                onClick={handleAsNeededToggle}
                className={`text-xs px-2.5 py-1 rounded-lg border font-medium transition cursor-pointer ${
                  isAsNeededDuration
                    ? 'bg-brand-soft text-brand border-brand'
                    : 'bg-paper text-ink-muted border-stone-200 hover:text-ink'
                }`}
              >
                As needed (SOS)
              </button>
            </div>

            {!isAsNeededDuration ? (
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => handleDaysChange(durationDays - 1)}
                  disabled={durationDays <= 1}
                  className="w-12 h-12 rounded-xl border border-stone-300 bg-paper hover:bg-stone-50 active:scale-95 flex items-center justify-center text-ink disabled:opacity-40 disabled:cursor-not-allowed transition"
                  aria-label="Decrease days"
                >
                  <Minus className="w-5 h-5" />
                </button>

                <div className="flex-1 text-center py-2 px-3 border border-stone-200 rounded-xl bg-stone-50">
                  <div className="text-lg font-bold text-ink">{durationDays} days</div>
                  <div className="text-[11px] text-ink-muted">
                    {durationDays === 7 ? '1 week' : durationDays === 14 ? '2 weeks' : durationDays === 30 ? '1 month' : `${durationDays} consecutive days`}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleDaysChange(durationDays + 1)}
                  disabled={durationDays >= 90}
                  className="w-12 h-12 rounded-xl border border-stone-300 bg-paper hover:bg-stone-50 active:scale-95 flex items-center justify-center text-ink disabled:opacity-40 disabled:cursor-not-allowed transition"
                  aria-label="Increase days"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <div className="p-3 text-center rounded-xl bg-brand-soft/50 border border-brand/20 text-xs text-brand font-medium">
                Take only when required for relief
              </div>
            )}
          </div>
        </form>

        {/* Footer Actions */}
        <div className="p-4 sm:px-6 bg-[#FAF9F6] border-t border-stone-200 flex items-center justify-end gap-3 shrink-0">
          <Button type="button" variant="ghost" onClick={onClose} disabled={isSaving}>
            {t('hero.edit_cancel', 'Cancel')}
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleSubmit}
            isLoading={isSaving}
            disabled={!isValid || isSaving}
            leftIcon={<Save className="w-4 h-4" />}
          >
            {t('hero.edit_save', 'Save changes')}
          </Button>
        </div>
      </div>
    </div>
  );
};
