import React from 'react';
import {
  Square,
  Edit3,
  Eye,
  Clock,
  MessageSquare,
} from 'lucide-react';
import { Button } from './ui/Button';
import { DerivedSchedule } from '../utils/medicationSchedule';
import { useLanguage } from '../context/LanguageContext';
import {
  SunriseIcon,
  MiddaySunIcon,
  MoonIcon,
  BeforeFoodIcon,
  AfterFoodIcon,
  WithFoodIcon,
  AlertAmberIcon,
  ListenIcon,
  getMedicineFormIcon,
} from './icons/HealthcareIcons';

interface MedicineHeroCardProps {
  schedule: DerivedSchedule;
  originalText?: string;
  onListen: () => void;
  isSpeaking: boolean;
  onEdit: () => void;
  onShowPhoto: () => void;
  onAsk?: () => void;
}

export const MedicineHeroCard: React.FC<MedicineHeroCardProps> = ({
  schedule,
  originalText,
  onListen,
  isSpeaking,
  onEdit,
  onShowPhoto,
  onAsk,
}) => {
  const { t } = useLanguage();

  const FormIcon = getMedicineFormIcon(schedule.form);
  const formLabel = schedule.form ? t(`hero.${schedule.form}`, schedule.form) : null;

  return (
    <article
      className={`rounded-2xl p-5 sm:p-6 transition shadow-xs text-left bg-white border ${
        schedule.isUncertain
          ? 'border-l-4 border-l-[#B45309] border-stone-200 shadow-2xs'
          : 'border-stone-200 hover:border-stone-300'
      }`}
    >
      {/* 1. TOP BAR: Uncertain / Unsure Alert with Calm Amber Left Accent */}
      {schedule.isUncertain && (
        <div className="mb-4 p-3 rounded-xl bg-[#FEF3C7]/60 border border-[#FCD34D] flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <AlertAmberIcon className="text-[#B45309] shrink-0" size={18} />
            <span className="text-xs font-bold text-[#78350F]">
              {t('hero.please_check', 'Please check this')}
              {schedule.uncertainReason && (
                <span className="font-normal block sm:inline sm:ml-1 text-stone-700">
                  — {schedule.uncertainReason}
                </span>
              )}
            </span>
          </div>

          <button
            type="button"
            onClick={onShowPhoto}
            className="text-xs font-bold text-[#0F5147] hover:underline flex items-center gap-1.5 cursor-pointer bg-white px-2.5 py-1.5 rounded-lg border border-amber-300 shadow-2xs min-h-[36px]"
          >
            <Eye className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{t('hero.show_on_photo', 'Show on photo')}</span>
          </button>
        </div>
      )}

      {/* 2. MEDICINE NAME (Large), STRENGTH, FORM ONLY IF KNOWN */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 pb-4 border-b border-stone-100">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <div className="w-8 h-8 rounded-lg bg-[#E6F0EE] border border-[#9DC1BB] flex items-center justify-center text-[#0F5147] shrink-0">
              <FormIcon size={18} />
            </div>

            {/* Form badge ONLY if known */}
            {formLabel && (
              <span className="text-xs font-bold uppercase tracking-wider text-[#0F5147] bg-[#E6F0EE] px-2 py-0.5 rounded-md">
                {formLabel}
              </span>
            )}

            {/* Strength */}
            {schedule.strength && (
              <span className="text-xs font-semibold text-stone-700 bg-[#F4F2EC] px-2 py-0.5 rounded-md border border-stone-200">
                {schedule.strength}
              </span>
            )}

            {/* Interval badge if q6h/q8h */}
            {schedule.intervalHours && (
              <span className="text-xs font-semibold text-[#0F5147] bg-[#E6F0EE] px-2 py-0.5 rounded-md">
                Every {schedule.intervalHours} hours
              </span>
            )}
          </div>

          <h3 className="text-xl sm:text-2xl font-bold text-[#1C252E] tracking-tight leading-tight">
            {schedule.cleanName}
          </h3>

          {originalText && originalText.trim().toLowerCase() !== schedule.cleanName.trim().toLowerCase() && (
            <p className="text-xs text-stone-500 mt-0.5 font-mono truncate">
              Prescription line: &quot;{originalText}&quot;
            </p>
          )}
        </div>

        {/* Action Buttons: Listen (Primary Green), Edit, Ask */}
        <div className="flex items-center gap-2 shrink-0 pt-1 sm:pt-0">
          {/* Primary Action Button: Listen */}
          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={onListen}
            leftIcon={
              isSpeaking ? (
                <Square className="w-4 h-4 text-white animate-pulse" />
              ) : (
                <ListenIcon size={18} className="text-white" />
              )
            }
            className={`min-h-[44px] ${
              isSpeaking
                ? 'bg-[#BE123C] hover:bg-[#9F1239]'
                : 'bg-[#0F5147] hover:bg-[#0A3831]'
            }`}
            aria-label={`Listen to ${schedule.cleanName} directions`}
          >
            <span>{isSpeaking ? t('hero.stop_voice', 'Stop') : t('hero.listen', 'Listen')}</span>
          </Button>

          {/* Secondary Action: Edit */}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onEdit}
            leftIcon={<Edit3 className="w-4 h-4 text-stone-600" />}
            className="min-h-[44px] text-stone-700 hover:bg-[#FAF9F6]"
            aria-label={`Edit ${schedule.cleanName} details`}
          >
            <span>{t('hero.edit', 'Edit')}</span>
          </Button>

          {/* Optional Action: Ask Assistant */}
          {onAsk && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onAsk}
              leftIcon={<MessageSquare className="w-4 h-4 text-[#0F5147]" />}
              className="min-h-[44px] text-[#0F5147] hover:bg-[#E6F0EE]"
              aria-label={`Ask assistant about ${schedule.cleanName}`}
            >
              <span>Ask</span>
            </Button>
          )}
        </div>
      </div>

      {/* 3. DAILY SCHEDULE ROW: 3 CLEAR SLOTS (Morning / Afternoon / Night) */}
      <div className="py-4">
        <label className="block text-xs font-bold uppercase tracking-wider text-stone-500 mb-2.5">
          Daily Schedule
        </label>

        {schedule.isOnlyIfNeeded ? (
          /* SOS / PRN Notice */
          <div className="p-4 rounded-xl bg-[#FAF9F6] border border-stone-200 text-xs sm:text-sm text-stone-700 flex items-center gap-3">
            <Clock className="w-5 h-5 text-amber-600 shrink-0" aria-hidden="true" />
            <div>
              <span className="font-bold text-sm text-[#1C252E] block">
                {t('hero.only_if_needed', 'Only if needed (fever / pain)')}
              </span>
              <span className="text-xs text-stone-600">
                {schedule.asNeededReason
                  ? `Take only for ${schedule.asNeededReason}. Do not take on a daily fixed schedule.`
                  : 'Do not take on a daily fixed schedule. Take only when symptom occurs.'}
              </span>
            </div>
          </div>
        ) : (
          /* 3 Slots Grid: Morning / Afternoon / Night */
          <div className="grid grid-cols-3 gap-2 sm:gap-3">
            {/* Slot 1: Morning */}
            <div
              className={`p-3 rounded-xl border text-center transition ${schedule.morningCount > 0
                ? 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]'
                : 'bg-[#FAF9F6] border-stone-200 text-stone-400'
                }`}
            >
              <div className="flex items-center justify-center gap-1.5 text-xs font-bold uppercase tracking-wider mb-1">
                <SunriseIcon
                  size={18}
                  className={schedule.morningCount > 0 ? 'text-[#0F5147]' : 'text-stone-400'}
                />
                <span>{t('hero.morning', 'Morning')}</span>
              </div>
              <p
                className={`text-sm sm:text-base font-extrabold ${schedule.morningCount > 0 ? 'text-[#0F5147]' : 'text-stone-400 font-normal'
                  }`}
              >
                {schedule.morning}
              </p>
            </div>

            {/* Slot 2: Afternoon */}
            <div
              className={`p-3 rounded-xl border text-center transition ${schedule.afternoonCount > 0
                ? 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]'
                : 'bg-[#FAF9F6] border-stone-200 text-stone-400'
                }`}
            >
              <div className="flex items-center justify-center gap-1.5 text-xs font-bold uppercase tracking-wider mb-1">
                <MiddaySunIcon
                  size={18}
                  className={schedule.afternoonCount > 0 ? 'text-[#0F5147]' : 'text-stone-400'}
                />
                <span>{t('hero.afternoon', 'Afternoon')}</span>
              </div>
              <p
                className={`text-sm sm:text-base font-extrabold ${schedule.afternoonCount > 0 ? 'text-[#0F5147]' : 'text-stone-400 font-normal'
                  }`}
              >
                {schedule.afternoon}
              </p>
            </div>

            {/* Slot 3: Night */}
            <div
              className={`p-3 rounded-xl border text-center transition ${schedule.nightCount > 0
                ? 'bg-[#E6F0EE] border-[#9DC1BB] text-[#0F5147]'
                : 'bg-[#FAF9F6] border-stone-200 text-stone-400'
                }`}
            >
              <div className="flex items-center justify-center gap-1.5 text-xs font-bold uppercase tracking-wider mb-1">
                <MoonIcon
                  size={18}
                  className={schedule.nightCount > 0 ? 'text-[#0F5147]' : 'text-stone-400'}
                />
                <span>{t('hero.night', 'Night')}</span>
              </div>
              <p
                className={`text-sm sm:text-base font-extrabold ${schedule.nightCount > 0 ? 'text-[#0F5147]' : 'text-stone-400 font-normal'
                  }`}
              >
                {schedule.night}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 4. FOOTER ROW: Food Timing & Duration as Plain Icon Lines (Not Pill Badges) */}
      <div className="pt-3 border-t border-stone-100 flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
        {/* Plain Icon Line for Food Timing */}
        <div className="flex items-center gap-2 text-stone-700">
          {schedule.foodTiming === 'before_food' ? (
            <>
              <BeforeFoodIcon size={18} className="text-[#0F5147] shrink-0" />
              <span className="font-semibold text-[#1C252E]">
                {t('hero.before_food', 'Take before food')}
              </span>
            </>
          ) : schedule.foodTiming === 'after_food' ? (
            <>
              <AfterFoodIcon size={18} className="text-[#0F5147] shrink-0" />
              <span className="font-semibold text-[#1C252E]">
                {t('hero.after_food', 'Take after food')}
              </span>
            </>
          ) : schedule.foodTiming === 'with_food' ? (
            <>
              <WithFoodIcon size={18} className="text-[#0F5147] shrink-0" />
              <span className="font-semibold text-[#1C252E]">
                {t('hero.with_food', 'Take with food / milk')}
              </span>
            </>
          ) : (
            <span className="text-stone-500 italic">
              Meal timing: Check with chemist or doctor
            </span>
          )}
        </div>

        {/* Plain Icon Line for Duration */}
        <div className="flex items-center gap-2 text-stone-700">
          <Clock className="w-4 h-4 text-stone-500 shrink-0" aria-hidden="true" />
          <span className="text-stone-600">
            {t('hero.for_days', 'For')}{' '}
            <strong className="text-[#1C252E] font-bold">
              {schedule.durationText || 'as directed by doctor'}
            </strong>
          </span>
        </div>
      </div>
    </article>
  );
};

export default MedicineHeroCard;
