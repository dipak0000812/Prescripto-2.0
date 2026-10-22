import React from 'react';
import { AnalysisStageOut, StageName } from '../types/api';
import { CheckCircle2, CircleDashed, AlertCircle, MinusCircle, Loader2 } from 'lucide-react';

interface StageProgressBarProps {
  stages: AnalysisStageOut[];
  currentStatus: string;
}

const ORDERED_STAGES: { id: StageName; label: string; desc: string }[] = [
  { id: 'INGESTION', label: '1. Ingestion', desc: 'Integrity & Format Verification' },
  { id: 'QUALITY_CHECK', label: '2. Quality Check', desc: 'Laplacian Variance & Contrast' },
  { id: 'TEXT_DETECTION', label: '3. Text Detection', desc: 'Line Bounding Box Detection' },
  { id: 'OCR_RECOGNITION', label: '4. Recognition', desc: 'Handwriting OCR & Calibration' },
  { id: 'STRUCTURED_EXTRACTION', label: '5. Extraction', desc: '8 Clinical Fields Structured' },
  { id: 'MEDICATION_NORMALIZATION', label: '6. Normalization', desc: 'CDSCO Medication Master' },
  { id: 'SAFETY_SCREENING', label: '7. Safety Screening', desc: 'Duplicate Check & OpenFDA' },
  { id: 'REPORT_ASSEMBLY', label: '8. Report Assembly', desc: 'Review Triggers & Packaging' },
];

export const StageProgressBar: React.FC<StageProgressBarProps> = ({ stages, currentStatus }) => {
  const stageMap = new Map(stages.map((s) => [s.stage_name, s]));

  const completedCount = stages.filter((s) => s.status === 'COMPLETED').length;
  const progressPercent = Math.round((completedCount / ORDERED_STAGES.length) * 100);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Deterministic 8-Stage Clinical Verification</span>
            {currentStatus === 'PROCESSING' && (
              <span className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                <Loader2 className="w-3 h-3 animate-spin" /> In Progress
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Monotonic lease fencing with per-stage verification — no uncalibrated inference
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs font-medium text-slate-700">
            {completedCount} of {ORDERED_STAGES.length} stages completed
          </div>
          <div className="w-36 bg-slate-100 rounded-full h-2 mt-1.5 overflow-hidden border border-slate-200">
            <div
              className="bg-teal-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 pt-4">
        {ORDERED_STAGES.map((s) => {
          const stageResult = stageMap.get(s.id);
          const status = stageResult?.status || 'PENDING';
          const errorCode = stageResult?.error_code;

          let badgeColor = 'bg-slate-50 border-slate-200 text-slate-500';
          let icon = <CircleDashed className="w-4 h-4 text-slate-400" />;

          if (status === 'COMPLETED') {
            badgeColor = 'bg-emerald-50/70 border-emerald-200 text-emerald-900';
            icon = <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />;
          } else if (status === 'RUNNING') {
            badgeColor = 'bg-blue-50/70 border-blue-200 text-blue-900';
            icon = <Loader2 className="w-4 h-4 text-blue-600 animate-spin shrink-0" />;
          } else if (status === 'FAILED') {
            badgeColor = 'bg-rose-50/70 border-rose-200 text-rose-900';
            icon = <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />;
          } else if (status === 'SKIPPED') {
            badgeColor = 'bg-slate-50 border-slate-200 text-slate-400';
            icon = <MinusCircle className="w-4 h-4 text-slate-400 shrink-0" />;
          }

          return (
            <div
              key={s.id}
              className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 transition-all ${badgeColor}`}
            >
              <div className="mt-0.5">{icon}</div>
              <div className="min-w-0 flex-1">
                <div className="font-semibold text-slate-800 truncate">{s.label}</div>
                <div className="text-[11px] text-slate-500 mt-0.5 truncate">{s.desc}</div>
                {errorCode && (
                  <div className="mt-1 text-[10px] font-mono text-rose-700 bg-rose-50 px-1 py-0.5 rounded border border-rose-200 inline-block">
                    {errorCode}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StageProgressBar;
