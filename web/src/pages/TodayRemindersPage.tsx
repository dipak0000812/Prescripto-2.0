import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  Bell,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  FastForward,
  Calendar,
  RefreshCw,
  PlusCircle,
  Check,
  ChevronRight,
  Download,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { AlertBanner } from '../components/ui/AlertBanner';
import {
  getTodayRemindersApi,
  actOnReminderEventApi,
  getAdherenceReportApi,
  getPlanIcsDownloadUrl,
} from '../api/reminders';
import {
  TodayRemindersResponse,
  ReminderEventOut,
  AdherenceReportResponse,
} from '../types/api';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { formatLocaleDate } from '../utils/dateUtils';
import { SunriseIcon, MiddaySunIcon, MoonIcon } from '../components/icons/HealthcareIcons';

function playReminderChime() {
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.setValueAtTime(880, ctx.currentTime + 0.15); // A5
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.85);
  } catch {}
}

function formatDueTime(isoString: string): string {
  try {
    const dt = new Date(isoString);
    return dt.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
  } catch {
    return isoString;
  }
}

export const TodayRemindersPage: React.FC = () => {
  const { session } = useAuth();
  const { language, t } = useLanguage();

  const [data, setData] = useState<TodayRemindersResponse | null>(null);
  const [adherence, setAdherence] = useState<AdherenceReportResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actingId, setActingId] = useState<string | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  const prevDueCount = useRef<number>(0);

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setIsLoading(true);
    setError(null);
    try {
      const todayRes = await getTodayRemindersApi();
      setData(todayRes);

      // Play audio chime if overdue count jumped
      if (todayRes.overdue.length > prevDueCount.current && prevDueCount.current !== 0) {
        playReminderChime();
      }
      prevDueCount.current = todayRes.overdue.length;

      // Also fetch adherence report in background
      try {
        const adhRes = await getAdherenceReportApi();
        setAdherence(adhRes);
      } catch {}
    } catch (err: any) {
      setError(
        err.response?.data?.detail?.message ||
          err.response?.data?.detail ||
          'Failed to load today’s medicine schedule.'
      );
    } finally {
      if (!isSilent) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => {
      loadData(true);
    }, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleAction = async (eventId: string, action: 'TAKEN' | 'SNOOZE' | 'SKIP') => {
    setActingId(eventId);
    setFeedbackMsg(null);
    try {
      await actOnReminderEventApi(eventId, action);
      if (action === 'TAKEN') {
        setFeedbackMsg('Dose marked as taken.');
        playReminderChime();
      } else if (action === 'SNOOZE') {
        setFeedbackMsg('Snoozed for 10 minutes.');
      } else {
        setFeedbackMsg('Dose recorded as skipped.');
      }
      await loadData(true);
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || 'Failed to update dose status.');
    } finally {
      setActingId(null);
    }
  };

  const todayFormatted = formatLocaleDate(new Date().toISOString(), language, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  const nextUpcomingDose = data?.upcoming && data.upcoming.length > 0 ? data.upcoming[0] : null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-stone-200">
        <div>
          <span className="text-xs font-semibold text-brand">
            Daily schedule
          </span>
          <h1 className="text-2xl sm:text-3xl font-bold text-ink mt-0.5">
            Today's doses
          </h1>
          <p className="text-sm text-ink-muted mt-0.5">{todayFormatted}</p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => loadData(false)}
            leftIcon={<RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />}
            className="text-xs"
          >
            Refresh
          </Button>

          <Link to="/upload">
            <Button
              type="button"
              variant="outline"
              size="sm"
              leftIcon={<PlusCircle className="w-4 h-4 text-brand" />}
              className="text-xs font-semibold"
            >
              Scan new prescription
            </Button>
          </Link>
        </div>
      </div>

      {/* Notifications / Feedback */}
      {feedbackMsg && (
        <div className="p-4 rounded-2xl bg-brand-soft border border-brand/20 text-brand-dark text-sm flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-brand shrink-0" />
            <span className="font-semibold">{feedbackMsg}</span>
          </div>
          <button
            type="button"
            onClick={() => setFeedbackMsg(null)}
            className="text-xs font-semibold text-brand hover:underline cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <AlertBanner type="error" title="Schedule notice">
          {error}
        </AlertBanner>
      )}

      {/* Metric Cards Banner */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white border border-stone-200 rounded-2xl p-4 shadow-2xs text-left">
            <span className="text-xs font-semibold text-ink-muted">Total doses</span>
            <p className="text-2xl font-bold text-ink mt-1">{data.total_due}</p>
          </div>

          <div className="bg-brand-soft/60 border border-brand/20 rounded-2xl p-4 shadow-2xs text-left">
            <span className="text-xs font-semibold text-brand">Taken</span>
            <p className="text-2xl font-bold text-brand mt-1">{data.taken_count}</p>
          </div>

          <div className="bg-amber-50/70 border border-amber-200 rounded-2xl p-4 shadow-2xs text-left">
            <span className="text-xs font-semibold text-amber-800">Pending</span>
            <p className="text-2xl font-bold text-amber-800 mt-1">{data.pending_count}</p>
          </div>

          <div className="bg-paper border border-stone-200 rounded-2xl p-4 shadow-2xs text-left">
            <span className="text-xs font-semibold text-ink-muted">On track</span>
            <p className="text-2xl font-bold text-ink mt-1">
              {adherence ? `${Math.round(adherence.overall_adherence_rate)}%` : '--'}
            </p>
          </div>
        </div>
      )}

      {/* Next Dose Hero Banner */}
      {nextUpcomingDose && (
        <div className="p-5 rounded-2xl bg-brand text-white shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider bg-white/20 px-2 py-0.5 rounded-full">
                Next dose
              </span>
              <span className="text-xs font-medium text-white/80">
                Scheduled at {formatDueTime(nextUpcomingDose.due_at)}
              </span>
            </div>
            <h2 className="text-xl font-bold">{nextUpcomingDose.medicine_name}</h2>
            {nextUpcomingDose.dosage_text && (
              <p className="text-xs text-white/80">{nextUpcomingDose.dosage_text}</p>
            )}
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <Button
              type="button"
              variant="secondary"
              onClick={() => handleAction(nextUpcomingDose.id, 'TAKEN')}
              disabled={actingId === nextUpcomingDose.id}
              leftIcon={<Check className="w-4 h-4 text-brand" />}
              className="bg-white text-brand hover:bg-stone-100 font-bold min-h-[48px]"
            >
              Take now
            </Button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {isLoading && !data ? (
        <div className="p-12 text-center bg-white border border-stone-200 rounded-2xl">
          <RefreshCw className="w-8 h-8 text-brand animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-ink-muted">Loading today’s doses…</p>
        </div>
      ) : !data || data.total_due === 0 ? (
        /* Empty State */
        <div className="p-12 text-center bg-white border border-stone-200 rounded-2xl space-y-4">
          <div className="w-16 h-16 rounded-full bg-paper border border-stone-200 flex items-center justify-center mx-auto text-ink-muted">
            <Calendar className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto">
            <h2 className="text-lg font-bold text-ink">No reminders scheduled for today</h2>
            <p className="text-sm text-ink-muted mt-1 leading-relaxed">
              When you scan a prescription and confirm it, your daily doses will appear right here.
            </p>
          </div>
          <div className="pt-2">
            <Link to="/upload">
              <Button
                variant="primary"
                leftIcon={<PlusCircle className="w-4 h-4" />}
                className="px-6 min-h-[48px]"
              >
                Scan a prescription
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          {/* 1. OVERDUE DOSES */}
          {data.overdue.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                <h2 className="text-lg font-bold text-ink">
                  Overdue ({data.overdue.length})
                </h2>
              </div>

              <div className="space-y-3">
                {data.overdue.map((ev) => (
                  <DoseCard
                    key={ev.id}
                    event={ev}
                    isOverdue={true}
                    isActing={actingId === ev.id}
                    onAction={handleAction}
                  />
                ))}
              </div>
            </section>
          )}

          {/* 2. UPCOMING DOSES */}
          <section className="space-y-3">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-brand" />
              <h2 className="text-lg font-bold text-ink">
                Upcoming today ({data.upcoming.length})
              </h2>
            </div>

            {data.upcoming.length === 0 ? (
              <div className="p-6 text-center bg-paper border border-stone-200 rounded-2xl text-ink-muted text-sm">
                No more upcoming doses scheduled for today.
              </div>
            ) : (
              <div className="space-y-3">
                {data.upcoming.map((ev) => (
                  <DoseCard
                    key={ev.id}
                    event={ev}
                    isOverdue={false}
                    isActing={actingId === ev.id}
                    onAction={handleAction}
                  />
                ))}
              </div>
            )}
          </section>

          {/* 3. COMPLETED DOSES */}
          {data.completed.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-brand" />
                <h2 className="text-lg font-bold text-ink">
                  Completed today ({data.completed.length})
                </h2>
              </div>

              <div className="space-y-2">
                {data.completed.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-4 rounded-2xl bg-white border border-stone-200 flex items-center justify-between text-left opacity-75"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                          ev.status === 'TAKEN'
                            ? 'bg-brand-soft text-brand'
                            : 'bg-stone-100 text-stone-500'
                        }`}
                      >
                        {ev.status === 'TAKEN' ? (
                          <Check className="w-4 h-4" />
                        ) : (
                          <FastForward className="w-4 h-4" />
                        )}
                      </div>
                      <div>
                        <span className="font-semibold text-ink text-sm">
                          {ev.medicine_name}
                        </span>
                        {ev.dosage_text && (
                          <span className="text-xs text-ink-muted ml-2">({ev.dosage_text})</span>
                        )}
                        <p className="text-xs text-ink-muted">
                          Scheduled {formatDueTime(ev.due_at)}
                          {ev.acted_at && ` · Logged ${formatDueTime(ev.acted_at)}`}
                        </p>
                      </div>
                    </div>

                    <span
                      className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                        ev.status === 'TAKEN'
                          ? 'bg-brand-soft text-brand border border-brand/20'
                          : 'bg-stone-100 text-stone-600 border border-stone-200'
                      }`}
                    >
                      {ev.status === 'TAKEN' ? 'Taken' : 'Skipped'}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
};

interface DoseCardProps {
  event: ReminderEventOut;
  isOverdue: boolean;
  isActing: boolean;
  onAction: (eventId: string, action: 'TAKEN' | 'SNOOZE' | 'SKIP') => void;
}

const DoseCard: React.FC<DoseCardProps> = ({ event, isOverdue, isActing, onAction }) => {
  return (
    <div
      className={`p-4 sm:p-5 rounded-2xl border transition text-left flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
        isOverdue
          ? 'bg-red-50/30 border-red-200 shadow-2xs border-l-4 border-l-red-500'
          : 'bg-white border-stone-200 shadow-2xs hover:border-stone-300'
      }`}
    >
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
              isOverdue
                ? 'bg-red-100 text-red-800 border border-red-200'
                : 'bg-stone-100 text-ink'
            }`}
          >
            {formatDueTime(event.due_at)}
          </span>
          {isOverdue && (
            <span className="text-xs font-semibold text-red-700 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              Overdue
            </span>
          )}
        </div>

        <h3 className="text-lg font-bold text-ink mt-1">{event.medicine_name}</h3>
        {event.dosage_text && (
          <p className="text-xs text-ink-muted font-medium">{event.dosage_text}</p>
        )}
      </div>

      {/* Action Buttons: Taken, Snooze, Skip */}
      <div className="flex items-center gap-2 pt-2 sm:pt-0 border-t sm:border-t-0 border-stone-100">
        <Button
          type="button"
          size="md"
          variant="primary"
          disabled={isActing}
          onClick={() => onAction(event.id, 'TAKEN')}
          leftIcon={<Check className="w-4 h-4" />}
          className="flex-1 sm:flex-none min-h-[48px]"
        >
          Taken
        </Button>

        <Button
          type="button"
          size="md"
          variant="outline"
          disabled={isActing}
          onClick={() => onAction(event.id, 'SNOOZE')}
          leftIcon={<RotateCcw className="w-4 h-4" />}
          className="flex-1 sm:flex-none min-h-[48px]"
        >
          Snooze 10m
        </Button>

        <Button
          type="button"
          size="md"
          variant="ghost"
          disabled={isActing}
          onClick={() => onAction(event.id, 'SKIP')}
          className="text-ink-muted hover:text-ink text-xs min-h-[48px]"
        >
          Skip
        </Button>
      </div>
    </div>
  );
};

export default TodayRemindersPage;
