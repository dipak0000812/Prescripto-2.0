import React from 'react';
import {
  Sun,
  SunMedium,
  Moon,
  Pill,
  FlaskConical,
  Droplets,
  Syringe,
  Sparkles,
  Volume2,
  Square,
  Edit3,
  AlertTriangle,
  Eye,
  Clock,
  UtensilsCrossed,
} from 'lucide-react';
import { Button } from './ui/Button';
import { DerivedSchedule, MedicineForm } from '../utils/medicationSchedule';
import { useLanguage } from '../context/LanguageContext';

interface MedicineHeroCardProps {
  schedule: DerivedSchedule;
  originalText?: string;
  onListen: () => void;
  isSpeaking: boolean;
  onEdit: () => void;
  onShowPhoto: () => void;
}

export const MedicineHeroCard: React.FC<MedicineHeroCardProps> = ({
  schedule,
  originalText,
  onListen,
  isSpeaking,
  onEdit,
  onShowPhoto,
}) => {
  const { t } = useLanguage();

  // Helper for medicine form icon & label
  const renderFormIcon = (form: MedicineForm) => {
    switch (form) {
      case 'syrup':
        return <FlaskConical className="w-5 h-5 text-[#0F5147]" aria-hidden="true" />;
      case 'drops':
        return <Droplets className="w-5 h-5 text-[#0F5147]" aria-hidden="true" />;
      case 'injection':
        return <Syringe className="w-5 h-5 text-[#0F5147]" aria-hidden="true" />;
      case 'ointment':
        return <Sparkles className="w-5 h-5 text-[#0F5147]" aria-hidden="true" />;
      case 'capsule':
      case 'tablet':
      default:
        return <Pill className="w-5 h-5 text-[#0F5147]" aria-hidden="true" />;
    }
  };

  const formLabel = t(`hero.${schedule.form}`, schedule.form);

  return (
    <article
      className={`rounded-2xl p-5 sm:p-6 transition shadow-xs text-left ${
        schedule.isUncertain
          ? 'bg-[#FFFBEB] border-2 border-[#FCD34D] ring-2 ring-[#FEF3C7]'
          : 'bg-white border border-stone-200 hover:border-stone-300'
      }`}
    >
      {/* 1. TOP BAR: Unsure Alert (if applicable) */}
      {schedule.isUncertain && (
        <div className="mb-4 p-3 rounded-xl bg-[#FEF3C7] border border-[#FCD34D] flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#B45309] shrink-0" aria-hidden="true" />
            <span className="text-xs font-bold text-[#78350F]">
              {t('hero.please_check', 'Please check this')}
              {schedule.uncertainReason && (
                <span className="font-normal block sm:inline sm:ml-1">
                  — {schedule.uncertainReason}
                </span>
              )}
            </span>
          </div>

          <button
            type="button"
            onClick={onShowPhoto}
            className="text-xs font-bold text-[#0F5147] hover:underline flex items-center gap-1 cursor-pointer bg-white px-2.5 py-1 rounded-lg border border-amber-300 shadow-2xs"
          >
            <Eye className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{t('hero.show_on_photo', 'Show on photo')}</span>
          </button>
        </div>
      )}

      {/* 2. MEDICINE NAME (Large), STRENGTH & FORM */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-4 border-b border-stone-100">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 rounded-lg bg-[#E6F0EE] border border-[#9DC1BB] flex items-center justify-center shrink-0">
              {renderFormIcon(schedule.form)}
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#0F5147] bg-[#E6F0EE] px-2 py-0.5 rounded-md">
              {formLabel}
            </span>
            {schedule.strength && (
              <span className="text-xs font-semibold text-stone-700 bg-[#F4F2EC] px-2 py-0.5 rounded-md border border-stone-200">
                {schedule.strength}
              </span>
            )}
          </div>

          <h3 className="text-xl sm:text-2xl font-extrabold text-[#1C252E] tracking-tight leading-tight">
            {schedule.cleanName}
          </h3>

          {originalText && originalText !== schedule.cleanName && (
            <p className="text-xs text-stone-500 mt-0.5 font-mono truncate">
              Prescription line: &quot;{originalText}&quot;
            </p>
          )}
        </div>

        {/* Action Buttons: Listen & Edit (Touch target >= 48px) */}
        <div className="flex items-center gap-2 shrink-0 pt-1 sm:pt-0">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onListen}
            leftIcon={
              isSpeaking ? (
                <Square className="w-4 h-4 text-[#BE123C] animate-pulse" />
              ) : (
                <Volume2 className="w-4 h-4 text-[#0F5147]" />
              )
            }
            className={`min-h-[44px] ${isSpeaking ? 'bg-[#FFE4E6] text-[#BE123C] border-[#FDA4AF]' : ''}`}
            aria-label={`Listen to ${schedule.cleanName} directions`}
          >
            <span>{isSpeaking ? t('hero.stop_voice', 'Stop') : t('hero.listen', 'Listen')}</span>
          </Button>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onEdit}
            leftIcon={<Edit3 className="w-4 h-4 text-stone-600" />}
            className="min-h-[44px] text-stone-700 hover:bg-[#F4F2EC]"
            aria-label={`Edit ${schedule.cleanName} details`}
          >
            <span>{t('hero.edit', 'Edit')}</span>
          </Button>
        </div>
      </div>

      {/* 3. DAILY SCHEDULE ROW: 3 CLEAR SLOTS (Morning / Afternoon / Night) */}
      <div className="py-4">
        <label className="block text-xs font-bold uppercase tracking-wider text-stone-500 mb-2.5">
          Daily Schedule
        </label>

        {schedule.isOnlyIfNeeded ? (
          /* SOS / PRN Notice */
          <div className="p-4 rounded-xl bg-[#FEF3C7] border border-[#FCD34D] text-xs sm:text-sm text-[#78350F] flex items-center gap-3">
            <Clock className="w-5 h-5 text-[#B45309] shrink-0" aria-hidden="true" />
            <div>
              <span className="font-bold text-sm block">
                {t('hero.only_if_needed', 'Only if needed (fever / pain)')}
              </span>
              <span className="text-xs text-stone-700">
                Do not take on a daily fixed schedule. Take only when symptom occurs.
              </span>
            </div>
          </div>
        ) : (
          /* 3 Slots Grid: Morning / Afternoon / Night */
          <div className="grid grid-cols-3 gap-2 sm:gap-3">
            {/* Slot 1: Morning */}
            <div
              className={`p-3 rounded-xl border text-center transition ${
                schedule.morningCount > 0
                  ? 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]'
                  : 'bg-[#FAF9F6] border-stone-200 text-stone-400'
              }`}
            >
              <div className="flex items-center justify-center gap-1 text-xs font-bold uppercase tracking-wider mb-1">
                <Sun className={`w-4 h-4 ${schedule.morningCount > 0 ? 'text-[#0F5147]' : 'text-stone-400'}`} aria-hidden="true" />
                <span>{t('hero.morning', 'Morning')}</span>
              </div>
              <p
                className={`text-sm sm:text-base font-extrabold ${
                  schedule.morningCount > 0 ? 'text-[#0F5147]' : 'text-stone-400 font-normal'
                }`}
              >
                {schedule.morning}
              </p>
            </div>

            {/* Slot 2: Afternoon */}
            <div
              className={`p-3 rounded-xl border text-center transition ${
                schedule.afternoonCount > 0
                  ? 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]'
                  : 'bg-[#FAF9F6] border-stone-200 text-stone-400'
              }`}
            >
              <div className="flex items-center justify-center gap-1 text-xs font-bold uppercase tracking-wider mb-1">
                <SunMedium className={`w-4 h-4 ${schedule.afternoonCount > 0 ? 'text-[#0F5147]' : 'text-stone-400'}`} aria-hidden="true" />
                <span>{t('hero.afternoon', 'Afternoon')}</span>
              </div>
              <p
                className={`text-sm sm:text-base font-extrabold ${
                  schedule.afternoonCount > 0 ? 'text-[#0F5147]' : 'text-stone-400 font-normal'
                }`}
              >
                {schedule.afternoon}
              </p>
            </div>

            {/* Slot 3: Night */}
            <div
              className={`p-3 rounded-xl border text-center transition ${
                schedule.nightCount > 0
                  ? 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]'
                  : 'bg-[#FAF9F6] border-stone-200 text-stone-400'
              }`}
            >
              <div className="flex items-center justify-center gap-1 text-xs font-bold uppercase tracking-wider mb-1">
                <Moon className={`w-4 h-4 ${schedule.nightCount > 0 ? 'text-[#0F5147]' : 'text-stone-400'}`} aria-hidden="true" />
                <span>{t('hero.night', 'Night')}</span>
              </div>
              <p
                className={`text-sm sm:text-base font-extrabold ${
                  schedule.nightCount > 0 ? 'text-[#0F5147]' : 'text-stone-400 font-normal'
                }`}
              >
                {schedule.night}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 4. FOOTER ROW: Food Timing Chip + "For How Many Days" */}
      <div className="pt-3 border-t border-stone-100 flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
        {/* Food Timing Chip */}
        <div>
          {schedule.foodTiming === 'before_food' ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-[#E6F0EE] text-[#0F5147] border border-[#9DC1BB]">
              <UtensilsCrossed className="w-3.5 h-3.5 text-[#0F5147]" aria-hidden="true" />
              <span>{t('hero.before_food', 'Before food')}</span>
            </span>
          ) : schedule.foodTiming === 'after_food' ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
              <UtensilsCrossed className="w-3.5 h-3.5 text-[#047857]" aria-hidden="true" />
              <span>{t('hero.after_food', 'After food')}</span>
            </span>
          ) : schedule.foodTiming === 'with_food' ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-[#F4F2EC] text-[#1C252E] border border-stone-300">
              <UtensilsCrossed className="w-3.5 h-3.5 text-stone-600" aria-hidden="true" />
              <span>{t('hero.with_food', 'With food')}</span>
            </span>
          ) : (
            <span className="text-stone-500 italic text-xs">
              Meal timing: Check with chemist
            </span>
          )}
        </div>

        {/* Duration: Big Number + Days */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-stone-500 uppercase font-bold tracking-wider">
            {t('hero.for_days', 'For')}
          </span>
          {schedule.durationDays ? (
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-extrabold text-[#0F5147] leading-none">
                {schedule.durationDays}
              </span>
              <span className="text-xs font-bold text-stone-700">
                {t('hero.days', 'days')}
              </span>
            </div>
          ) : (
            <span className="text-xs font-semibold text-stone-700 bg-[#F4F2EC] px-2 py-0.5 rounded">
              {schedule.durationText || 'As prescribed'}
            </span>
          )}
        </div>
      </div>
    </article>
  );
};

