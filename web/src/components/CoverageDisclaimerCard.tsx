import React from 'react';
import { ShieldAlert } from 'lucide-react';

interface CoverageDisclaimerCardProps {
  disclaimer?: string;
}

export const CoverageDisclaimerCard: React.FC<CoverageDisclaimerCardProps> = ({ disclaimer }) => {
  const defaultDisclaimer =
    'Prescripto AI 2.0 extracts structured medication data and screens against licensed safety sources. It does not diagnose, prescribe, or claim comprehensive interaction coverage. No finding is actionable until a qualified human reviewer signs off.';

  return (
    <div className="bg-amber-50/70 border-l-4 border-amber-500 border border-amber-200 rounded-r-xl p-4 text-xs text-amber-900 shadow-xs">
      <div className="flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold tracking-tight text-amber-900 uppercase text-[11px]">
            Clinical Safety & Decision Support Notice
          </div>
          <p className="leading-relaxed text-amber-800">
            {disclaimer || defaultDisclaimer}
          </p>
          <div className="text-[11px] text-amber-700/90 font-medium">
            Clinical Notice: Assistive AI output provides clinical decision support and does not replace professional medical judgment. Absence of flagged findings does not guarantee absence of risk.
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoverageDisclaimerCard;
