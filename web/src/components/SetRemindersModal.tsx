import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  Clock,
  Calendar,
  AlertCircle,
  CheckCircle2,
  Download,
  Info,
  X,
  Plus,
  Smartphone,
  ChevronRight,
} from 'lucide-react';
import { Button } from './ui/Button';
import { DerivedSchedule } from '../utils/medicationSchedule';
import {
  createReminderPlansApi,
  getPlanIcsDownloadUrl,
} from '../api/reminders';
import {
  isPushSupported,
  registerServiceWorkerAndSubscribe,
} from '../utils/pushNotifications';
import { CreatePlanItem, ReminderPlanOut } from '../types/api';
import {
  SunriseIcon,
  MiddaySunIcon,
  MoonIcon,
} from './icons/HealthcareIcons';

interface ReminderItemState {
  enabled: boolean;
  medicationLineId?: string;
  name: string;
  dosageText: string;
  times: string[];
  durationDays: number | null;
}

interface SetRemindersModalProps {
  isOpen: boolean;
  onClose: () => void;
  analysisId: string;
  medications: Array<{
    id?: string;
    name: string;
    schedule: DerivedSchedule;
    originalText?: string;
  }>;
  onSuccess?: (createdPlans: ReminderPlanOut[]) => void;
}

export const SetRemindersModal: React.FC<SetRemindersModalProps> = ({
  isOpen,
  onClose,
  analysisId,
  medications,
  onSuccess,
}) => {
  const navigate = useNavigate();

  // Initialize reminder items from extracted medications
  const [items, setItems] = useState<ReminderItemState[]>(() =>
    medications.map((m) => {
      // Derive default times from schedule counts and food timing
      const derivedTimes: string[] = [];
      if (m.schedule.morningCount > 0) {
        derivedTimes.push(m.schedule.foodTiming === 'before_food' ? '08:00' : '09:00');
      }
      if (m.schedule.afternoonCount > 0) {
        derivedTimes.push(m.schedule.foodTiming === 'before_food' ? '13:00' : '14:00');
      }
      if (m.schedule.nightCount > 0) {
        derivedTimes.push(m.schedule.foodTiming === 'before_food' ? '20:00' : '21:00');
      }

      // Default fallback if no specific times extracted
      const finalTimes = derivedTimes.length > 0 ? derivedTimes : ['09:00', '21:00'];

      const parsedDuration = m.schedule.durationDays
        ? parseInt(m.schedule.durationDays, 10)
        : null;

      return {
        enabled: true,
        medicationLineId: m.id,
        name: m.name,
        dosageText: m.schedule.strength || (m.schedule.form ? `${m.schedule.form}` : ''),
        times: finalTimes,
        durationDays: isNaN(parsedDuration as number) ? null : parsedDuration,
      };
    })
  );

  const [requestPush, setRequestPush] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [createdPlans, setCreatedPlans] = useState<ReminderPlanOut[] | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [pushStatusMessage, setPushStatusMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleToggleItem = (index: number) => {
    setItems((prev) =>
      prev.map((it, idx) => (idx === index ? { ...it, enabled: !it.enabled } : it))
    );
  };

  const handleTimeChange = (itemIndex: number, timeIndex: number, newTime: string) => {
    setItems((prev) =>
      prev.map((it, idx) => {
        if (idx !== itemIndex) return it;
        const updatedTimes = [...it.times];
        updatedTimes[timeIndex] = newTime;
        return { ...it, times: updatedTimes };
      })
    );
  };

  const handleAddTime = (itemIndex: number) => {
    setItems((prev) =>
      prev.map((it, idx) => {
        if (idx !== itemIndex) return it;
        return { ...it, times: [...it.times, '14:00'] };
      })
    );
  };

  const handleRemoveTime = (itemIndex: number, timeIndex: number) => {
    setItems((prev) =>
      prev.map((it, idx) => {
        if (idx !== itemIndex) return it;
        const updated = it.times.filter((_, tIdx) => tIdx !== timeIndex);
        return { ...it, times: updated.length > 0 ? updated : ['09:00'] };
      })
    );
  };

  const handleDurationChange = (itemIndex: number, val: string) => {
    const num = parseInt(val, 10);
    setItems((prev) =>
      prev.map((it, idx) => {
        if (idx !== itemIndex) return it;
        return { ...it, durationDays: isNaN(num) || num <= 0 ? null : num };
      })
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setPushStatusMessage(null);
    setIsSubmitting(true);

    try {
      const activeItems = items.filter((it) => it.enabled);
      if (activeItems.length === 0) {
        setErrorMsg('Please select at least one medicine to schedule reminders.');
        setIsSubmitting(false);
        return;
      }

      const planItems: CreatePlanItem[] = activeItems.map((it) => ({
        medication_line_id: it.medicationLineId || null,
        medicine_name: it.name,
        dosage_text: it.dosageText || null,
        local_times: it.times,
        duration_days: it.durationDays,
      }));

      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata';

      const plans = await createReminderPlansApi({
        analysis_id: analysisId,
        timezone: tz,
        medications: planItems,
      });

      // Attempt push registration if requested
      if (requestPush && isPushSupported()) {
        try {
          const pushRes = await registerServiceWorkerAndSubscribe();
          if (pushRes.success) {
            setPushStatusMessage('Phone alerts turned on for this device.');
          } else if (pushRes.reason === 'denied') {
            setPushStatusMessage('Alerts were blocked in your browser settings. You can still check your Today screen.');
          }
        } catch {
          setPushStatusMessage('Could not activate push alerts. Calendar downloads remain available.');
        }
      }

      setCreatedPlans(plans);
      if (onSuccess) {
        onSuccess(plans);
      }
    } catch (err: any) {
      setErrorMsg(
        err.response?.data?.detail?.message ||
          err.response?.data?.detail ||
          err.message ||
          'Failed to schedule reminders. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-stone-900/40 backdrop-blur-xs flex items-end sm:items-center justify-center p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="reminders-modal-title"
    >
      <div className="relative w-full max-w-2xl bg-white rounded-t-3xl sm:rounded-2xl shadow-xl border border-stone-200 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Mobile handle */}
        <div className="sm:hidden pt-3 pb-1 flex justify-center shrink-0">
          <div className="w-12 h-1 bg-stone-300 rounded-full" />
        </div>

        {/* Header */}
        <div className="px-6 py-4 bg-paper border-b border-stone-200 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-soft flex items-center justify-center text-brand">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h2 id="reminders-modal-title" className="text-lg font-bold text-ink">
                Set daily reminders
              </h2>
              <p className="text-xs text-ink-muted">
                Pre-set times matching your prescription. You can adjust the exact alarm hours.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 text-stone-400 hover:text-stone-700 rounded-xl hover:bg-stone-100 min-h-[44px] min-w-[44px] flex items-center justify-center transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {errorMsg && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Success State */}
          {createdPlans ? (
            <div className="space-y-6 text-center py-6">
              <div className="w-14 h-14 mx-auto rounded-full bg-brand-soft text-brand flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8" />
              </div>

              <div>
                <h3 className="text-xl font-bold text-ink">Reminders scheduled</h3>
                <p className="text-sm text-ink-muted mt-1">
                  {createdPlans.length} medicine reminder plans have been scheduled.
                </p>
                {pushStatusMessage && (
                  <p className="text-xs font-semibold text-brand mt-2 bg-brand-soft py-1 px-3 rounded-full inline-block">
                    {pushStatusMessage}
                  </p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
                <Button
                  type="button"
                  variant="primary"
                  onClick={() => {
                    onClose();
                    navigate('/today');
                  }}
                  className="px-6"
                >
                  Go to Today's doses
                </Button>

                {createdPlans.length > 0 && (
                  <a
                    href={getPlanIcsDownloadUrl(createdPlans[0].id)}
                    download
                    className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold text-ink bg-paper border border-stone-200 hover:bg-stone-50 rounded-xl transition min-h-[48px]"
                  >
                    <Download className="w-4 h-4 text-brand" />
                    Download calendar (.ics)
                  </a>
                )}
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Medicine List */}
              <div className="space-y-4">
                {items.map((item, itemIdx) => (
                  <div
                    key={itemIdx}
                    className={`p-4 rounded-2xl border transition ${
                      item.enabled
                        ? 'bg-white border-stone-300 shadow-2xs'
                        : 'bg-stone-50 border-stone-200 opacity-60'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={item.enabled}
                          onChange={() => handleToggleItem(itemIdx)}
                          className="mt-1 h-5 w-5 rounded border-stone-300 text-brand focus:ring-brand"
                        />
                        <div>
                          <span className="font-bold text-ink text-base">{item.name}</span>
                          {item.dosageText && (
                            <p className="text-xs text-ink-muted">{item.dosageText}</p>
                          )}
                        </div>
                      </label>

                      {/* Duration input */}
                      {item.enabled && (
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="text-ink-muted">Days:</span>
                          <input
                            type="number"
                            min="1"
                            max="365"
                            value={item.durationDays || ''}
                            onChange={(e) => handleDurationChange(itemIdx, e.target.value)}
                            placeholder="Ongoing"
                            className="w-20 px-2.5 py-1.5 text-xs bg-paper border border-stone-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-brand text-ink"
                          />
                        </div>
                      )}
                    </div>

                    {/* Time chips */}
                    {item.enabled && (
                      <div className="mt-4 pt-3 border-t border-stone-100 space-y-2">
                        <span className="text-xs font-semibold text-ink-muted flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-brand" />
                          Reminder times:
                        </span>

                        <div className="flex flex-wrap items-center gap-2">
                          {item.times.map((tVal, tIdx) => {
                            const hour = parseInt(tVal.split(':')[0], 10);
                            const IconComp = hour < 12 ? SunriseIcon : hour < 18 ? MiddaySunIcon : MoonIcon;
                            return (
                              <div
                                key={tIdx}
                                className="flex items-center gap-1.5 bg-paper border border-stone-200 px-3 py-1.5 rounded-xl text-xs"
                              >
                                <IconComp className="w-3.5 h-3.5 text-ink-muted" />
                                <input
                                  type="time"
                                  value={tVal}
                                  onChange={(e) => handleTimeChange(itemIdx, tIdx, e.target.value)}
                                  className="bg-transparent font-bold text-ink focus:outline-none"
                                />
                                {item.times.length > 1 && (
                                  <button
                                    type="button"
                                    onClick={() => handleRemoveTime(itemIdx, tIdx)}
                                    className="text-stone-400 hover:text-red-600 p-0.5 ml-1 rounded-md"
                                    aria-label="Remove time"
                                  >
                                    <X className="w-3 h-3" />
                                  </button>
                                )}
                              </div>
                            );
                          })}

                          <button
                            type="button"
                            onClick={() => handleAddTime(itemIdx)}
                            className="flex items-center gap-1 text-xs font-semibold text-brand hover:underline px-2.5 py-1.5 rounded-xl border border-dashed border-stone-300 hover:bg-stone-50 transition cursor-pointer min-h-[36px]"
                          >
                            <Plus className="w-3.5 h-3.5" />
                            Add time
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Web Push Option */}
              {isPushSupported() && (
                <div className="p-4 rounded-2xl bg-paper border border-stone-200 flex items-start gap-3">
                  <Smartphone className="w-5 h-5 text-brand shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <label className="flex items-center gap-2 font-semibold text-ink text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={requestPush}
                        onChange={(e) => setRequestPush(e.target.checked)}
                        className="h-4 w-4 rounded border-stone-300 text-brand focus:ring-brand"
                      />
                      Enable phone / browser alerts
                    </label>
                    <p className="text-xs text-ink-muted mt-1 leading-relaxed">
                      Receive notifications on this device when it's time to take each dose.
                    </p>
                  </div>
                </div>
              )}

              {/* Calm Honest Limits Notice */}
              <div className="p-4 rounded-2xl bg-amber-50/50 border border-amber-200 text-xs text-amber-900 leading-relaxed flex items-start gap-2.5">
                <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <div>
                  <strong>Honest limits:</strong> Notifications are best-effort. Battery optimization,
                  Do Not Disturb, or phone sleep modes may silence alerts. Always follow your doctor's instructions.
                </div>
              </div>

              {/* Modal Footer */}
              <div className="pt-4 border-t border-stone-200 flex items-center justify-end gap-3 shrink-0">
                <Button type="button" variant="ghost" onClick={onClose} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting}
                >
                  Save & start reminders
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
